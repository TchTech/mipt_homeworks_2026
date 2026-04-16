import datetime
import functools
import json
from collections.abc import Callable
from typing import Any
from urllib.request import urlopen

INVALID_CRITICAL_COUNT = "Breaker count must be positive integer!"
INVALID_RECOVERY_TIME = "Breaker recovery time must be positive integer!"
VALIDATIONS_FAILED = "Invalid decorator args."
TOO_MUCH = "Too much requests, just wait."


class BreakerError(Exception):
    def __init__(self, func_name: str, block_time: datetime.datetime) -> None:
        super().__init__(TOO_MUCH)
        self.func_name = func_name
        self.block_time = block_time


class CircuitBreaker:
    def __init__(
        self,
        critical_count: int = 5,
        time_to_recover: int = 30,
        triggers_on: type[Exception] = Exception,
    ) -> None:
        errors: list[ValueError] = []
        if critical_count < 1:
            errors.append(ValueError(INVALID_CRITICAL_COUNT))
        if time_to_recover < 1:
            errors.append(ValueError(INVALID_RECOVERY_TIME))
        if errors:
            raise ExceptionGroup(VALIDATIONS_FAILED, errors)

        self.critical_count = critical_count
        self.time_to_recover = time_to_recover
        self.triggers_on = triggers_on

    def __call__(self, func: Callable[..., object]) -> Callable[..., object]:
        func_name = f"{func.__module__}.{func.__name__}"
        self._count = 0
        self._block_time: datetime.datetime | None = None

        @functools.wraps(func)
        def wrapper(*args: object, **kwargs: object) -> object:
            if self._block_time is not None:
                now = datetime.datetime.now(datetime.UTC)
                if (now - self._block_time).total_seconds() < self.time_to_recover:
                    raise BreakerError(func_name, self._block_time)
                self._count = 0
                self._block_time = None

            try:
                result = func(*args, **kwargs)
            except self.triggers_on as exc:
                self._count += 1
                if self._count >= self.critical_count:
                    block_time = datetime.datetime.now(datetime.UTC)
                    raise BreakerError(func_name, block_time) from exc
                raise
            else:
                self._count = 0
                return result

        return wrapper


circuit_breaker = CircuitBreaker(5, 30, Exception)


# @circuit_breaker
def get_comments(post_id: int) -> Any:
    """
    Получает комментарии к посту

    Args:
        post_id (int): Идентификатор поста

    Returns:
        list[dict[int | str]]: Список комментариев
    """
    response = urlopen(f"https://jsonplaceholder.typicode.com/comments?postId={post_id}")
    return json.loads(response.read())


if __name__ == "__main__":
    comments = get_comments(1)
