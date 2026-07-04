# buzzer.py — Buzzer com beep proporcional a distancia
# Projeto 2 - Lab de Sistemas Embarcados (FEEC/UNICAMP)
# Plataforma: BitDogLab V7 (RP2040)

from machine import Pin, PWM
import time


class Buzzer:
    # Mapeamento linear de frequencia (Hz) com a proximidade:
    FREQ_LONGE = 400     # objeto no limite (dist_max) -> grave
    FREQ_PERTO = 2500    # objeto colado -> agudo
    # Cadencia (ms) linear: longe = bipe lento, perto = bipe rapido
    INTERVALO_LONGE = 700
    INTERVALO_PERTO = 60

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
        """Sensor de re LINEAR: frequencia e cadencia variam continuamente
        com a distancia. Mais perto = mais agudo e bipes mais rapidos.
        Abaixo de dist_alerta vira tom continuo. Acima de dist_max, silencio.
        """
        if self.mute or distancia_cm < 0 or distancia_cm > self.dist_max:
            self.parar()
            return

        # proximidade linear: 0.0 (longe = dist_max) -> 1.0 (colado)
        prox = (self.dist_max - distancia_cm) / self.dist_max
        if prox < 0:
            prox = 0.0
        elif prox > 1:
            prox = 1.0

        # frequencia linear com a proximidade
        freq = int(self.FREQ_LONGE + prox * (self.FREQ_PERTO - self.FREQ_LONGE))

        # zona critica: tom continuo (sem cortar)
        if distancia_cm < self.dist_alerta:
            self._tocar(freq)
            return

        # cadencia linear: longe = lento, perto = rapido
        intervalo = int(self.INTERVALO_LONGE -
                        prox * (self.INTERVALO_LONGE - self.INTERVALO_PERTO))

        ciclo = time.ticks_diff(tempo_ms, self._ultimo_beep)
        if ciclo >= intervalo * 2:
            self._ultimo_beep = tempo_ms
            ciclo = 0

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
