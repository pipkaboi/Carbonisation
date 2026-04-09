"""Эмуляция GPIO через JSON-файл"""

import json
import os
from gpio_interface import GPIOInterface

class WindowsGPIO(GPIOInterface):
    def __init__(self, state_file: str = "gpio_state.json"):
        self.state_file = state_file
        self.pins = {}
        # Загружаем сохранённое состояние, если файл есть
        if os.path.exists(state_file):
            with open(state_file, 'r') as f:
                self.pins = json.load(f)
    
    def _save(self):
        with open(self.state_file, 'w') as f:
            json.dump(self.pins, f, indent=2)
    
    def setup_pin(self, pin: int, direction: str) -> None:
        self.pins[f"pin_{pin}_dir"] = direction
        self.pins[f"pin_{pin}_value"] = 0
        self._save()
        print(f"[GPIO] Пин {pin} настроен как {direction}")
    
    def write_pin(self, pin: int, value: int) -> None:
        self.pins[f"pin_{pin}_value"] = value
        self._save()
        print(f"[GPIO] Пин {pin} = {value}")
    
    def read_pin(self, pin: int) -> int:
        return self.pins.get(f"pin_{pin}_value", 0)