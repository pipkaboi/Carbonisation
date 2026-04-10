from gpio_windows import WindowsGPIO
from carbonization import CarbonationSystem

gpio = WindowsGPIO()

gpio.setup_pin(0, "in") # Датчик давления
gpio.setup_pin(10, "out") # Клапан CO2

def main():
    # Создаём систему карбонизации
    soda = CarbonationSystem(gpio, valve_pin=17)
    
    # Устанавливаем уровень газировки
    soda.set_target_pressure(2.5)  # 2.5 бара — как в магазинной газировке
    
    # Запускаем процесс
    soda.carbonate()
    
if __name__ == "__main__":
    main()