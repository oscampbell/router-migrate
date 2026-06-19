from abc import ABC, abstractmethod
from router_migrate.models import MigrationIR

class BaseGenerator(ABC):
    @abstractmethod
    def generate(self, migration_ir: MigrationIR) -> str:
        """Generates target vendor configuration text from the MigrationIR"""
        pass
