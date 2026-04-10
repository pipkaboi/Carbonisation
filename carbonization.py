"""Логика системы карбонизации"""

import time

class CarbonationSystem:
    def __init__(self, gpio, valve_pin=17, pressure_sensor_pin=18):
        self.gpio = gpio
        self.valve_pin = valve_pin
        self.pressure_sensor_pin = pressure_sensor_pin
        self.target_pressure = 2.5  # бар
        self.current_pressure = 0.0

    def set_target_pressure(self, pressure: float):
        self.target_pressure = pressure
        print(f"Целевое давление: {pressure} бар")
    
    def read_pressure(self) -> float:
        """Эмуляция чтения давления. В реальности здесь был бы АЦП."""
        # Для демонстрации: давление растёт, когда клапан открыт
        # В реальной системе ты бы читал датчик через gpio.read_pin()
        return self.current_pressure
    
    def update_pressure(self, valve_open: bool):
        """Симуляция изменения давления. При реальной работе这个方法 не нужен."""
        if valve_open and self.current_pressure < self.target_pressure:
            self.current_pressure += 0.15
        elif not valve_open and self.current_pressure > 0:
            self.current_pressure -= 0.05
        if self.current_pressure > self.target_pressure:
            self.current_pressure = self.target_pressure
        if self.current_pressure < 0:
            self.current_pressure = 0
    
    def carbonate(self):
        """Главный цикл карбонизации."""
        print(f"\nЗАПУСК КАРБОНИЗАЦИИ")
        print(f"Цель: {self.target_pressure} бар")
        print("-" * 40)
        
        self.current_pressure = 0.0
        cycles = 0
        
        while self.current_pressure < self.target_pressure:
            # Открываем клапан
            self.gpio.write_pin(self.valve_pin, 1)
            self.update_pressure(valve_open=True)
            cycles += 1
            
            print(f"Цикл {cycles}: давление {self.current_pressure:.1f} / {self.target_pressure} бар")
            time.sleep(0.5)
        
        # Достигли цели — закрываем клапан
        self.gpio.write_pin(self.valve_pin, 0)
        print("-" * 40)
        print(f"✅ ГОТОВО! Давление достигнуто: {self.current_pressure:.1f} бар")