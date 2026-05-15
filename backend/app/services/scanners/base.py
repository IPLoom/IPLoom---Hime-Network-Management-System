from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseScanner(ABC):
    @abstractmethod
    async def scan(self, target: str, **kwargs) -> List[Dict[str, Any]]:
        """
        Perform a scan on the target and return a list of found devices/results.
        """
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the scanner."""
        pass
