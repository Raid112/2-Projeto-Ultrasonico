# vibra.py — Motor vibratorio (ERM) proporcional a distancia
# Projeto 2 - Lab de Sistemas Embarcados (FEEC/UNICAMP)
# Plataforma: BitDogLab V7 (RP2040)
#
# Canal haptico analogo ao buzzer: quanto mais perto, mais forte e mais
# rapida a vibracao. Zona critica vira vibracao continua.
# GPIO14 -> circuito driver (transistor) -> motor vibratorio.
# PWM varia o DUTY (intensidade). ERM tem limiar de partida, por isso
# a intensidade e mapeada entre DUTY_MIN (minimo que ja gira) e DUTY_MAX.

from machine import Pin, PWM
import time


class Vibra:
    # Intensidade (duty 0..65535) linear com a proximidade.
    # Faixa restrita a [75%, 100%]: abaixo de ~50% este ERM nao parte, e entre
    # 75-100% a intensidade quase nao muda ao toque -> a distancia e' comunicada
    # sobretudo pela CADENCIA (pulso lento longe -> rapido perto), nao pela forca.
    DUTY_MIN = 49000     # objeto no limite (dist_max) -> ~75% (parte com folga)
    DUTY_MAX = 65535     # objeto colado -> 100%
    # Cadencia (ms) linear: longe = pulso lento, perto = pulso rapido
    INTERVALO_LONGE = 700
    INTERVALO_PERTO = 60

    def __init__(self, pin=14, dist_max=30, dist_alerta=5):
        self.pwm = PWM(Pin(pin))
        self.pwm.freq(1000)      # motor integra o PWM; 1kHz suave para o driver
        self.pwm.duty_u16(0)
        self._ultimo_pulso = 0
        self.mute = False
        self.dist_max = dist_max
        self.dist_alerta = dist_alerta

    def toggle_mute(self):
        self.mute = not self.mute
        if self.mute:
            self.parar()
        return self.mute

    def vibrar_proximidade(self, distancia_cm, tempo_ms):
        """Haptico LINEAR: intensidade e cadencia variam continuamente com a
        distancia. Mais perto = mais forte e pulsos mais rapidos.
        Abaixo de dist_alerta vira vibracao continua. Acima de dist_max, parado.
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

        # intensidade linear com a proximidade
        duty = int(self.DUTY_MIN + prox * (self.DUTY_MAX - self.DUTY_MIN))

        # zona critica: vibracao continua (sem cortar)
        if distancia_cm < self.dist_alerta:
            self._vibrar(duty)
            return

        # cadencia linear: longe = lento, perto = rapido
        intervalo = int(self.INTERVALO_LONGE -
                        prox * (self.INTERVALO_LONGE - self.INTERVALO_PERTO))

        ciclo = time.ticks_diff(tempo_ms, self._ultimo_pulso)
        if ciclo >= intervalo * 2:
            self._ultimo_pulso = tempo_ms
            ciclo = 0

        if ciclo < intervalo:
            self._vibrar(duty)
        else:
            self.parar()

    def _vibrar(self, duty_u16):
        self.pwm.duty_u16(duty_u16)

    def parar(self):
        self.pwm.duty_u16(0)

    def pulso_curto(self, duracao_ms=200):
        """Pulso unico de vibracao para feedback (ex: alerta de queda)."""
        if self.mute:
            return
        self._vibrar(self.DUTY_MAX)
        time.sleep_ms(duracao_ms)
        self.parar()
