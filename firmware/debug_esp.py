# debug_esp.py — Diagnostico hardware do ESP8266
# Roda via: mpremote connect COMx run debug_esp.py
# Foca em problemas fisicos: baudrate, TX/RX invertido, alimentacao, boot mode

from machine import UART, Pin
import time

SEP = "=" * 44

# Baudrates comuns do ESP8266 (74880 e' o boot log)
BAUDRATES = [74880, 115200, 9600, 19200, 38400, 57600]

# -----------------------------------------------------------------
# UART0: TX=GP0, RX=GP1  (ligacao padrao do projeto)
# UART0: TX=GP1, RX=GP0  (TX/RX invertido — erro comum de montagem)
# -----------------------------------------------------------------
CONFIGS = [
    {"id": 0, "tx": 0, "rx": 1, "label": "UART0  TX=GP0 RX=GP1 (padrao)"},
    {"id": 0, "tx": 1, "rx": 0, "label": "UART0  TX=GP1 RX=GP0 (invertido)"},
    {"id": 1, "tx": 4, "rx": 5, "label": "UART1  TX=GP4 RX=GP5 (alternativo)"},
]


def raw_hex(data):
    return " ".join("{:02X}".format(b) for b in data)


def enviar_at(uart, cmd, espera_ms=1200):
    while uart.any():
        uart.read()
    uart.write(cmd + "\r\n")
    time.sleep_ms(espera_ms)
    resp = b""
    deadline = time.ticks_add(time.ticks_ms(), 300)
    while time.ticks_diff(deadline, time.ticks_ms()) > 0:
        if uart.any():
            resp += uart.read()
            deadline = time.ticks_add(time.ticks_ms(), 100)
    return resp


def analisar(resp):
    """Classifica a resposta: OK, lixo (baudrate errado), silencio."""
    if not resp:
        return "SILENCIO — sem bytes. ESP desligado, pino errado ou TX/RX ambos desconectados."
    try:
        txt = resp.decode("utf-8")
        if "OK" in txt:
            return "OK — ESP respondeu corretamente!"
        if "ERROR" in txt:
            return "ERROR — ESP vivo mas comando rejeitado (ok, e' comunicacao)."
        if "ready" in txt.lower() or "AT" in txt:
            return "PARCIAL — ESP vivo, possivel ruido ou eco."
        return "TEXTO ESTRANHO — ESP vivo mas resposta inesperada: " + repr(txt[:60])
    except Exception:
        return "LIXO (bytes nao-UTF8) — baudrate provavelmente errado."


print()
print(SEP)
print("  DEBUG HARDWARE ESP8266")
print(SEP)
print()

# ---------- AVISO VISUAL DE HARDWARE ----------
print("CHECKLIST ANTES DE COMECAR:")
print("  [ ] ESP8266 alimentado em 3.3V (NAO 5V)")
print("  [ ] GPIO0 do ESP solto ou em HIGH (nao em GND/flash mode)")
print("  [ ] CH_PD/EN do ESP ligado em 3.3V")
print("  [ ] Cabo USB nao e' so de carga (precisa de dados)")
print()
print("Iniciando testes em 2s...")
time.sleep_ms(2000)

encontrado = False

for cfg in CONFIGS:
    print()
    print(SEP)
    print("CONFIG:", cfg["label"])
    print(SEP)

    for baud in BAUDRATES:
        try:
            uart = UART(cfg["id"], baudrate=baud,
                        tx=Pin(cfg["tx"]), rx=Pin(cfg["rx"]),
                        timeout=200)
        except Exception as e:
            print("  [{}] ERRO ao abrir UART: {}".format(baud, e))
            continue

        time.sleep_ms(80)
        resp = enviar_at(uart, "AT")

        status = analisar(resp)
        hex_str = raw_hex(resp) if resp else "(vazio)"

        print("  [{:>6}] {} | hex: {}".format(baud, status, hex_str[:60]))

        if "OK" in status or "ERROR" in status or "PARCIAL" in status or "ESTRANHO" in status:
            print()
            print("  >>> COMUNICACAO DETECTADA! Baudrate:", baud)
            print("  >>> Config:", cfg["label"])
            print()
            print("  Testando mais comandos AT...")
            r = enviar_at(uart, "AT+GMR", 2000)
            print("  AT+GMR (versao firmware):", repr(r.decode("utf-8", "ignore")[:80]))
            r = enviar_at(uart, "AT+CWMODE?", 1500)
            print("  AT+CWMODE? (modo wifi):  ", repr(r.decode("utf-8", "ignore")[:60]))
            encontrado = True
            break

        uart.deinit()
        time.sleep_ms(50)

    if encontrado:
        break

print()
print(SEP)
if encontrado:
    print("RESULTADO: ESP8266 encontrado e respondendo.")
    print("Use o baudrate e config acima no wifi.py / cfg.")
else:
    print("RESULTADO: ESP8266 NAO respondeu em nenhuma config.")
    print()
    print("Provaveis causas:")
    print("  1. ESP nao alimentado — checar 3.3V no VCC e CH_PD/EN")
    print("  2. GPIO0 em GND — ESP travado em flash mode (soltar o pino)")
    print("  3. Todos os 4 fios desconectados (TX, RX, VCC, GND)")
    print("  4. Firmware AT apagado — precisa reflashear o ESP")
    print("  5. ESP queimado (alimentado com 5V anteriormente)")
print(SEP)
