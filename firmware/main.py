# main.py — Loop principal do Projeto Ultrasonico
# Projeto 2 - Lab de Sistemas Embarcados (FEEC/UNICAMP)
# Plataforma: BitDogLab V7 (RP2040) + ESP8266 + HC-SR04
#
# Funcionalidade:
#   - Mede distancia com sensor ultrasonico HC-SR04
#   - Feedback visual: OLED + NeoPixel 5x5 + LED RGB
#   - Feedback sonoro: buzzer com beep proporcional
#   - Alerta WhatsApp via CallMeBot quando objeto < DISTANCIA_ALERTA_CM

import time
from machine import Pin
from ultrasonico import Ultrasonico
from wifi import WiFi
from buzzer import Buzzer
from feedback import Feedback
from display import Display
from cfg import (
    WIFI_SSID, WIFI_SENHA,
    TELEFONE, APIKEY,
    DISTANCIA_ALERTA_CM, COOLDOWN_ALERTA_SEG,
    INTERVALO_LEITURA_MS,
)

# Inicializacao dos modulos
sensor = Ultrasonico()
wifi = WiFi()
bz = Buzzer()
fb = Feedback()
disp = Display()

btn_c = Pin(10, Pin.IN, Pin.PULL_UP)  # botao verde C: toggle mute do buzzer
_btn_c_anterior = 1

# Tela de boas-vindas
disp.mostrar_inicio()
bz.beep_curto(1000, 150)
time.sleep_ms(1500)

# Conectar Wi-Fi
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

# Estado do alerta
ultimo_alerta = 0  # timestamp do ultimo alerta enviado
alerta_flag = False  # flag visual temporaria

# Loop principal
while True:
    agora = time.ticks_ms()

    # 0. Botao C: toggle mute do buzzer (borda de descida)
    btn_c_atual = btn_c.value()
    if _btn_c_anterior == 1 and btn_c_atual == 0:
        bz.toggle_mute()
    _btn_c_anterior = btn_c_atual

    # 1. Medir distancia
    dist = sensor.medir_cm()

    # 2. Feedback sonoro (beep proporcional)
    bz.beep_proximidade(dist, agora)

    # 3. Feedback visual (NeoPixel + LED RGB)
    fb.atualizar(dist)

    # 4. Verificar alerta WhatsApp
    if (dist >= 0 and dist < DISTANCIA_ALERTA_CM and wifi.conectado):
        tempo_desde_alerta = time.ticks_diff(agora, ultimo_alerta) / 1000
        if tempo_desde_alerta > COOLDOWN_ALERTA_SEG or ultimo_alerta == 0:
            msg = "ALERTA! Objeto detectado a {} cm".format(dist)
            if wifi.enviar_whatsapp(TELEFONE, APIKEY, msg):
                ultimo_alerta = agora
                alerta_flag = True
                bz.beep_curto(2500, 200)

    # 5. Atualizar display OLED
    disp.atualizar(dist, wifi.conectado, alerta_flag)

    # Limpar flag de alerta apos 3 segundos
    if alerta_flag and time.ticks_diff(agora, ultimo_alerta) > 3000:
        alerta_flag = False

    # 6. Intervalo entre leituras
    time.sleep_ms(INTERVALO_LEITURA_MS)
