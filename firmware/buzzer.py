# buzzer.py — Buzzer com beep proporcional a distancia
# Projeto 2 - Lab de Sistemas Embarcados (FEEC/UNICAMP)
# Plataforma: BitDogLab V7 (RP2040)

from machine import Pin, PWM
import time


class Buzzer:
    def __init__(self, pin=21, dist_max=30, dist_alerta=5):
        self.pwm = PWM(Pin(pin))
        self.pwm.duty_u16(0)
        self._ultimo_beep = 0
        self.mute = False
        self.dist_max = dist_max
        self.dist_alerta = dist_alerta

    def toggle_mute(self):
        self.mute = not self.mute
        if self.mute:
            self.parar()
        return self.mute

    def beep_proximidade(self, distancia_cm, tempo_ms):
        """Beep escalado por dist_max / dist_alerta (sensor de re).

        d < dist_alerta          : beep continuo agudo
        dist_alerta .. 1/3 max   : beep rapido
        1/3 max   .. 2/3 max     : beep medio
        2/3 max   .. dist_max    : beep lento
        d > dist_max             : silencio
        """
        if self.mute or distancia_cm < 0 or distancia_cm > self.dist_max:
            self.parar()
            return

        if distancia_cm < self.dist_alerta:
            self._tocar(2000)
            return

        faixa = self.dist_max - self.dist_alerta
        t1 = self.dist_alerta + faixa / 3
        t2 = self.dist_alerta + 2 * faixa / 3

        if distancia_cm < t1:
            intervalo = 100
            freq = 1500
        elif distancia_cm < t2:
            intervalo = 300
            freq = 1000
        else:
            intervalo = 600
            freq = 800

        # Alternar beep/silencio
        ciclo = time.ticks_diff(tempo_ms, self._ultimo_beep)
        if ciclo >= intervalo * 2:
            self._ultimo_beep = tempo_ms

        if ciclo < intervalo:
            self._tocar(freq)
        else:
            self.parar()

    def _tocar(self, freq_hz):
        self.pwm.freq(freq_hz)
        self.pwm.duty_u16(32768)

    def parar(self):
        self.pwm.duty_u16(0)

    def beep_curto(self, freq=1000, duracao_ms=100):
        """Beep unico para feedback."""
        if self.mute:
            return
        self._tocar(freq)
        time.sleep_ms(duracao_ms)
        self.parar()
