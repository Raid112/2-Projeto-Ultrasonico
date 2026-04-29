# debug_zap.py — Testa envio WhatsApp passo a passo com saida serial detalhada
# mpremote connect COMx run debug_zap.py

from machine import UART, Pin
import time
from cfg import WIFI_SSID, WIFI_SENHA, TELEFONE, APIKEY

SEP = "=" * 44
uart = UART(0, baudrate=19200, tx=Pin(0), rx=Pin(1), timeout=200)


def at(cmd, espera_ms=2000, label=None):
    while uart.any():
        uart.read()
    print("  >> {}".format(cmd))
    uart.write(cmd + "\r\n")
    t0 = time.ticks_ms()
    resp = b""
    while time.ticks_diff(time.ticks_ms(), t0) < espera_ms:
        if uart.any():
            resp += uart.read()
        time.sleep_ms(50)
    txt = resp.decode("utf-8", "ignore")
    print("  << {}".format(repr(txt[:120])))
    return txt


print()
print(SEP)
print("  DEBUG WHATSAPP — CALLMEBOT")
print(SEP)

# 1. Ping
print("\n[1] Ping ESP...")
r = at("AT", 1500)
if "OK" not in r:
    print("  FALHOU — ESP nao responde. Rode debug_esp.py primeiro.")
    raise SystemExit
print("  OK")

# 2. Modo station
print("\n[2] Modo station...")
at("AT+CWMODE=1", 1000)

# 3. Conectar Wi-Fi
print("\n[3] Conectando ao Wi-Fi: {}".format(WIFI_SSID))
r = at('AT+CWJAP="{}","{}"'.format(WIFI_SSID, WIFI_SENHA), 15000)
if "OK" not in r and "GOT IP" not in r:
    print("  FALHOU — checar SSID/senha ou sinal.")
    raise SystemExit
print("  Conectado!")

# 4. Checar IP
print("\n[4] IP obtido:")
at("AT+CIFSR", 2000)

# 5. Desabilitar multiplas conexoes (single mode)
print("\n[5] Single connection mode...")
at("AT+CIPMUX=0", 1000)

# 6. Abrir TCP
HOST = "api.callmebot.com"
print("\n[6] Abrindo TCP para {}:80...".format(HOST))
r = at('AT+CIPSTART="TCP","{}",80'.format(HOST), 6000)
if "ERROR" in r and "ALREADY" not in r:
    print("  FALHOU — sem rota para internet ou DNS falhou.")
    raise SystemExit
print("  TCP aberto!")

# 7. Montar e enviar HTTP GET
msg = "TESTE+DEBUG+EMBARCADOS"
path = "/whatsapp.php?phone={}&text={}&apikey={}".format(TELEFONE, msg, APIKEY)
req = "GET {} HTTP/1.1\r\nHost: {}\r\nConnection: close\r\n\r\n".format(path, HOST)
print("\n[7] Enviando HTTP GET...")
print("  PATH:", path)

r = at("AT+CIPSEND={}".format(len(req)), 1000)
if ">" not in r:
    print("  FALHOU — ESP nao abriu janela de envio ('>').")
    at("AT+CIPCLOSE", 1000)
    raise SystemExit

# Mandar o payload
while uart.any():
    uart.read()
uart.write(req)
time.sleep_ms(6000)
resp = b""
deadline = time.ticks_add(time.ticks_ms(), 3000)
while time.ticks_diff(deadline, time.ticks_ms()) > 0:
    if uart.any():
        resp += uart.read()
        deadline = time.ticks_add(time.ticks_ms(), 500)
txt = resp.decode("utf-8", "ignore")
print("  << RESPOSTA COMPLETA:")
print(txt[:500])

# 8. Resultado
print()
print(SEP)
if "SEND OK" in txt or "+IPD" in txt or "200" in txt or "Message Sent" in txt:
    print("RESULTADO: MENSAGEM ENVIADA com sucesso!")
elif "SEND FAIL" in txt:
    print("RESULTADO: SEND FAIL — TCP caiu antes de enviar.")
elif "403" in txt or "401" in txt:
    print("RESULTADO: HTTP {}  — APIKEY ou telefone invalido.".format(
        "403" if "403" in txt else "401"))
elif "404" in txt:
    print("RESULTADO: HTTP 404 — rota da API errada.")
else:
    print("RESULTADO: Resposta inconclusiva — veja o texto acima.")
print(SEP)

at("AT+CIPCLOSE", 1000)
