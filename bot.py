import xml.etree.ElementTree as ET
from decimal import Decimal
import logging

import requests

import conf


BASE_URL = f'https://api.telegram.org/bot{conf.TOKEN}'
STOCK_URL = 'http://www.cbr.ru/scripts/XML_daily_eng.asp'


def get_updates(last_update_id: int) -> requests.Response:
    limit = 1
    offset = last_update_id + 1
    timeout = 300
    params = {'timeout': timeout, 'limit': limit, 'offset': offset}
    url = f'{BASE_URL}/getUpdates'
    print(url)
    response = requests.get(url=url, params=params, proxies=conf.PROXIES)
    return response


def parse_answer(answer: dict) -> tuple:
    message = answer['result'][0]['message']
    chat_id = message['chat']['id']
    text = message['text']
    update_id = answer['result'][0]['update_id']
    return (chat_id, text, update_id)


def _help():
    message = 'To receive currency exchange rate send message with currency code:\n'
    stock = _get_stock()
    message_body = ''
    for char_code, content in stock.items():
        line = f'{char_code} — {content["name"]}\n'
        message_body += line
    return message + message_body


def _dispatch_command(text: str) -> callable:
    commands = {
        '/help': _help
    }
    handler = commands.get(text)
    return handler


def _handle_text(text: str) -> str:
    if text.startswith('/'):
        handler = _dispatch_command(text)
        return handler()
    return text


def _get_stock() -> dict:
    response = requests.get(STOCK_URL)
    root = ET.fromstring(response.text)
    stock = {}
    for child in root:
        char_code = child.find('CharCode').text
        nominal_text = child.find('Nominal').text
        name = child.find('Name').text
        value_text = child.find('Value').text.replace(',', '.')
        rate = (
            (Decimal(value_text) / Decimal(nominal_text))
            .quantize(Decimal('1.00'))
        )
        stock[char_code] = {'name': name, 'rate': rate}
    return stock


def construct_response(text: str) -> str:
    handled_text = _handle_text(text)
    if text.startswith('/'):
        return handled_text
    stock = _get_stock()
    currency = stock.get(handled_text.upper())
    if not currency:
        return _help()
    reply = f'1 {currency["name"]} costs {currency["rate"]} rubles'
    return reply


def send_response(chat_id: int, text: str) -> requests.Response:
    url = f'{BASE_URL}/sendMessage'
    params = {'chat_id': chat_id, 'text': text}
    response = requests.get(url, params=params, proxies=conf.PROXIES)
    return response


if __name__ == '__main__':
    last_update_id = 0
    while True:
        response = get_updates(last_update_id)
        answer = response.json()
        if answer.get('ok') is True and answer['result']:
            chat_id, text, update_id = parse_answer(answer)
            last_update_id = update_id
            reply = construct_response(text)
            send_result = send_response(chat_id=chat_id, text=reply)
