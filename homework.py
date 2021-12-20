import os
import time
import requests
import telegram
import logging
from exceptions import APIKeyError, BadResponseError
from dotenv import load_dotenv
from typing import Dict
from sys import stdout


load_dotenv()
logging.basicConfig(
    format='%(asctime)s, %(levelname)s, %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
handler = logging.StreamHandler(stdout)
logger.addHandler(handler)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_TIME = 600
PRACTICUM_ENDPOINT = (
    'https://practicum.yandex.ru/api/'
    'user_api/homework_statuses/'
)
PRACTICUM_ENDPOINT_HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def send_message(bot, message) -> None:
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(
            chat_id=TELEGRAM_CHAT_ID,
            text=message,
        )
        logging.info(f'Бот отправил сообщение: "{message}"')
    except telegram.error.TelegramError as err:
        logging.error(f'Telegramm Error: {err}')


def get_api_answer(current_timestamp):
    """Делает запрос к эндпоинту API-сервиса Практикум.Домашка."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    try:
        response = requests.get(
            PRACTICUM_ENDPOINT,
            headers=PRACTICUM_ENDPOINT_HEADERS,
            params=params
        )
        if response.status_code == 200:
            return response.json()
        raise ConnectionError
    except Exception as error:
        logging.error(f'Ошибка запроса к API: {error}')
        raise BadResponseError(response.status_code, PRACTICUM_ENDPOINT)


def check_response(response):
    """Проверяет ответ API на корректность."""
    if not isinstance(response, dict):
        raise TypeError('тип response отличен от dict')
    homeworks = response.get('homeworks')
    if not isinstance(homeworks, list):
        raise TypeError('тип homeworks отличен от list')
    if homeworks == []:
        return homeworks
    if not homeworks:
        raise APIKeyError('homeworks')
    if not response.get('current_date'):
        raise APIKeyError('current_date')
    return homeworks


def parse_status(homework: Dict) -> str:
    """Извлекает статус домашней работы.
    В случае успеха возвращает строку для отправки в Telegram.
    """
    homework_status = homework['status']
    if homework_status not in HOMEWORK_STATUSES:
        error_message = 'недокументированный статус домашней работы'
        logging.error(error_message)
        raise KeyError(error_message)
    verdict = HOMEWORK_STATUSES[homework_status]
    homework_name = homework['homework_name']
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens() -> bool:
    """Проверяет доступность необходимых переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def main() -> None:
    """Основная логика работы бота."""
    if not check_tokens():
        message = (
            'Отсутствует обязательная переменная окружения!'
            'Программа принудительно остановлена.'
        )
        logging.critical(message)
        return
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    cache_message = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            logging.info('Успешный запрос к эндпоинту Практикум.Домашка')
            homeworks = check_response(response)
            logging.debug('Ответ API корректен')
            if homeworks:
                string_to_telegram: str = parse_status(homeworks[0])
                send_message(bot, string_to_telegram)
                logging.info('Обновился статус проверки домашней работы.')
            else:
                logging.debug('Статус домашней работы НЕ изменился.')
            current_timestamp = response.get('current_date')
            logging.debug('Итерация основного цикла прошла без ошибок.')
            time.sleep(RETRY_TIME)
        except Exception as error:
            message = f'Ошибка: {error}'
            logging.error(message)
            if message != cache_message:
                send_message(bot, message)
                cache_message = message
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
