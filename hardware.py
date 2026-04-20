import os
from gpiozero import DigitalInputDevice, DigitalOutputDevice, MCP3008

IS_EMULATION = not os.path.exists('/sys/class/gpio')

if IS_EMULATION:
    from gpiozero import Device
    from gpiozero.pins.mock import MockFactory
    Device.pin_factory = MockFactory()
    print("Режим эмуляции")
    
    # Эмулируем аналоговые датчики
    class EmulatedMCP3008:
        def __init__(self, channel, initial=0.5):
            self.channel = channel
            self._value = initial
        @property
        def value(self):
            return self._value
        def set_value(self, value):
            self._value = value
    
    pressure_sensor = EmulatedMCP3008(0, 0.0)
    water_sensor = EmulatedMCP3008(1, 0.8)  # 80% воды
    temperature_sensor = EmulatedMCP3008(2, 0.5)  # 25°C
else:
    from gpiozero import MCP3008
    pressure_sensor = MCP3008(channel=0)
    water_sensor = MCP3008(channel=1)
    temperature_sensor = MCP3008(channel=2)

# ===== ПИНЫ (не используем 8,9,10,11, тк это аналоговые) =====
valve_co2           = DigitalOutputDevice(0, initial_value=False)
valve_water         = DigitalOutputDevice(1, initial_value=False)
valve_production    = DigitalOutputDevice(2, initial_value=False)
valve_release       = DigitalOutputDevice(3, initial_value=False)
pump_water          = DigitalOutputDevice(4, initial_value=False)
pressure_release    = DigitalOutputDevice(5, initial_value=False)

button_release       = DigitalInputDevice(6)