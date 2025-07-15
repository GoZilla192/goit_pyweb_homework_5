from abc import ABC, abstractmethod
import datetime
import aiohttp 


class Connection(ABC):
    @abstractmethod
    def get_json(self, url):
        pass