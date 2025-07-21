import asyncio
from datetime import datetime
import logging
import websockets
import names
from websockets import WebSocketServerProtocol
from websockets.exceptions import ConnectionClosedOK
import aiofile
import aiopath

from parse_utils import AsyncRequestConnection, JSONProcessData, get_calculate_dates, WebChatOutput

logging.basicConfig(level=logging.INFO)


async def get_currency(days: int = 1):
    BASE_URL = "https://api.privatbank.ua/p24api/exchange_rates?date="

    dates = get_calculate_dates(days)
    semaphore = asyncio.Semaphore(5)
    requests_tasks = [
        AsyncRequestConnection.get_json(BASE_URL + next_date, semaphore) for next_date in dates
    ]

    json_lists = await asyncio.gather(*requests_tasks)
    processed_json_lists = await JSONProcessData.process(json_lists, ["*"])

    return processed_json_lists


class Server:
    clients = set()

    async def register(self, ws: WebSocketServerProtocol):
        ws.name = names.get_full_name()
        self.clients.add(ws)
        logging.info(f"{ws.remote_address} connects")

    async def unregister(self, ws: WebSocketServerProtocol):
        self.clients.remove(ws)
        logging.info(f"{ws.remote_address} disconnects")

    async def send_to_client(self, message: str):
        if self.clients:
            [await client.send(message) for client in self.clients]

    async def ws_handler(self, ws: WebSocketServerProtocol):
        await self.register(ws)
        try:
            await self.distrubute(ws)
        except ConnectionClosedOK:
            pass
        finally:
            await self.unregister(ws)

    async def distrubute(self, ws: WebSocketServerProtocol):
        async for message in ws:
            await self.send_to_client(f"{ws.name}: {message}")
            processed_message = message.strip().lower().split()
            if len(processed_message) > 0 and processed_message[0] == "exchange":
                async with aiofile.async_open(aiopath.AsyncPath(__file__).parent / "log.txt", 'a') as afp:
                    await afp.write(f"{datetime.now()}: user \"{ws.name}\" execute command \"{message}\"\n")

                if len(processed_message) == 2:
                    all_currency = await get_currency(int(processed_message[1]))
                elif len(processed_message) == 1:
                    all_currency = await get_currency()

                if self.clients:
                    [
                        await client.send(WebChatOutput.display(all_currency))
                        for client in self.clients
                    ]


async def main():
    server = Server()
    async with websockets.serve(server.ws_handler, "localhost", 8080):
        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())
