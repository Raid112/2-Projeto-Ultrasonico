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
from feedback import Feedback
from display import Display
from imu import IMU
from cfg import (
    WIFI_SSID, WIFI_SENHA,
    TELEFONE, APIKEY,
    DISTANCIA_MAX_CM, DISTANCIA_ALERTA_CM, COOLDOWN_ALERTA_SEG,
    INTERVALO_LEITURA_MS, JANELA_MEDIA_MS,
    FREEFALL_G, FREEFALL_MIN_MS, IMPACT_G, IMPACT_JANELA_MS,
    MODO_DEBUG, DEBUG_RESET_MIN_MAX_SEG,
)

i2c_bus = SoftI2C(scl=Pin(3), sda=Pin(2), freq=100000)

sensor = Ultrasonico()
wifi = WiFi()
bz = Buzzer(dist_max=DISTANCIA_MAX_CM, dist_alerta=DISTANCIA_ALERTA_CM)
fb = Feedback(dist_max=DISTANCIA_MAX_CM, dist_alerta=DISTANCIA_ALERTA_CM)
disp = Display(i2c=i2c_bus)
imu = IMU(freefall_g=FREEFALL_G, freefall_min_ms=FREEFALL_MIN_MS,
          impact_g=IMPACT_G, impact_janela_ms=IMPACT_JANELA_MS, i2c=i2c_bus)

btn_c = Pin(10, Pin.IN, Pin.PULL_UP)
_btn_c_anterior = 1

disp.mostrar_inicio()
bz.beep_curto(1000, 150)
time.sleep_ms(1500)

disp.mostrar_wifi("Buscando ESP...")
if not wifi.iniciar():
    disp.mostrar_wifi("ESP nao encontrado")
    time.sleep_ms(2000)
else:
    disp.mostrar_wifi("Conectando WiFi...")
    if wifi.conectar(WIFI_SSID, WIFI_SENHA):
        disp.mostrar_wifi("WiFi conectado!")
        bz.beep_curto(1500, 100)
        time.sleep_ms(500)
        bz.beep_curto(2000, 100)
    else:
        disp.mostrar_wifi("Falha no WiFi")
    time.sleep_ms(1500)

ultimo_alerta = 0
alerta_flag = False

# Debug: min/max de magnitude por janela de DEBUG_INTERVALO_SEG
_dbg_inicio = time.ticks_ms()
_dbg_min = 99.0
_dbg_max = 0.0
_dbg_freefalls_ultimo = 0

# Janela de media do ultrasonico (so alimenta o buzzer)
dist = -1
_buffer_amostras = []
_inicio_janela = time.ticks_ms()

while True:
    agora = time.ticks_ms()

    # 0. Botao C: toggle mute do buzzer
    btn_c_atual = btn_c.value()
    if _btn_c_anterior == 1 and btn_c_atual == 0:
        bz.toggle_mute()
    _btn_c_anterior = btn_c_atual

    # 1. Amostrar ultrasonico e fechar janela de media a cada JANELA_MEDIA_MS
    amostra = sensor.medir_cm()
    if amostra >= 0:
        _buffer_amostras.append(amostra)

    if time.ticks_diff(agora, _inicio_janela) >= JANELA_MEDIA_MS:
        if _buffer_amostras:
            _buffer_amostras.sort()
            dist = _buffer_amostras[len(_buffer_amostras) // 2]
        else:
            dist = -1
        _buffer_amostras = []
        _inicio_janela = agora

    # 2. Buzzer reage a distancia (unico papel do ultrasonico)
    bz.beep_proximidade(dist, agora)

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

    # 5. Display OLED (debug ou modo normal)
    if MODO_DEBUG:
        disp.mostrar_debug(mag, _dbg_min, _dbg_max,
                           imu.freefalls_detectados, imu._estado)
    else:
        disp.atualizar(dist, wifi.conectado, alerta_flag)

    # Limpar flag visual apos 3s
    if alerta_flag and time.ticks_diff(agora, ultimo_alerta) > 3000:
        alerta_flag = False

    time.sleep_ms(INTERVALO_LEITURA_MS)
