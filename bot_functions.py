from time import sleep
import gspread
from oauth2client.service_account import ServiceAccountCredentials

import logging
import requests
from bs4 import BeautifulSoup


logging.basicConfig(filename='output.log', level=logging.DEBUG, format='')


def auth_spread():
    scope = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    credentials = ServiceAccountCredentials.from_json_keyfile_name(r'Service Accounts/morbot-338716-b219142d9c70.json')

    gc = gspread.authorize(credentials)
    spread = gc.open_by_key('1bGbNieNgqDNSORaphLhLOHUbIUE00yxA0q_b4HsNclM') # Расчеты

    return spread


def get_worksheet_ids(worksheet):
    def get_ids(worksheet):
        try:
            client_price_col = worksheet.find('Итог (клиент)').col
            id_order_col = worksheet.find('артикул WB').col
            id_orders = worksheet.col_values(id_order_col)

            return id_orders, client_price_col

        except gspread.exceptions.APIError:
            logging.warning('Превышен лимит запросов.')
            sleep(30)
            get_ids(worksheet)
    
    def get_client_price(id, price_col):
        try:
            if len(id) == 8:
                order_row = worksheet.find(str(id)).row
                order_client_price = worksheet.cell(order_row, price_col).value.split(',')[0]
                # order_with_client_price[id] = order_client_price.replace(u'\xa0', '')
                order_with_client_price.append({
                    "article": id,
                    'client_price': order_client_price.replace(u'\xa0', '')
                })
                logging.info(f'Записан: {id}')
        except gspread.exceptions.APIError:
            logging.warning('Превышен лимит по API')
            sleep(20)
            get_client_price(id, price_col)

    order_with_client_price = []
    ids, client_price_col = get_ids(worksheet)

    for id in ids:
        get_client_price(id, client_price_col)
    
    return order_with_client_price


def parse_wildberries_by_order(article):
    url = f'https://www.wildberries.ru/catalog/{article}/detail.aspx?targetUrl=SP'
    request = requests.get(url)
    soup = BeautifulSoup(request.text, 'lxml')
    wb_price = soup.find('span', class_='price-block__final-price').text.split('₽')[0].strip()
    
    return wb_price, url


def get_worksheet_order_info(sheet):
    wrong_prices = []
    data_orders = get_worksheet_ids(sheet)
    for order in data_orders:
        article = order['article']
        try:
            wb_price, url = parse_wildberries_by_order(article)
            wb_price = wb_price.replace(u'\xa0', u'')
            if wb_price == order['client_price']:
                logging.info(f'Цена для {article} совпадает: {wb_price} - {order["client_price"]}')
            else:
                print(wb_price, order['client_price'])
                wrong_prices.append({
                    'article': article,
                    'price': order['client_price'],
                    'wb_price': wb_price,
                    'url': url
                })

                logging.warning(f'НЕ СОВПАДАЕТ цена для {article}: {wb_price} - {order["client_price"]}')
        except AttributeError:
            logging.warning(f'Товара нет в наличии: {article}')
            # print(article, url)

            wrong_prices.append({
                    'article': article,
                    'price': order['client_price'],
                    'wb_price': 'Товара нет в наличии',
                    'url': f'https://www.wildberries.ru/catalog/{article}/detail.aspx?targetUrl=SP'
                    })
    return wrong_prices 


if __name__ == '__main__':
    spread = auth_spread()
    work = spread.worksheets()[:3]
    get_worksheet_order_info(work[1])
    