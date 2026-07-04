# teste_reset_boot.py — Controla GPIO0 + RST do ESP por software e testa AT.
# LIGACOES NECESSARIAS:
#   RST do ESP   --> GP4 da BitDogLab
#   GPIO0 do ESP --> GP5 da BitDogLab
#   (VCC, CH_PD -> 3V3 da bateria; GND comum; TX->GP1; RX->GP0)
#
# Forca GPIO0=HIGH (boot normal/flash), pulsa RST, le o boot log (deve virar
# boot mode (3,x)), e entao manda AT em 19200 e 115200 esperando "OK".

from machine import UART, Pin
import time

rst = Pin(4, Pin.OUT)
gpio0 = Pin(9, Pin.OUT)   # GPIO0 do ESP ligado no GP9

gpio0.value(1)   # GPIO0 HIGH = boot normal (roda firmware AT)
rst.value(1)     # ESP rodando
time.sleep_ms(50)

def reset_e_le_boot(uart):
    while uart.any():
        uart.read()
    gpio0.value(1)      # garante GPIO0 alto ANTES de soltar o reset
    rst.value(0)
    time.sleep_ms(80)
    rst.value(1)
    t0 = time.ticks_ms()
    total = b""
    while time.ticks_diff(time.ticks_ms(), t0) < 3000:
        if uart.any():
            c = uart.read()
            if c:
                total += c
        time.sleep_ms(5)
    return total

print("=" * 50)
print(" RESET c/ GPIO0=HIGH (GP5) + boot log (74880)")
print("=" * 50)

uart = UART(0, baudrate=74880, tx=Pin(0), rx=Pin(1), timeout=200)
boot = reset_e_le_boot(uart)
if boot:
    txt = "".join(chr(b) if 32 <= b < 127 else "." for b in boot)
    print("boot log:", txt)
    if "(3," in txt:
        print(">>> BOOT MODE (3,x) = NORMAL! Firmware AT vai rodar.")
    elif "(1," in txt:
        print(">>> Ainda (1,x) = GPIO0 baixo. GP5 nao chegou no GPIO0 do ESP.")
else:
    print("boot log vazio")

# Agora testa AT nos bauds do projeto (19200 primeiro, depois 115200)
print("\n" + "=" * 50)
print(" TESTANDO AT (apos boot normal)")
print("=" * 50)

def enviar_at(uart, cmd, espera_ms=1500):
    while uart.any():
        uart.read()
    uart.write(cmd + "\r\n")
    t0 = time.ticks_ms()
    resp = b""
    while time.ticks_diff(time.ticks_ms(), t0) < espera_ms:
        if uart.any():
            resp += uart.read()
        time.sleep_ms(20)
    return resp

for baud in (19200, 115200, 9600, 74880, 38400, 57600):
    u = UART(0, baudrate=baud, tx=Pin(0), rx=Pin(1), timeout=200)
    time.sleep_ms(100)
    r = enviar_at(u, "AT")
    txt = "".join(chr(b) if 32 <= b < 127 else "." for b in r) if r else "(vazio)"
    marca = "  <<< OK!!!" if b"OK" in r else ""
    print("  [{:>6}] {}{}".format(baud, txt[:40], marca))
    if b"OK" in r:
        print("\n>>> ESP RESPONDENDO em {} baud! Use esse no wifi.py.".format(baud))
        print(">>> Versao do firmware:")
        v = enviar_at(u, "AT+GMR", 2000)
        print("   ", "".join(chr(b) if 32 <= b < 127 else "." for b in v)[:200])
        break
    u.deinit()
    time.sleep_ms(50)

print("=" * 50)
