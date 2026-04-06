# teste_sensor.py — Teste puro do HC-SR04
from machine import Pin, time_pulse_us
import time

trig = Pin(8, Pin.OUT)
echo = Pin(9, Pin.IN)
trig.value(0)

print("Testando HC-SR04 (GPIO8=trig, GPIO9=echo)")
print("Ctrl+C para parar\n")

while True:
    trig.value(0)
    time.sleep_us(2)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)

    duracao = time_pulse_us(echo, 1, 30000)

    if duracao < 0:
        print("Sem leitura (timeout)")
    else:
        dist = (duracao / 2.0) / 29.15
        print("Distancia: {:.1f} cm  (duracao: {} us)".format(dist, duracao))

    time.sleep_ms(500)
