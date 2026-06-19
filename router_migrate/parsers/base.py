from abc import ABC, abstractmethod
from typing import List, Tuple
from router_migrate.models import DeviceIR

class BaseParser(ABC):
    @abstractmethod
    def parse(self, config_text: str) -> DeviceIR:
        """Parses a full vendor configuration into the DeviceIR"""
        pass
    
    @abstractmethod
    def parse_snippet(self, snippet_text: str) -> DeviceIR:
        """Parses a snippet of config into a partial DeviceIR"""
        pass
