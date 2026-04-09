from gpio_windows import WindowsGPIO

gpio = WindowsGPIO()

gpio.setup_pin(0, "in")
gpio.setup_pin(10, "out") 
