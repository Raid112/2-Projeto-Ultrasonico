# imu.py — MPU6050 + detector de queda (free-fall + impacto)
# I2C1: SDA=GP2, SCL=GP3. Endereco 0x68.

from machine import SoftI2C, Pin
import time
import struct

_ADDR = 0x68
_PWR_MGMT_1 = 0x6B
_ACCEL_XOUT_H = 0x3B

_ACC_LSB_PER_G = 16384.0
_GYRO_LSB_PER_DPS = 131.0


class IMU:
    def __init__(self, freefall_g=0.5, freefall_min_ms=80,
                 impact_g=2.2, impact_janela_ms=1000, i2c=None):
        if i2c is None:
            i2c = SoftI2C(scl=Pin(3), sda=Pin(2), freq=100000)
        self.i2c = i2c
        for _ in range(3):
            try:
                self.i2c.writeto_mem(_ADDR, _PWR_MGMT_1, b"\x00")
                break
            except OSError:
                time.sleep_ms(50)
        time.sleep_ms(100)

        self.freefall_g = freefall_g
        self.freefall_min_ms = freefall_min_ms
        self.impact_g = impact_g
        self.impact_janela_ms = impact_janela_ms

        # Estado da maquina: "normal" -> "freefall" -> "aguardando_impacto" -> "normal"
        self._estado = "normal"
        self._t_freefall_inicio = 0
        self._t_freefall_fim = 0
        self.ultima_magnitude = 0.0
        self.freefalls_detectados = 0

    def ler(self):
        """Retorna tupla de 7 floats ou None se leitura I2C falhar."""
        try:
            raw = self.i2c.readfrom_mem(_ADDR, _ACCEL_XOUT_H, 14)
        except OSError:
            return None
        ax, ay, az, t, gx, gy, gz = struct.unpack(">hhhhhhh", raw)
        return (
            ax / _ACC_LSB_PER_G, ay / _ACC_LSB_PER_G, az / _ACC_LSB_PER_G,
            gx / _GYRO_LSB_PER_DPS, gy / _GYRO_LSB_PER_DPS, gz / _GYRO_LSB_PER_DPS,
            t / 340.0 + 36.53,
        )

    def magnitude_accel(self):
        dados = self.ler()
        if dados is None:
            return None
        ax, ay, az, _, _, _, _ = dados
        return (ax * ax + ay * ay + az * az) ** 0.5

    def atualizar_detector(self, agora_ms=None):
        """Maquina de estados para queda. Retorna True uma vez por queda detectada."""
        if agora_ms is None:
            agora_ms = time.ticks_ms()
        mag = self.magnitude_accel()
        if mag is None:
            return False  # leitura falhou, mantem estado anterior
        self.ultima_magnitude = mag

        if self._estado == "normal":
            if mag < self.freefall_g:
                self._estado = "freefall"
                self._t_freefall_inicio = agora_ms
            return False

        if self._estado == "freefall":
            if mag >= self.freefall_g:
                dur = time.ticks_diff(agora_ms, self._t_freefall_inicio)
                if dur >= self.freefall_min_ms:
                    self._estado = "aguardando_impacto"
                    self._t_freefall_fim = agora_ms
                    self.freefalls_detectados += 1
                else:
                    self._estado = "normal"  # freefall muito curto, ignora
            return False

        if self._estado == "aguardando_impacto":
            if mag >= self.impact_g:
                self._estado = "normal"
                return True  # QUEDA CONFIRMADA
            if time.ticks_diff(agora_ms, self._t_freefall_fim) > self.impact_janela_ms:
                self._estado = "normal"  # tempo esgotou sem impacto
            return False

        return False
