import time
import threading
from hardware import *

class CarbonationStateMachine:
    # Состояния конечного автомата
    STATE_IDLE = 0          # ожидание запуска
    STATE_CHECK_WATER = 1   # проверка уровня воды
    STATE_FILL_WATER = 2    # наполнение водой
    STATE_CARBONATE = 3     # карбонизация CO2
    STATE_RELEASE = 4       # розлив / сброс давления
    STATE_ERROR = 5         # ошибка, автомат останавливается
    STATE_STOPPING = 6      # аварийная остановка

    def __init__(self):
        # Изначально автомат в состоянии ожидания
        self.state = self.STATE_IDLE
        # Целевое давление для карбонизации
        self.target_pressure = 2.5
        # Флаг активного процесса
        self.process_active = False
        # Текущее сообщение об ошибке или предупреждение
        self.error_message = ""
        # Ручная команда RELEASE от веб-интерфейса
        self.release_button_pressed = False
        # Поток выполнения автомата
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
        # Остановить все исполнительные механизмы
        valve_co2.off()
        valve_water.off()
        valve_production.off()
        valve_release.off()
        pump_water.off()
        pressure_release.off()

    def _check_temperature(self):
        # Проверка температуры: датчик возвращает 0-1, нормализуем в °C
        temp = temperature_sensor.value * 100 - 20
        if temp < 5:
            self.error_message = f"Слишком холодно: {temp:.1f}°C (мин. 5°C)"
            return False
        elif temp > 35:
            self.error_message = f"Слишком жарко: {temp:.1f}°C (макс. 35°C)"
            return False
        self.error_message = ""
        return True

    def _pressure_safety_check(self):
        # Проверка давления и включение клапана сброса при превышении
        pressure = pressure_sensor.value * 3
        safety_limit = min(self.target_pressure + 0.2, 3.0)
        if pressure > safety_limit:
            if not pressure_release.value:
                print(f"Давление {pressure:.2f} бар выше безопасности {safety_limit:.2f}, открываем клапан сброса")
            pressure_release.on()
            self.error_message = f"Высокое давление: {pressure:.2f} бар — открывается клапан сброса"
        else:
            if pressure_release.value:
                print(f"Давление {pressure:.2f} бар в норме, закрываем клапан сброса")
            pressure_release.off()
            if self.error_message.startswith("Высокое давление:"):
                self.error_message = ""

    def _run(self):
        # Основной цикл конечного автомата
        self.process_active = True
        self.state = self.STATE_CHECK_WATER
        self.error_message = ""

        while self.process_active:
            # Всегда контролируем давление на каждом шаге
            self._pressure_safety_check()
            if self.state == self.STATE_CHECK_WATER:
                # Сначала проверяем, есть ли вода в баке
                print("Проверка уровня воды...")
                if water_sensor.value < 0.1:
                    self.state = self.STATE_ERROR
                    self.error_message = "НЕТ ВОДЫ"
                else:
                    # Если воды достаточно, идём сразу к карбонизации
                    self.state = self.STATE_CARBONATE

            elif self.state == self.STATE_FILL_WATER:
                # Автоматическое наполнение водой
                print("Наполнение водой...")
                pump_water.on()
                valve_water.on()
                while self.process_active and water_sensor.value < 0.9:
                    self._pressure_safety_check()
                    time.sleep(0.2)
                pump_water.off()
                valve_water.off()
                print("Вода набрана")
                self.state = self.STATE_CARBONATE

            elif self.state == self.STATE_CARBONATE:
                # Карбонизация: накачиваем CO2 до целевого давления
                print(f"Подача CO2 до {self.target_pressure} бар...")
                valve_co2.on()
                while self.process_active and pressure_sensor.value * 3 < self.target_pressure:
                    self._pressure_safety_check()
                    if pressure_release.value:
                        # Если давление превысило безопасный уровень во время карбонизации,
                        # переходим к состоянию RELEASE, чтобы сбросить давление
                        print("Давление превысило безопасность, переходим в состояние РОЗЛИВ для сброса давления")
                        break
                    time.sleep(0.2)
                valve_co2.off()
                if pressure_release.value:
                    self.state = self.STATE_RELEASE
                    continue
                print("Давление достигнуто")
                self.state = self.STATE_RELEASE
                self.release_requested = False

            elif self.state == self.STATE_RELEASE:
                # Состояние розлива: либо сброс давления, либо выпуск продукта
                if pressure_release.value:
                    # При сверхдавлении держим продуктовый клапан закрытым
                    if valve_production.value:
                        valve_production.off()
                    if not self.error_message.startswith("Высокое давление"):
                        self.error_message = "Высокое давление, розлив запрещён"
                    time.sleep(0.2)
                    continue
                # Если давление в норме и RELEASE не нажат, возвращаемся обратно к карбонизации
                if pressure_sensor.value * 3 < self.target_pressure and not (button_release.is_active or self.release_button_pressed):
                    print("Давление нормализовано, возвращаемся в карбонизацию")
                    self.state = self.STATE_CARBONATE
                    continue
                if button_release.is_active or self.release_button_pressed:
                    if not valve_production.value:
                        print("Розлив продукта...")
                    valve_production.on()
                    while self.process_active and (button_release.is_active or self.release_button_pressed) and water_sensor.value > 0.1:
                        self._pressure_safety_check()
                        if pressure_release.value:
                            print("Давление превысило безопасность во время розлива, закрываем клапан продукта")
                            break
                        time.sleep(0.1)
                    valve_production.off()
                    if water_sensor.value <= 0.1:
                        print("Розлив завершён")
                        self.state = self.STATE_FILL_WATER
                    else:
                        print("Кнопка RELEASE отпущена, закрываем клапан продукта")
                    self.release_button_pressed = False
                else:
                    time.sleep(0.1)

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
            self._thread = threading.Thread(target=self._run)
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
        """Установка состояния кнопки RELEASE из веб-интерфейса."""
        if self.state == self.STATE_RELEASE:
            self.release_button_pressed = bool(pressed)
            return True
        return False

    def get_status(self):
        # Формируем JSON-статус для /status
        status = {
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
            'pressure_release': pressure_release.value,
            'button_release': button_release.value,
            'process_active': self.process_active,
            'error_message': self.error_message
        }
        if pressure_release.value and not status['error_message']:
            status['error_message'] = 'Клапан сброса давления открыт'
        return status

machine = CarbonationStateMachine()