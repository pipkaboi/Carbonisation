"""Абстрактный интерфейс для работы с GPIO."""

from abc import ABC, abstractmethod

class GPIOInterface(ABC):
    @abstractmethod
    def write_pin(self, pin: int, value: int) -> None:
        """Установить значение на пине (1 = HIGH, 0 = LOW)"""
        pass
    
    @abstractmethod
    def read_pin(self, pin: int) -> int:
        """Прочитать значение с пина"""
        pass
    
    @abstractmethod
    def setup_pin(self, pin: int, direction: str) -> None:
        """Настроить пин как INPUT или OUTPUT"""
        pass