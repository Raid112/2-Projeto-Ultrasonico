# display.py — Painel OLED para o Projeto Ultrasonico
# Projeto 2 - Lab de Sistemas Embarcados (FEEC/UNICAMP)
# Plataforma: BitDogLab V7 (RP2040)

from machine import Pin, SoftI2C
from ssd1306 import SSD1306_I2C


class Display:
    def __init__(self, i2c=None):
        if i2c is None:
            i2c = SoftI2C(scl=Pin(3), sda=Pin(2))
        self.oled = SSD1306_I2C(128, 64, i2c)
        self._estado_anterior = None

    def atualizar(self, distancia_cm, wifi_ok, alerta_enviado=False):
        """Atualiza display com distancia e status.

        Args:
            distancia_cm: distancia medida (ou -1 se erro)
            wifi_ok: True se Wi-Fi conectado
            alerta_enviado: True se acabou de enviar alerta WhatsApp
        """
        estado = (round(distancia_cm), wifi_ok, alerta_enviado)
        if estado == self._estado_anterior:
            return
        self._estado_anterior = estado

        self.oled.fill(0)

        # Titulo
        self.oled.text("Sensor Ultra.", 8, 0)

        # Distancia grande no centro
        if distancia_cm < 0:
            self.oled.text("Sem leitura", 12, 20)
        else:
            dist_str = "{} cm".format(distancia_cm)
            # Centralizar texto
            x = max(0, (128 - len(dist_str) * 8) // 2)
            self.oled.text(dist_str, x, 18)

            # Barra visual de distancia (0-200cm mapeado para 0-120px)
            barra_w = min(120, max(2, int(distancia_cm * 120 / 200)))
            self.oled.fill_rect(4, 32, barra_w, 8, 1)
            self.oled.rect(4, 32, 120, 8, 1)

        # Status Wi-Fi
        wifi_txt = "WiFi: OK" if wifi_ok else "WiFi: --"
        self.oled.text(wifi_txt, 0, 48)

        # Status alerta
        if alerta_enviado:
            self.oled.text("WhatsApp!", 64, 48)

        self.oled.show()

    def mostrar_inicio(self):
        """Tela de boas-vindas."""
        self.oled.fill(0)
        self.oled.text("Projeto Ultra.", 8, 4)
        self.oled.text("Sensor + WhatsApp", 0, 20)
        self.oled.text("Lab Embarcados", 8, 36)
        self.oled.text("FEEC/UNICAMP", 16, 52)
        self.oled.show()

    def mostrar_wifi(self, status):
        """Mostra status da conexao Wi-Fi."""
        self.oled.fill(0)
        self.oled.text("Conectando...", 8, 16)
        self.oled.text(status, 0, 36)
        self.oled.show()

    def mostrar_erro(self, titulo, linha1="", linha2=""):
        """Tela de erro com titulo e duas linhas de detalhe."""
        self.oled.fill(0)
        self.oled.text("!! ERRO !!", 24, 0)
        self.oled.hline(0, 10, 128, 1)
        self.oled.text(titulo[:16], 0, 18)
        if linha1:
            self.oled.text(linha1[:16], 0, 34)
        if linha2:
            self.oled.text(linha2[:16], 0, 50)
        self.oled.show()

    def mostrar_debug(self, mag_atual, mag_min, mag_max, freefalls, estado):
        """Tela de debug do IMU: magnitude de accel + contadores."""
        self.oled.fill(0)
        self.oled.text("IMU DEBUG", 28, 0)
        self.oled.text("mag {:>5.2f} g".format(mag_atual), 0, 14)
        self.oled.text("min {:>5.2f}".format(mag_min), 0, 26)
        self.oled.text("max {:>5.2f}".format(mag_max), 0, 38)
        self.oled.text("ff {}  {}".format(freefalls, estado[:6]), 0, 52)
        self.oled.show()
