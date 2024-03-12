from functools import wraps
from typing import Any, Callable


def error_handler(func: Callable[[Any], Any]) -> Callable[[Any], Any]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            pass

    return wrapper
