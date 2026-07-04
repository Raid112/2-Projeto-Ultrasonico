# buzzer.py — Buzzer com beep proporcional a distancia
# Projeto 2 - Lab de Sistemas Embarcados (FEEC/UNICAMP)
# Plataforma: BitDogLab V7 (RP2040)

from machine import Pin, PWM
import time


class Buzzer:
    # Frequencias DISCRETAS por faixa de distancia (mesmas faixas do LED).
    # Mais perto = mais agudo. Indice 0 = mais perto ... 3 = mais longe.
    FREQ_FAIXA = (1000, 800, 600, 400)

    def __init__(self, pin=21, dist_max=30, dist_alerta=5):
        self.pwm = PWM(Pin(pin))
        self.pwm.duty_u16(0)
        self.mute = False
        self.dist_max = dist_max
        self.dist_alerta = dist_alerta

    def toggle_mute(self):
        self.mute = not self.mute
        if self.mute:
            self.parar()
        return self.mute

    def beep_proximidade(self, distancia_cm, tempo_ms=0):
        """Tom continuo no tempo (sem gaps) mas com pitch em DEGRAUS discretos
        por faixa de distancia -- as mesmas faixas do feedback de LED. Mais
        perto = mais agudo. Silencio quando nao ha objeto ou alem de dist_max.
        (tempo_ms mantido so por compatibilidade de chamada.)
        """
        if self.mute or distancia_cm < 0 or distancia_cm > self.dist_max:
            self.parar()
            return

        # mesmas faixas do LED: critica + 3 tercos ate dist_max
        faixa_total = self.dist_max - self.dist_alerta
        t1 = self.dist_alerta + faixa_total / 3
        t2 = self.dist_alerta + 2 * faixa_total / 3

        if distancia_cm < self.dist_alerta:
            faixa = 0
        elif distancia_cm < t1:
            faixa = 1
        elif distancia_cm < t2:
            faixa = 2
        else:
            faixa = 3

        self._tocar(self.FREQ_FAIXA[faixa])

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
