# teste_wifi.py — Diagnostico completo de conexao Wi-Fi via ESP8266
from machine import UART, Pin
import time

SSID = "Caio-Rede"
SENHA = "87654321"
BAUDRATE = 19200

uart = UART(0, baudrate=BAUDRATE, tx=Pin(0), rx=Pin(1))
time.sleep_ms(200)


def at(cmd, espera_ms=2000, titulo=None):
    print("\n>>>", titulo or cmd)
    while uart.any():
        uart.read()
    uart.write(cmd + "\r\n")
    t0 = time.ticks_ms()
    resp = b""
    while time.ticks_diff(time.ticks_ms(), t0) < espera_ms:
        if uart.any():
            resp += uart.read()
        time.sleep_ms(50)
    texto = resp.decode("utf-8", "ignore")
    print(texto.strip() if texto.strip() else "(sem resposta)")
    return texto


# 1. Sanity check
at("AT", 1000, "1. AT (sanity)")

# 2. Versao do firmware
at("AT+GMR", 2000, "2. Versao firmware")

# 3. Modo station
at("AT+CWMODE=1", 1000, "3. Modo station")

# 4. Listar redes visiveis
print("\n>>> 4. Escaneando redes (pode demorar ~5s)...")
resp = at("AT+CWLAP", 8000, "4. AT+CWLAP")
if SSID in resp:
    print(">>> Rede '{}' VISIVEL pelo ESP".format(SSID))
else:
    print(">>> ATENCAO: rede '{}' NAO aparece no scan!".format(SSID))

# 5. Tentar conectar
print("\n>>> 5. Conectando em '{}'...".format(SSID))
resp = at('AT+CWJAP="{}","{}"'.format(SSID, SENHA), 15000, "5. AT+CWJAP")

if "OK" in resp or "WIFI CONNECTED" in resp or "WIFI GOT IP" in resp:
    print(">>> WIFI OK!")
elif "FAIL" in resp:
    print(">>> FALHOU — verifique senha / sinal / 2.4GHz (ESP8266 NAO suporta 5GHz)")
else:
    print(">>> Resposta inesperada, veja texto acima")

# 6. Status final
at("AT+CIPSTATUS", 2000, "6. Status da conexao")
at("AT+CIFSR", 2000, "7. IP obtido")
