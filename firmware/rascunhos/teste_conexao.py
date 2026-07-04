# teste_conexao.py — Check rapido de fiacao: MPU6050 (J5/I2C1) + ESP8266 (J6/UART0)
# Roda no Thonny. Confirma se os DOIS modulos recem-ligados respondem.
# Nao conecta no WiFi nem interpreta movimento — so verifica presenca/comunicacao.

from machine import I2C, Pin, UART
import time
import struct

print("=" * 50)
print(" CHECK DE FIACAO — MPU6050 + ESP8266")
print("=" * 50)

# ---------------------------------------------------------------
# 1. MPU6050 no I2C1 (GP2=SDA, GP3=SCL) — conector J5
# ---------------------------------------------------------------
print("\n[1] MPU6050 no barramento I2C1 (J5)...")
mpu_ok = False
try:
    i2c = I2C(1, scl=Pin(3), sda=Pin(2), freq=100000)
    enderecos = i2c.scan()
    print("    Dispositivos I2C1 encontrados:", [hex(a) for a in enderecos])

    if 0x68 in enderecos or 0x69 in enderecos:
        addr = 0x68 if 0x68 in enderecos else 0x69
        # WHO_AM_I deve retornar 0x68
        who = i2c.readfrom_mem(addr, 0x75, 1)[0]
        # Tira do sleep e le uma amostra
        i2c.writeto_mem(addr, 0x6B, b"\x00")
        time.sleep_ms(100)
        raw = i2c.readfrom_mem(addr, 0x3B, 14)
        ax, ay, az, t, gx, gy, gz = struct.unpack(">hhhhhhh", raw)
        print("    OK! MPU em {} | WHO_AM_I={}".format(hex(addr), hex(who)))
        print("    Accel (g): ax={:.2f} ay={:.2f} az={:.2f}".format(
            ax / 16384, ay / 16384, az / 16384))
        print("    (parado, um eixo deve ler ~1.0 g)")
        mpu_ok = True
    else:
        print("    >>> MPU NAO encontrado (esperado 0x68).")
        print("    >>> Cheque: VCC=3V3, GND, SDA=GP2, SCL=GP3.")
        print("    >>> Se OLED/INA aparecem mas MPU nao -> SDA/SCL trocados no fio.")
except Exception as e:
    print("    >>> ERRO no I2C1:", e)

# ---------------------------------------------------------------
# 2. ESP8266 na UART0 (GP0=TX, GP1=RX) — conector J6
# ---------------------------------------------------------------
print("\n[2] ESP8266 na UART0 (J6) @ 19200 baud...")
esp_ok = False
try:
    uart = UART(0, baudrate=19200, tx=Pin(0), rx=Pin(1))
    time.sleep_ms(200)
    while uart.any():
        uart.read()
    uart.write("AT\r\n")
    t0 = time.ticks_ms()
    resp = b""
    while time.ticks_diff(time.ticks_ms(), t0) < 2000:
        if uart.any():
            resp += uart.read()
        time.sleep_ms(50)
    texto = resp.decode("utf-8", "ignore")
    print("    Resposta ao 'AT':", repr(texto.strip()) if texto.strip() else "(vazio)")
    if "OK" in texto:
        print("    OK! ESP8266 respondeu.")
        esp_ok = True
    else:
        print("    >>> ESP nao respondeu 'OK'.")
        print("    >>> Cheque TX/RX: ESP-RX no GP0, ESP-TX no GP1 (cruzado!).")
        print("    >>> Se nada vier, rode debug_esp.py (varre GP0/GP1, invertido, UART1).")
except Exception as e:
    print("    >>> ERRO na UART0:", e)

# ---------------------------------------------------------------
# 3. Veredito
# ---------------------------------------------------------------
print("\n" + "=" * 50)
print(" RESULTADO")
print("=" * 50)
print("  MPU6050 (J5/I2C1):", "OK" if mpu_ok else "FALHOU")
print("  ESP8266  (J6/UART0):", "OK" if esp_ok else "FALHOU")
if mpu_ok and esp_ok:
    print("\n  Tudo conectado! Pode rodar o main.py.")
else:
    print("\n  Corrija a fiacao acima antes de rodar o main.py.")
