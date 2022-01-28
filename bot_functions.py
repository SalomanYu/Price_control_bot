from time import sleep
import gspread
from oauth2client.service_account import ServiceAccountCredentials

import requests
from bs4 import BeautifulSoup


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
            print('Превышен лимит запросов.')
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
                print('Записан ', id)
        except gspread.exceptions.APIError:
            print('Превышен лимит по API')
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
    
    return wb_price



def start():
    spread = auth_spread()
    worksheets = spread.worksheets()[:3] # [:5]
    wrong_prices = []
    for sheet in worksheets:
        data_orders = get_worksheet_ids(sheet)
        # data_orders = [{'article': '40579043', 'client_price': '441'}, {'article': '41158021', 'client_price': '364'}, {'article': '41228775', 'client_price': '270'}, {'article': '41240866', 'client_price': '340'}, {'article': '43257800', 'client_price': '991'}, {'article': '43268541', 'client_price': '991'}, {'article': '45806492', 'client_price': '1937'}, {'article': '43498940', 'client_price': '491'}, {'article': '43501647', 'client_price': '324'}, {'article': '43742573', 'client_price': '601'}, {'article': '43742793', 'client_price': '325'}, {'article': '43743931', 'client_price': '601'}, {'article': '43745146', 'client_price': '445'}, {'article': '43745147', 'client_price': '445'}, {'article': '43745690', 'client_price': '445'}, {'article': '43745691', 'client_price': '445'}, {'article': '43860422', 'client_price': '344'}, {'article': '48564403', 'client_price': '344'}, {'article': '48566203', 'client_price': '234'}, {'article': '49234031', 'client_price': '434'}, {'article': '49234032', 'client_price': '434'}, {'article': '51460785', 'client_price': '827'}, {'article': '41797971', 'client_price': '459'}, {'article': '48105035', 'client_price': '317'}, {'article': '52451400', 'client_price': '1420'}, {'article': '54624031', 'client_price': '1445'}, {'article': '54624443', 'client_price': '1445'}, {'article': '54624699', 'client_price': '1445'}, {'article': '46451469', 'client_price': '788'}, {'article': '46584126', 'client_price': '2599'}, {'article': '48059401', 'client_price': '835'}, {'article': '43968564', 'client_price': '682'}, {'article': '43973145', 'client_price': '630'}, {'article': '43973146', 'client_price': '619'}]
        for order in data_orders:
            article = order['article']
            try:
                wb_price = parse_wildberries_by_order(article)
                wb_price = wb_price.replace(u'\xa0', u'')
                if wb_price == order['client_price']:
                    print(f'Цена для {article} совпадает: {wb_price} - {order["client_price"]}')
                else:
                    wrong_prices.append({
                        'article': article,
                        'price': order['client_price'],
                        'wb_price': wb_price
                    })
                
                    print(f'НЕ СОВПАДАЕТ цена для {article}: {wb_price} - {order["client_price"]}')
            except AttributeError:
                print('Товара нет в наличии: ', article)
                wrong_prices.append({
                        'article': article,
                        'price': order['client_price'],
                        'wb_price': 'Товара нет в наличии'
                    })
        # break
    print('Товары закончились')
    return wrong_prices

# get_worksheet_ids('21')
# main()
