# feedback.py — Feedback visual (NeoPixel + LED RGB)
# Projeto 2 - Lab de Sistemas Embarcados (FEEC/UNICAMP)
# Plataforma: BitDogLab V7 (RP2040)

from machine import Pin, PWM
import neopixel


# Mapeamento zigzag da matriz 5x5
LED_MATRIX = [
    [24, 23, 22, 21, 20],
    [15, 16, 17, 18, 19],
    [14, 13, 12, 11, 10],
    [ 5,  6,  7,  8,  9],
    [ 4,  3,  2,  1,  0],
]


class Feedback:
    def __init__(self, dist_max=30, dist_alerta=5):
        # NeoPixel 5x5
        self.np = neopixel.NeoPixel(Pin(7), 25)

        # LED RGB (PWM)
        self.led_r = PWM(Pin(13)); self.led_r.freq(1000)
        self.led_g = PWM(Pin(11)); self.led_g.freq(1000)
        self.led_b = PWM(Pin(12)); self.led_b.freq(1000)

        self._estado_anterior = -1
        self.dist_max = dist_max
        self.dist_alerta = dist_alerta

    def atualizar(self, distancia_cm):
        """Faixas escaladas por dist_max / dist_alerta.

        d < 0                    : azul (sem leitura)
        d < dist_alerta          : vermelho piscante (critico)
        dist_alerta .. 1/3 max   : vermelho
        1/3 max   .. 2/3 max     : amarelo
        2/3 max   .. dist_max    : verde
        d > dist_max             : apagado
        """
        faixa_total = self.dist_max - self.dist_alerta
        t1 = self.dist_alerta + faixa_total / 3
        t2 = self.dist_alerta + 2 * faixa_total / 3

        if distancia_cm < 0:
            faixa = -1
        elif distancia_cm < self.dist_alerta:
            faixa = 0
        elif distancia_cm < t1:
            faixa = 1
        elif distancia_cm < t2:
            faixa = 2
        elif distancia_cm <= self.dist_max:
            faixa = 3
        else:
            faixa = 4

        if faixa == self._estado_anterior and faixa != 0:
            return  # sem mudanca (exceto piscante)
        self._estado_anterior = faixa

        if faixa == -1:
            # Erro — azul
            self._cor_rgb(0, 0, 30000)
            self._preencher_np((0, 0, 10))
        elif faixa == 0:
            # Muito proximo — vermelho
            self._cor_rgb(50000, 0, 0)
            self._barra_np(5, (40, 0, 0))
        elif faixa == 1:
            # Proximo — vermelho
            self._cor_rgb(40000, 0, 0)
            self._barra_np(4, (30, 0, 0))
        elif faixa == 2:
            # Atencao — amarelo
            self._cor_rgb(30000, 20000, 0)
            self._barra_np(3, (20, 15, 0))
        elif faixa == 3:
            # Longe — verde
            self._cor_rgb(0, 20000, 0)
            self._barra_np(2, (0, 15, 0))
        else:
            # Sem objeto — apagado
            self._cor_rgb(0, 0, 0)
            self._preencher_np((0, 0, 0))

    def _cor_rgb(self, r, g, b):
        """Define cor do LED RGB via duty cycle."""
        self.led_r.duty_u16(r)
        self.led_g.duty_u16(g)
        self.led_b.duty_u16(b)

    def _preencher_np(self, cor):
        """Preenche toda a matriz com uma cor (r, g, b)."""
        for i in range(25):
            self.np[i] = cor
        self.np.write()

    def _barra_np(self, linhas, cor):
        """Preenche N linhas de baixo para cima como barra de nivel.

        Args:
            linhas: quantas linhas acender (1-5)
            cor: tupla (r, g, b)
        """
        for i in range(25):
            self.np[i] = (0, 0, 0)

        for row in range(5 - linhas, 5):
            for col in range(5):
                self.np[LED_MATRIX[row][col]] = cor

        self.np.write()

    def apagar(self):
        """Desliga tudo."""
        self._cor_rgb(0, 0, 0)
        self._preencher_np((0, 0, 0))
