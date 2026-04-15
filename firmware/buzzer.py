# buzzer.py — Buzzer com beep proporcional a distancia
# Projeto 2 - Lab de Sistemas Embarcados (FEEC/UNICAMP)
# Plataforma: BitDogLab V7 (RP2040)

from machine import Pin, PWM
import time


class Buzzer:
    def __init__(self, pin=21):
        self.pwm = PWM(Pin(pin))
        self.pwm.duty_u16(0)
        self._ultimo_beep = 0
        self.mute = False

    def toggle_mute(self):
        self.mute = not self.mute
        if self.mute:
            self.parar()
        return self.mute

    def beep_proximidade(self, distancia_cm, tempo_ms):
        """Controla frequencia de beeps baseado na distancia.

        Quanto mais perto, mais rapido o beep (estilo sensor de re).
        < 10cm:  beep continuo
        10-30cm: beep a cada 100ms
        30-60cm: beep a cada 300ms
        60-100cm: beep a cada 600ms
        > 100cm: silencio

        Args:
            distancia_cm: distancia medida
            tempo_ms: timestamp atual (time.ticks_ms)
        """
        if self.mute or distancia_cm < 0 or distancia_cm > 100:
            self.parar()
            return

        if distancia_cm < 10:
            # Beep continuo — tom agudo
            self._tocar(2000)
            return

        # Definir intervalo do beep
        if distancia_cm < 30:
            intervalo = 100
            freq = 1500
        elif distancia_cm < 60:
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
