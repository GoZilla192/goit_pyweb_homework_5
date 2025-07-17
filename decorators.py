from functools import wraps
from aiohttp import ClientError

from exceptions import UnexpectedHTTPStatusCode


def error_handler(func: callable):
    @wraps(func)
    async def inner(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except ClientError as err:
            print(f"Happen error: {err}")
        except UnexpectedHTTPStatusCode:
            print(f"Unexpected status code ")
        except TypeError as e:
            print(e)

    return inner
