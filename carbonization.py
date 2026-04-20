import time
import threading
from hardware import *

class CarbonationStateMachine:

    STATE_IDLE = 0
    STATE_CHECK_WATER = 1
    STATE_FILL_WATER = 2
    STATE_CARBONATE = 3
    STATE_RELEASE = 4
    STATE_ERROR = 5
    STATE_STOPPING = 6

    def __init__(self):
        self.state = self.STATE_IDLE
        self.target_pressure = 2.5
        self.process_active = False
        self.error_message = ""
        self.release_button_pressed = False
        self._thread = None

    def _get_state_name(self):
        names = {
            0: "ОЖИДАНИЕ",
            1: "ПРОВЕРКА ВОДЫ",
            2: "НАПОЛНЕНИЕ ВОДОЙ",
            3: "КАРБОНИЗАЦИЯ",
            4: "РОЗЛИВ",
            5: "ОШИБКА",
            6: "ОСТАНОВКА"
        }
        return names.get(self.state, "НЕИЗВЕСТНО")

    def set_target_pressure(self, pressure):
        self.target_pressure = max(0.5, min(3.0, pressure))
        print(f"Целевое давление: {self.target_pressure} бар")

    def _stop_all(self):
        valve_co2.off()
        valve_water.off()
        valve_production.off()
        valve_release.off()
        pump_water.off()
        pressure_release.off()

    def _check_temperature(self):
        temp = temperature_sensor.value * 100 - 20
        if temp < 5:
            self.error_message = f"Слишком холодно: {temp:.1f}°C (мин. 5°C)"
            return False
        elif temp > 35:
            self.error_message = f"Слишком жарко: {temp:.1f}°C (макс. 35°C)"
            return False
        self.error_message = ""
        return True

    def _run(self):
        self.process_active = True
        self.state = self.STATE_CHECK_WATER
        self.error_message = ""

        while self.process_active:
            if self.state == self.STATE_CHECK_WATER:
                print("Проверка уровня воды...")
                if water_sensor.value < 0.1:
                    self.state = self.STATE_ERROR
                    self.error_message = "НЕТ ВОДЫ"
                else:
                    # Если воды достаточно, идём в карбонизацию, минуя наполнение
                    self.state = self.STATE_CARBONATE

            elif self.state == self.STATE_FILL_WATER:
                print("Наполнение водой...")
                pump_water.on()
                valve_water.on()
                while self.process_active and water_sensor.value < 0.9:
                    time.sleep(0.2)
                pump_water.off()
                valve_water.off()
                print("Вода набрана")
                self.state = self.STATE_CARBONATE

            elif self.state == self.STATE_CARBONATE:
                print(f"Подача CO2 до {self.target_pressure} бар...")
                valve_co2.on()
                while self.process_active and pressure_sensor.value * 3 < self.target_pressure:
                    time.sleep(0.2)
                valve_co2.off()
                print("Давление достигнуто")
                self.state = self.STATE_RELEASE
                self.release_requested = False

            elif self.state == self.STATE_RELEASE:
                if button_release.is_active or self.release_button_pressed:
                    if not valve_production.value:
                        print("Розлив продукта...")
                    valve_production.on()
                    while self.process_active and (button_release.is_active or self.release_button_pressed) and water_sensor.value > 0.1:
                        time.sleep(0.2)
                    valve_production.off()
                    if water_sensor.value <= 0.1:
                        print("Розлив завершён")
                        self.state = self.STATE_IDLE
                        self.process_active = False
                    else:
                        print("Кнопка RELEASE отпущена, закрываем клапан продукта")
                    self.release_button_pressed = False
                else:
                    time.sleep(0.2)

            elif self.state == self.STATE_ERROR:
                print(f"Ошибка: {self.error_message}")
                time.sleep(2)
                self._stop_all()
                self.state = self.STATE_IDLE
                self.process_active = False

            elif self.state == self.STATE_STOPPING:
                print("Аварийная остановка")
                self._stop_all()
                self.state = self.STATE_IDLE
                self.process_active = False

            time.sleep(0.1)

        self._stop_all()
        print("Конечный автомат остановлен")

    def start(self):
        if not self.process_active and self.state == self.STATE_IDLE:
            if not self._check_temperature():
                return False
            if water_sensor.value < 0.1:
                self.error_message = "НЕТ ВОДЫ"
                return False
            self._thread = threading.Thread(target=self._run, daemon=True)
            self._thread.start()
            return True
        return False

    def stop(self):
        if self.process_active:
            self.process_active = False
            self.state = self.STATE_STOPPING
            return True
        return False

    def set_release_button(self, pressed):
        """Установка состояния кнопки RELEASE"""
        if self.state == self.STATE_RELEASE:
            self.release_button_pressed = bool(pressed)
            return True
        return False

    def get_status(self):
        return {
            'pressure': round(pressure_sensor.value * 3, 1),
            'water': round(water_sensor.value * 100, 1),
            'temp': round(temperature_sensor.value * 100 - 20, 1),
            'state': self.state,
            'state_name': self._get_state_name(),
            'target_pressure': self.target_pressure,
            'valve_co2': valve_co2.value,
            'valve_water': valve_water.value,
            'valve_production': valve_production.value,
            'pump_water': pump_water.value,
            'valve_release': valve_release.value,
            'process_active': self.process_active,
            'error_message': self.error_message
        }

machine = CarbonationStateMachine()