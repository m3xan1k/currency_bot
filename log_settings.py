import logging

import requests

import conf


class TelegramHandler(logging.Handler):
    def __init__(self):
        logging.Handler.__init__(self)

    def emit(self, record: logging.LogRecord):
        msg = self.format(record)
        url = f'https://api.telegram.org/bot{conf.LOG_BOT_TOKEN}/sendMessage'
        params = {'chat_id': conf.ADMIN_CHAT_ID, 'text': msg}
        requests.get(url=url, params=params, proxies=conf.PROXIES)


LOGGER_SETUP = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standart': {
            'format': '{asctime} — {levelname} — {name} —{message}',
            'style': '{'
        }
    },
    'handlers': {
        'telegram': {
            '()': TelegramHandler,
            'level': 'ERROR',
            'formatter': 'standart',
        }
    },
    'loggers': {
        'bot_logger': {
            'handlers': ['telegram'],
            'level': 'ERROR',
            'propagate': False,
        }
    }
}
