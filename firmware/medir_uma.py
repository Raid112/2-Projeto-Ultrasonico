# medir_uma.py — Uma leitura estavel (mediana de 15 amostras)
# Use para coletar pares (real, medido) para calibracao.
from machine import Pin, time_pulse_us
import time

trig = Pin(8, Pin.OUT)
echo = Pin(9, Pin.IN)
trig.value(0)
time.sleep_ms(50)


def medir_us():
    trig.value(0)
    time.sleep_us(2)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)
    return time_pulse_us(echo, 1, 30000)


amostras = []
for _ in range(15):
    us = medir_us()
    if us >= 0:
        amostras.append((us / 2.0) / 29.15)
    time.sleep_ms(60)

if not amostras:
    print("timeout — sem eco")
else:
    amostras.sort()
    mediana = amostras[len(amostras) // 2]
    print("medido: {:.1f} cm  (n={}, min={:.1f}, max={:.1f})".format(
        mediana, len(amostras), amostras[0], amostras[-1]))
