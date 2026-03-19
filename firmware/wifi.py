# wifi.py — Controle do ESP8266 via UART (comandos AT)
# Projeto 2 - Lab de Sistemas Embarcados (FEEC/UNICAMP)
# Plataforma: BitDogLab V7 (RP2040)

from machine import UART, Pin
import time


class WiFi:
    def __init__(self, uart_id=0, tx_pin=0, rx_pin=1, baudrate=115200):
        self.uart = UART(uart_id, baudrate=baudrate,
                         tx=Pin(tx_pin), rx=Pin(rx_pin))
        self._conectado = False

    def _enviar_at(self, cmd, espera_ms=2000):
        """Envia comando AT e retorna resposta como string."""
        self.uart.write(cmd + "\r\n")
        time.sleep_ms(espera_ms)
        resp = b""
        while self.uart.any():
            resp += self.uart.read()
        return resp.decode("utf-8", "ignore")

    def iniciar(self):
        """Testa comunicacao com ESP8266."""
        resp = self._enviar_at("AT", 1000)
        return "OK" in resp

    def conectar(self, ssid, senha):
        """Conecta ao Wi-Fi.

        Args:
            ssid: nome da rede
            senha: senha da rede

        Returns:
            True se conectou com sucesso.
        """
        # Modo station
        self._enviar_at("AT+CWMODE=1", 1000)

        # Conectar
        cmd = 'AT+CWJAP="{}","{}"'.format(ssid, senha)
        resp = self._enviar_at(cmd, 10000)

        if "OK" in resp or "WIFI CONNECTED" in resp:
            self._conectado = True
            return True

        self._conectado = False
        return False

    def enviar_whatsapp(self, telefone, apikey, mensagem):
        """Envia mensagem via CallMeBot WhatsApp API.

        Args:
            telefone: numero com DDI (ex: "5519999999999")
            apikey: chave da API CallMeBot
            mensagem: texto da mensagem

        Returns:
            True se enviou com sucesso.
        """
        # Substituir espacos por + na mensagem
        msg_encoded = mensagem.replace(" ", "+")

        host = "api.callmebot.com"
        path = "/whatsapp.php?phone={}&text={}&apikey={}".format(
            telefone, msg_encoded, apikey
        )

        # Iniciar conexao TCP
        cmd_conn = 'AT+CIPSTART="TCP","{}",80'.format(host)
        resp = self._enviar_at(cmd_conn, 5000)
        if "ERROR" in resp and "ALREADY" not in resp:
            return False

        # Montar requisicao HTTP GET
        http_req = "GET {} HTTP/1.1\r\nHost: {}\r\n\r\n".format(path, host)

        # Enviar dados
        cmd_send = "AT+CIPSEND={}".format(len(http_req))
        self._enviar_at(cmd_send, 1000)
        time.sleep_ms(500)

        resp = self._enviar_at(http_req, 5000)

        # Fechar conexao
        self._enviar_at("AT+CIPCLOSE", 1000)

        return "SEND OK" in resp or "+IPD" in resp

    @property
    def conectado(self):
        return self._conectado
