# wifi.py — Controle do ESP8266 via UART (comandos AT)
# Projeto 2 - Lab de Sistemas Embarcados (FEEC/UNICAMP)
# Plataforma: BitDogLab V7 (RP2040)

from machine import UART, Pin
import time


class WiFi:
    def __init__(self, uart_id=0, tx_pin=0, rx_pin=1, baudrate=19200):
        self.uart = UART(uart_id, baudrate=baudrate,
                         tx=Pin(tx_pin), rx=Pin(rx_pin))
        self._conectado = False

    def _enviar_at(self, cmd, espera_ms=2000, ate=("OK", "ERROR")):
        """Envia comando AT e le a resposta. Sai assim que ve um dos tokens
        em `ate` (ex.: 'OK', 'ERROR', '>', '+IPD') em vez de esperar o timeout
        inteiro -> muito mais rapido no caminho feliz. `espera_ms` vira teto."""
        while self.uart.any():
            self.uart.read()
        self.uart.write(cmd + "\r\n")
        t0 = time.ticks_ms()
        resp = b""
        while time.ticks_diff(time.ticks_ms(), t0) < espera_ms:
            if self.uart.any():
                resp += self.uart.read()
                if ate:
                    txt = resp.decode("utf-8", "ignore")
                    if any(tok in txt for tok in ate):
                        break
            else:
                time.sleep_ms(10)
        return resp.decode("utf-8", "ignore")

    def iniciar(self):
        """Testa comunicacao com ESP8266. Tenta 5x com pausa (ESP-01 antigo demora pra acordar)."""
        for _ in range(5):
            resp = self._enviar_at("AT", 1500)
            if "OK" in resp:
                return True
            time.sleep_ms(500)
        return False

    def conectar(self, ssid, senha):
        """Conecta ao Wi-Fi.

        Args:
            ssid: nome da rede
            senha: senha da rede

        Returns:
            True se conectou com sucesso.
        """
        # Modo station + single connection
        self._enviar_at("AT+CWMODE=1", 1000)
        self._enviar_at("AT+CIPMUX=0", 1000)

        # Conectar
        cmd = 'AT+CWJAP="{}","{}"'.format(ssid, senha)
        resp = self._enviar_at(cmd, 15000)

        if "OK" in resp or "WIFI GOT IP" in resp:
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

        # Iniciar conexao TCP (sai assim que conecta)
        cmd_conn = 'AT+CIPSTART="TCP","{}",80'.format(host)
        resp = self._enviar_at(cmd_conn, 5000, ate=("CONNECT", "OK", "ERROR"))
        if "ERROR" in resp and "ALREADY" not in resp:
            return False

        # Montar requisicao HTTP GET
        http_req = "GET {} HTTP/1.1\r\nHost: {}\r\nConnection: close\r\n\r\n".format(path, host)

        # Pedir janela de envio e mandar o payload assim que ver o '>'
        cmd_send = "AT+CIPSEND={}".format(len(http_req))
        self._enviar_at(cmd_send, 1000, ate=(">",))

        # Le a resposta e retorna assim que a conexao fecha / chega o corpo
        resp = self._enviar_at(http_req, 8000, ate=("CLOSED", "+IPD", "SEND FAIL"))

        # Fechar conexao (best-effort)
        self._enviar_at("AT+CIPCLOSE", 800)

        # 209 = rate-limit da CallMeBot -> NAO conta como enviado
        if "209" in resp:
            return False
        return "SEND OK" in resp or "+IPD" in resp

    @property
    def conectado(self):
        return self._conectado
