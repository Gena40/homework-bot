class APIKeyError(Exception):
    """Вызывается, когда в ответе сервера не найден обязательный ключ."""

    def __init__(self, key) -> None:
        """Добавляем имя отсутствующего ключа для записи в лог."""
        self.key = key
        super().__init__()

    def __str__(self) -> str:
        """Переопределяем вывод для записи в лог."""
        return f'в ответе API отсутствует ключ {self.key}.'


class BadResponseError(Exception):
    """Вызывается, когда статус ответа сервера не равен 200."""

    def __init__(self, status_code, endpoint) -> None:
        """Сохраняем статус ответа сервера и ендпоинт для записи в лог."""
        self.status_code = status_code
        self.endpoint = endpoint
        super().__init__()

    def __str__(self) -> str:
        """Переопределяем вывод для записи в лог."""
        message = (
            f'эндпоинт {self.endpoint} недоступен, '
            f'статус {self.status_code}'
        )
        return message
