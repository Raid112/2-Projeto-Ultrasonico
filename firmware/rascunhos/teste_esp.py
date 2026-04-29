# teste_esp.py — Testa comunicacao com ESP8266 em varios baudrates
from machine import UART, Pin
import time

BAUDRATES = [9600, 19200, 38400, 57600, 115200, 74880]

for baud in BAUDRATES:
    print("--- Testando baudrate:", baud, "---")
    uart = UART(0, baudrate=baud, tx=Pin(0), rx=Pin(1))
    time.sleep_ms(100)

    # Limpar buffer
    while uart.any():
        uart.read()

    uart.write(b"AT\r\n")
    time.sleep_ms(1500)

    resp = b""
    while uart.any():
        resp += uart.read()

    print("Bytes:", resp)

    try:
        texto = resp.decode("utf-8")
        print("Texto:", repr(texto))
        if "OK" in texto:
            print(">>> ENCONTRADO! Baudrate correto:", baud)
            break
    except:
        print("(resposta nao-UTF8, baudrate provavelmente errado)")
else:
    print(">>> Nenhum baudrate retornou OK.")
