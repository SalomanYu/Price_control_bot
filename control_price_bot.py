from aiogram import Bot, Dispatcher, executor, types
import logging

import os


import bot_functions 

logging.basicConfig(level=logging.INFO)

TOKEN  = os.getenv('PRICE_CONTROL_BOT_TOKEN')
bot = Bot(TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start'])
async def send_hello(message: types.Message):
    await message.answer('Спасибо, что включил меня')


@dp.message_handler(commands=['check_client_price'])
async def check_price(message: types.Message):
    await message.answer('🕓 Я начал сравнивать цены. Подождите...')
    
    spread = bot_functions.auth_spread()
    worksheets = spread.worksheets()[:3]
    for sheet in worksheets:
        wrong_data = bot_functions.get_worksheet_order_info(sheet)
        await message.answer(f'👇 Информация по "{sheet.title}"')
        if wrong_data == []:
            await message.answer('😌 Совпадают все цены')
            continue

        for item in wrong_data:
            notification = f'❗️Не совпадает цена\nАртикул: {item["article"]}\nЦена в таблице: {item["price"]}\nЦена WB: {item["wb_price"]}\nСсылка на товар: {item["url"]}'
            await message.answer(notification)

    await message.answer('✅ Проверка закончилась')
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)   