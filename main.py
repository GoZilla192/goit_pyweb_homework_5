import argparse
import asyncio

from parse_utils import (
    get_calculate_dates,
    AsyncRequestConnection,
    JSONProcessData,
    ConsoleOutput,
)


async def main(program_args):
    BASE_URL = "https://api.privatbank.ua/p24api/exchange_rates?date="

    days = program_args.days

    dates = get_calculate_dates(days)

    semaphore = asyncio.Semaphore(5)
    requests_tasks = [
        AsyncRequestConnection.get_json(BASE_URL + next_date, semaphore) for next_date in dates
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

    
    asyncio.run(main(args))
