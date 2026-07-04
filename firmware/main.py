# main.py — Loop principal
# Projeto 2 - Lab de Sistemas Embarcados (FEEC/UNICAMP)
# Plataforma: BitDogLab V7 (RP2040) + ESP8266 + HC-SR04 + MPU6050
#
# Funcionalidade:
#   - HC-SR04 controla APENAS o buzzer (sensor de re sonoro)
#   - MPU6050 detecta queda real (freefall + impacto) -> envia WhatsApp
#   - Feedback visual (NeoPixel + LED RGB) reflete estado de queda
#   - Botao C muta/desmuta o buzzer

import time
from machine import Pin, SoftI2C
from ultrasonico import Ultrasonico
from wifi import WiFi
from buzzer import Buzzer
from vibra import Vibra
from feedback import Feedback
from display import Display
from imu import IMU
from cfg import (
    WIFI_SSID, WIFI_SENHA,
    TELEFONE, APIKEY,
    DISTANCIA_MAX_CM, DISTANCIA_ALERTA_CM, COOLDOWN_ALERTA_SEG,
    INTERVALO_LEITURA_MS, MEDIANA_N, ECHO_TIMEOUT_US, DISPLAY_INTERVALO_MS,
    FREEFALL_G, FREEFALL_MIN_MS, IMPACT_G, IMPACT_JANELA_MS,
    MODO_DEBUG, DEBUG_RESET_MIN_MAX_SEG,
)

# ===== Toggle de perifericos (hardcoded) =====
# OLED: False = nao usa o display. Loop mais rapido (sem o ~113ms do SoftI2C
# por redesenho). Buzzer, vibra, LED e WhatsApp continuam normais.
USAR_OLED = False
# Matriz NeoPixel 5x5: False = apaga e nao escreve nela. O LED RGB continua.
USAR_MATRIZ = False

i2c_bus = SoftI2C(scl=Pin(3), sda=Pin(2), freq=100000)

sensor = Ultrasonico(echo_timeout_us=ECHO_TIMEOUT_US)
wifi = WiFi()
bz = Buzzer(dist_max=DISTANCIA_MAX_CM, dist_alerta=DISTANCIA_ALERTA_CM)
vb = Vibra(dist_max=DISTANCIA_MAX_CM, dist_alerta=DISTANCIA_ALERTA_CM)
fb = Feedback(dist_max=DISTANCIA_MAX_CM, dist_alerta=DISTANCIA_ALERTA_CM,
              usar_matriz=USAR_MATRIZ)
class _DisplayNulo:
    """Stub usado quando USAR_OLED=False: todos os metodos viram no-op."""
    def mostrar_inicio(self): pass
    def mostrar_wifi(self, *a): pass
    def mostrar_erro(self, *a): pass
    def atualizar(self, *a): pass
    def mostrar_debug(self, *a): pass


disp = Display(i2c=i2c_bus) if USAR_OLED else _DisplayNulo()
imu = IMU(freefall_g=FREEFALL_G, freefall_min_ms=FREEFALL_MIN_MS,
          impact_g=IMPACT_G, impact_janela_ms=IMPACT_JANELA_MS, i2c=i2c_bus)

btn_c = Pin(10, Pin.IN, Pin.PULL_UP)
_btn_c_anterior = 1

disp.mostrar_inicio()
bz.beep_curto(1000, 150)
time.sleep_ms(1500)

disp.mostrar_wifi("Buscando ESP...")
if not wifi.iniciar():
    disp.mostrar_erro("ESP nao responde", "Checar cabos", "TX/RX GP0-GP1")
    time.sleep_ms(3000)
else:
    disp.mostrar_wifi("Conectando WiFi...")
    if wifi.conectar(WIFI_SSID, WIFI_SENHA):
        disp.mostrar_wifi("WiFi conectado!")
        bz.beep_curto(1500, 100)
        time.sleep_ms(500)
        bz.beep_curto(2000, 100)
    else:
        disp.mostrar_erro("Falha no WiFi", WIFI_SSID, "Checar roteador")
    time.sleep_ms(3000)

