# ultrasonico.py — Leitura do sensor HC-SR04
# Projeto Final - Bengala Assistiva - Lab de Sistemas Embarcados (FEEC/UNICAMP)
# Plataforma: BitDogLab V7 (RP2040)

from machine import Pin, time_pulse_us
import time


class Ultrasonico:
    def __init__(self, trig_pin=8, echo_pin=9, echo_timeout_us=30000):
        self.trig = Pin(trig_pin, Pin.OUT)
        self.echo = Pin(echo_pin, Pin.IN)
        self.trig.value(0)
        self.echo_timeout_us = echo_timeout_us

    def medir_cm(self):
        """Mede distancia em centimetros.

        Retorna distancia (float) ou -1 se timeout/erro.
        Velocidade do som: 343 m/s => 29.15 us/cm (ida e volta = /2).
        """
        # Pulso de trigger: 10us HIGH
        self.trig.value(0)
        time.sleep_us(2)
        self.trig.value(1)
        time.sleep_us(10)
        self.trig.value(0)

        # Medir duracao do echo (timeout configuravel)
        duracao = time_pulse_us(self.echo, 1, self.echo_timeout_us)

        if duracao < 0:
            return -1  # timeout

        distancia = (duracao / 2.0) / 29.15
        return round(distancia, 1)
