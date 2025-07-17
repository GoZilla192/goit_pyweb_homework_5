from abc import ABC, abstractmethod
import argparse
import datetime
import aiohttp
import asyncio
from typing import List, Dict


from exceptions import UnexpectedHTTPStatusCode
from decorators import error_handler


class Connection(ABC):
    @staticmethod
    @abstractmethod
    def get_json(url):
        pass


class Output(ABC):
    @staticmethod
    @abstractmethod
    def display(data):
        pass


class ProcessData(ABC):
    @staticmethod
    @abstractmethod
    def process(
        json_lists: List[Dict[str, int | float]],
    ) -> List[Dict[str, int | float]]:
        pass


class ConsoleOutput(Output):
    @staticmethod
    def display(data):
        from pprint import pprint

        pprint(data)


class AsyncRequestConnection(Connection):
    @staticmethod
    @error_handler
    async def get_json(url):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise UnexpectedHTTPStatusCode


class JSONProcessData:
    @staticmethod
    async def process(
        json_lists: List[Dict[str, int | float | str]],
        desired_currencies: List[str],
    ) -> List[Dict[str, int | float | str]]:
        """
        На вхід ми приймаємо список джсонів в інформація про багато валют,
        на виході ми повертаємо список джсонів з потрібними нам валютами
        """

        result = []

        for json_data in json_lists:
            json_data_which_we_append = {json_data["date"]: {}}

            for exchange_currency in json_data["exchangeRate"]:
                if exchange_currency["currency"] not in desired_currencies:
                    continue

                try:
                    json_data_which_we_append[json_data["date"]][
                        exchange_currency["currency"]
                    ] = {
                        "sale": exchange_currency["saleRate"],
                        "purchase": exchange_currency["purchaseRate"],
                    }
                except KeyError:
                    json_data_which_we_append[json_data["date"]][
                        exchange_currency["currency"]
                    ] = {
                        "sale": exchange_currency["saleRateNB"],
                        "purchase": exchange_currency["purchaseRateNB"],
                    }

            result.append(json_data_which_we_append)

        return result


def get_calculate_dates(day):
    curr_date = datetime.datetime.now()
    dates = [
        (curr_date - datetime.timedelta(days=i)).strftime("%d.%m.%Y")
        for i in range(day)
    ]

    return dates


async def main(program_args):
    days = program_args.days

    dates = get_calculate_dates(days)

    requests_tasks = [
        AsyncRequestConnection.get_json(BASE_URL + next_date) for next_date in dates
    ]

    json_lists = await asyncio.gather(*requests_tasks)
    processed_json_lists = await JSONProcessData.process(
        json_lists, program_args.currency.upper().split(",")
    )

    ConsoleOutput.display(processed_json_lists)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Currency viewer",
        usage="python3 main.py days [options]",
    )

    parser.add_argument(
        "days",
        help="Кількість пройдених днів за які ви хочете дізнатися інформацію.",
        default=1,
        type=int,
        nargs="?",
    )
    parser.add_argument(
        "-c",
        "--currency",
        help="Валюти які ви хочете побачити. Якщо більше 1 валюти то пишеться через ',' без пробілів. Наприклад: --currency=USD,EUR",
        default="USD,EUR",
    )

    args = parser.parse_args()
    if int(args.days) > 10:
        print("Ви не можете отримати інформацію більше ніж за 10 днів.")
        exit()

    BASE_URL = "https://api.privatbank.ua/p24api/exchange_rates?date="
    asyncio.run(main(args))