ultimo_alerta = 0
alerta_flag = False

# Debug: min/max de magnitude por janela de DEBUG_INTERVALO_SEG
_dbg_inicio = time.ticks_ms()
_dbg_min = 99.0
_dbg_max = 0.0
_dbg_freefalls_ultimo = 0

# Distancia filtrada por mediana movel (atualiza a cada loop, sem lag de janela)
dist = -1
_ultimas = []
_ultimo_display = 0

while True:
    agora = time.ticks_ms()

    # 0. Botao C: toggle mute do buzzer + vibracao
    btn_c_atual = btn_c.value()
    if _btn_c_anterior == 1 and btn_c_atual == 0:
        bz.toggle_mute()
        vb.toggle_mute()
    _btn_c_anterior = btn_c_atual

    # 1. Amostrar ultrasonico -> mediana movel de MEDIANA_N amostras.
    #    Atualiza dist a cada loop (sem o lag de uma janela de tempo), mas a
    #    mediana ainda rejeita os spikes ocasionais do HC-SR04.
    amostra = sensor.medir_cm()
    if amostra < 0:
        _ultimas = []
        dist = -1
    else:
        _ultimas.append(amostra)
        if len(_ultimas) > MEDIANA_N:
            _ultimas.pop(0)
        dist = sorted(_ultimas)[len(_ultimas) // 2]

    # 2. Buzzer + motor vibratorio reagem a distancia (papel do ultrasonico)
    bz.beep_proximidade(dist, agora)
    vb.vibrar_proximidade(dist, agora)

    # 3. IMU: detectar queda (roda a cada iteracao, ~50ms)
    queda = imu.atualizar_detector(agora)
    mag = imu.ultima_magnitude
    if mag < _dbg_min:
        _dbg_min = mag
    if mag > _dbg_max:
        _dbg_max = mag

    if queda and wifi.conectado:
        tempo_desde_alerta = time.ticks_diff(agora, ultimo_alerta) / 1000
        if tempo_desde_alerta > COOLDOWN_ALERTA_SEG or ultimo_alerta == 0:
            msg = "ALERTA! Queda detectada"
            if wifi.enviar_whatsapp(TELEFONE, APIKEY, msg):
                ultimo_alerta = agora
                alerta_flag = True
                bz.beep_curto(2500, 200)
                vb.pulso_curto(200)

    # 3b. Modo debug: resetar janela de min/max periodicamente
    if MODO_DEBUG and time.ticks_diff(agora, _dbg_inicio) >= DEBUG_RESET_MIN_MAX_SEG * 1000:
        _dbg_min = 99.0
        _dbg_max = 0.0
        _dbg_inicio = agora

    # 4. Feedback visual: vermelho piscante durante alerta_flag, distancia caso contrario
    if alerta_flag:
        fb.atualizar(0)  # forca faixa "critica" -> vermelho
    else:
        fb.atualizar(dist)

    # 5. Display OLED — throttled. O show() via SoftI2C custa ~113ms; se rodar
    #    todo loop trava buzzer/vibra/sensor. Atualiza a cada DISPLAY_INTERVALO_MS.
    if time.ticks_diff(agora, _ultimo_display) >= DISPLAY_INTERVALO_MS:
        _ultimo_display = agora
        if MODO_DEBUG:
            disp.mostrar_debug(mag, _dbg_min, _dbg_max,
                               imu.freefalls_detectados, imu._estado)
        else:
            disp.atualizar(dist, wifi.conectado, alerta_flag)

    # Limpar flag visual apos 3s
    if alerta_flag and time.ticks_diff(agora, ultimo_alerta) > 3000:
        alerta_flag = False

    time.sleep_ms(INTERVALO_LEITURA_MS)
