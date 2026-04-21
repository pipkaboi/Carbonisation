import threading
from flask import Flask, jsonify, render_template, request
from hardware import *
from carbonization import machine

app = Flask(__name__)


@app.route('/')
def index():
    # Передаём данные в HTML
    return render_template('index.html',
        pressure=round(pressure_sensor.value * 3, 1),           # давление в бар
        water=round(water_sensor.value * 100, 1),               # уровень воды %
        temp=round(temperature_sensor.value * 100 - 20, 1),     # температура °C
        valve_co2=valve_co2.value,                               # клапан CO2
        valve_water=valve_water.value,                           # клапан воды
        valve_production=valve_production.value,                 # клапан продукта
        pump_water=pump_water.value,                             # насос воды
        pressure_release=pressure_release.value,                 # клапан сброса давления
        button_release=button_release.value,                    # состояние кнопки RELEASE
        target_pressure=machine.target_pressure,                # целевое давление
        error_message=machine.error_message,                    # сообщение об ошибке
        status=machine._get_state_name()                         #статус конечного автомата
        )


@app.route('/start', methods=['POST'])
def start():
    result = machine.start()
    return jsonify({'success': result, 'message': 'Process started' if result else 'Failed to start'})

@app.route('/stop', methods=['POST'])
def stop():
    result = machine.stop()
    return jsonify({'success': result, 'message': 'Process stopped' if result else 'Failed to stop'})

@app.route('/release', methods=['POST'])
def release():
    data = request.get_json() or {}
    pressed = data.get('pressed', False)
    machine.set_release_button(pressed)
    return jsonify({'status': 'ok', 'pressed': pressed})

@app.route('/set_target', methods=['POST'])
def set_target():
    data = request.get_json()
    pressure = data.get('pressure', 2.5)
    machine.set_target_pressure(pressure)
    return jsonify({'status': 'ok', 'target': machine.target_pressure})

@app.route('/set_pressure', methods=['POST'])
def set_pressure():
    data = request.get_json()
    value = data.get('value', 0)
    if IS_EMULATION:
        pressure_sensor.set_value(value / 3) # type: ignore
    return 'ok'

@app.route('/set_water', methods=['POST'])
def set_water():
    data = request.get_json()
    value = data.get('value', 0)
    if IS_EMULATION:
        water_sensor.set_value(value / 100) # type: ignore
    return 'ok'

@app.route('/set_temp', methods=['POST'])
def set_temp():
    data = request.get_json()
    value = data.get('value', 0)
    if IS_EMULATION:
        normalized = (value + 20) / 100  # нормализуем обратно в 0-1
        temperature_sensor.set_value(normalized) # type: ignore
        machine._check_temperature()
    return 'ok'


@app.route('/status')
def status():
    return jsonify(machine.get_status())


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)