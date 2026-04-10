"""Работа с GPIO через sysfs (Linux)"""

import os
import time
from gpio_interface import GPIOInterface

class LinuxGPIO(GPIOInterface):
    def __init__(self):
        self.base_path = "/sys/class/gpio"
    
    def _export_pin(self, pin: int):
        export_path = f"{self.base_path}/export"
        if not os.path.exists(f"{self.base_path}/gpio{pin}"):
            with open(export_path, 'w') as f:
                f.write(str(pin))
            time.sleep(0.1)  # Даём системе время создать файлы
    
    def setup_pin(self, pin: int, direction: str) -> None:
        self._export_pin(pin)
        dir_path = f"{self.base_path}/gpio{pin}/direction"
        with open(dir_path, 'w') as f:
            f.write(direction)
        print(f"[Linux GPIO] Пин {pin} настроен как {direction}")
    
    def write_pin(self, pin: int, value: int) -> None:
        value_path = f"{self.base_path}/gpio{pin}/value"
        with open(value_path, 'w') as f:
            f.write(str(value))
        print(f"[Linux GPIO] Пин {pin} = {value}")
    
    def read_pin(self, pin: int) -> int:
        value_path = f"{self.base_path}/gpio{pin}/value"
        with open(value_path, 'r') as f:
            return int(f.read())