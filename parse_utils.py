from abc import ABC, abstractmethod
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
    def display(data) -> str | None:
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


class WebChatOutput(Output):
    @staticmethod
    def display(data):
        result = ""

        for json_dict in data:
            for curr_date in json_dict:
                result = result + "<br>" + curr_date if result else curr_date

                for currency in json_dict[curr_date]:
                    result += "<br>&emsp;" + currency + "&emsp;"
                    sale_rate = json_dict[curr_date][currency].get(
                        "saleRate", json_dict[curr_date][currency]["sale"]
                    )
                    purchase_rate = json_dict[curr_date][currency].get(
                        "purchaseRate", json_dict[curr_date][currency]["purchase"]
                    )
                    result += f"Купля {sale_rate:.4f}"
                    result += f"&emsp;Продаж {purchase_rate:.4f}"

        return result


class AsyncRequestConnection(Connection):
    @staticmethod
    @error_handler
    async def get_json(url, constrains_requests=asyncio.Semaphore(10)):
        async with constrains_requests:
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
                if (
                    desired_currencies != ["*"]
                    and exchange_currency["currency"] not in desired_currencies
                ):
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
