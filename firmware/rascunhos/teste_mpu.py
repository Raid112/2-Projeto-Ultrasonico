# teste_mpu.py — Driver minimo MPU6050 + leitura continua
# I2C1: SDA=GP2, SCL=GP3. Endereco 0x68 (AD0=GND).

from machine import I2C, Pin
import time
import struct

ADDR = 0x68
PWR_MGMT_1 = 0x6B
ACCEL_XOUT_H = 0x3B   # 14 bytes: ax, ay, az, temp, gx, gy, gz (big-endian signed 16)

# Escalas default (AFS_SEL=0 ±2g, FS_SEL=0 ±250 dps)
ACC_LSB_PER_G = 16384.0
GYRO_LSB_PER_DPS = 131.0

i2c = I2C(1, scl=Pin(3), sda=Pin(2), freq=400000)

# Tira do sleep
i2c.writeto_mem(ADDR, PWR_MGMT_1, b"\x00")
time.sleep_ms(100)

print("MPU6050 OK. Ctrl-C para parar.\n")
print("{:>7} {:>7} {:>7}  {:>7} {:>7} {:>7}  {:>6}".format(
    "ax(g)", "ay(g)", "az(g)", "gx", "gy", "gz", "T(C)"))
print("-" * 60)

try:
    while True:
        raw = i2c.readfrom_mem(ADDR, ACCEL_XOUT_H, 14)
        ax, ay, az, t, gx, gy, gz = struct.unpack(">hhhhhhh", raw)

        ax_g = ax / ACC_LSB_PER_G
        ay_g = ay / ACC_LSB_PER_G
        az_g = az / ACC_LSB_PER_G
        gx_d = gx / GYRO_LSB_PER_DPS
        gy_d = gy / GYRO_LSB_PER_DPS
        gz_d = gz / GYRO_LSB_PER_DPS
        temp_c = t / 340.0 + 36.53

        print("{:>7.2f} {:>7.2f} {:>7.2f}  {:>7.1f} {:>7.1f} {:>7.1f}  {:>6.1f}".format(
            ax_g, ay_g, az_g, gx_d, gy_d, gz_d, temp_c))
        time.sleep_ms(300)
except KeyboardInterrupt:
    print("\nparado.")
