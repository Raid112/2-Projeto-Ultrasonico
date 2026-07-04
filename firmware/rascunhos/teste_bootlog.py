# teste_bootlog.py — Captura o boot log do ESP8266 no GP1 (RX do Pico).
# O ESP cospe um log em 74880 baud LOGO APOS o reset/power-on.
# Rode e, durante a janela, faca POWER-CYCLE no ESP (desliga/religa VCC
# ou encosta RST no GND por 1s e solta). Pode repetir varias vezes.
#
# So acumula bytes crus (hex) — sem decode no loop (MicroPython nao suporta
# decode com 'ignore'). Mostra hex ao vivo e tenta texto so no final.

from machine import UART, Pin
import time

BAUD = 74880  # baud do boot ROM do ESP8266
JANELA_S = 35

uart = UART(0, baudrate=BAUD, tx=Pin(0), rx=Pin(1), timeout=200)
time.sleep_ms(100)
while uart.any():
    uart.read()

print("=" * 50)
print(" CAPTURANDO @ {} baud por {}s".format(BAUD, JANELA_S))
print(" >>> AGORA: POWER-CYCLE no ESP (desliga/religa VCC).")
print(" >>> Pode repetir o power-cycle varias vezes.")
print("=" * 50)

t0 = time.ticks_ms()
total = b""
while time.ticks_diff(time.ticks_ms(), t0) < JANELA_S * 1000:
    if uart.any():
        chunk = uart.read()
        if chunk:
            total += chunk
            print("hex:", " ".join("{:02X}".format(b) for b in chunk))
    time.sleep_ms(30)

print("=" * 50)
print("TOTAL recebido:", len(total), "bytes")
if total:
    print("HEX completo:")
    print(" ".join("{:02X}".format(b) for b in total))
    # tenta texto byte-a-byte (so ASCII imprimivel)
    txt = "".join(chr(b) if 32 <= b < 127 else "." for b in total)
    print("ASCII (. = nao imprimivel):")
    print(txt)
    print("-> Recebeu dados = FIACAO OK + ESP VIVO.")
    print("-> Se for lixo, e' baudrate; rode teste_baud.py p/ achar o certo.")
else:
    print("NADA. Confirme que deu power-cycle dentro da janela.")
print("=" * 50)
