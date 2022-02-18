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
    try:
        wb_price = soup.find('span', class_='price-block__final-price')
        status = request.status_code
        if status == 429:
            sleep(10)
            request = requests.get(url)
            soup = BeautifulSoup(request.text, 'lxml')
            wb_price = soup.find('span', class_='price-block__final-price').text.split('₽')[0].strip().replace(u'\xa0', u'')
        else:
            wb_price = wb_price.text.split('₽')[0].strip().replace(u'\xa0', u'')
    except AttributeError:
        wb_price = soup.find('span', class_='sold-out-product__text').text.replace(u'\xa0', u'')

    return wb_price, url




def get_worksheet_order_info(sheet):
    wrong_prices = []
    data_orders = get_worksheet_ids(sheet)
    # print(data_orders)
    # data_orders = [{'article': '40579043', 'client_price': '481'}, {'article': '41158021', 'client_price': '340'}, {'article': '41228775', 'client_price': '299'}, {'article': '41240866', 'client_price': '494'}, {'article': '43257800', 'client_price': '1292'}, {'article': '43268541', 'client_price': '1292'}, {'article': '45806492', 'client_price': '1998'}, {'article': '43498940', 'client_price': '491'}, {'article': '43501647', 'client_price': '307'}, {'article': '43742573', 'client_price': '554'}, {'article': '43742793', 'client_price': '316'}, {'article': '43745146', 'client_price': '421'}, {'article': '43745147', 'client_price': '421'}, {'article': '43745690', 'client_price': '421'}, {'article': '43745691', 'client_price': '421'}, {'article': '43860422', 'client_price': '324'}, {'article': '48564403', 'client_price': '324'}, {'article': '48566203', 'client_price': '217'}, {'article': '49234031', 'client_price': '424'}, {'article': '49234032', 'client_price': '424'}, {'article': '51460785', 'client_price': '778'}, {'article': '41797971', 'client_price': '373'}, {'article': '48105035', 'client_price': '300'}, {'article': '52451400', 'client_price': '1371'}, {'article': '54624031', 'client_price': '1371'}, {'article': '54624443', 'client_price': '1371'}, {'article': '54624699', 'client_price': '1371'}, {'article': '46451469', 'client_price': '867'}, {'article': '64048538', 'client_price': '2238'}, {'article': '46584126', 'client_price': '2599'}, {'article': '64307641', 'client_price': '2599'}, {'article': '48059401', 'client_price': '883'}, {'article': '43968564', 'client_price': '580'}, {'article': '43973145', 'client_price': '447'}, {'article': '43973146', 'client_price': '447'}, {'article': '61162427', 'client_price': '1086'}, {'article': '61165876', 'client_price': '728'}, {'article': '61200309', 'client_price': '994'}]
    for order in data_orders:
        wb_price, url = parse_wildberries_by_order(order['article'])
        if wb_price == 'Товара нет вналичии':
            logging.warning(f'Товара нет в наличии - {order["article"]}')
            # print('нет в наличии ', order)
            wrong_prices.append({
                    'article': order['article'],
                    'price': order['client_price'],
                    'wb_price': wb_price,
                    'url': url
                })

        elif int(wb_price) == int(order['client_price']):
            logging.info(f"Всё гуд для - {order['client_price']}")

        else:
            logging.warning(f"Неверная цена у - {order['client_price']}")
            wrong_prices.append({
                    'article': order['article'],
                    'price': order['client_price'],
                    'wb_price': wb_price,
                    'url': url
                })
        
    return wrong_prices 


if __name__ == '__main__':
    spread = auth_spread()
    work = spread.worksheets()
    print(get_worksheet_order_info(work[0]))
    