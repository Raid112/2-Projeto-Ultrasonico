# config.py — Configuracoes do projeto
# Projeto Final - Bengala Assistiva - Lab de Sistemas Embarcados (FEEC/UNICAMP)
#
# IMPORTANTE: Edite os valores abaixo antes de usar!

# Wi-Fi
WIFI_SSID = "BitDog"
WIFI_SENHA = "12345678"

# CallMeBot WhatsApp
# Para obter a apikey:
# 1. Adicione +34 644 71 98 32 nos contatos do WhatsApp
# 2. Envie "I allow callmebot to send me messages" para esse numero
# 3. Voce recebera a apikey por mensagem
TELEFONE = "5519971600151"
APIKEY = "9984181"

# Sensor
# Escala da aplicacao (ajustar conforme ambiente)
# Modo mesa:      MAX=30, ALERTA=5
# Modo vida real: MAX=200, ALERTA=30 (por exemplo)
DISTANCIA_MAX_CM = 30        # distancia maxima considerada (acima disso = sem objeto)
DISTANCIA_ALERTA_CM = 5      # distancia critica (so afeta o buzzer)

COOLDOWN_ALERTA_SEG = 10     # tempo minimo entre alertas WhatsApp (CallMeBot ~1 msg / 10s)

# Filtro de distancia: mediana movel das ultimas N amostras. Atualiza a cada
# loop (sem o lag de uma janela de tempo) mas ainda rejeita spikes do HC-SR04.
MEDIANA_N = 3
# Timeout do echo do HC-SR04 (us). Menor = menos bloqueio quando nao ha objeto.
# ~18000us ~= 300cm de alcance maximo de deteccao.
ECHO_TIMEOUT_US = 18000

# Deteccao de queda (MPU6050)
# Algoritmo: queda livre (accel baixo) seguida de impacto (accel alto) dentro de uma janela.
FREEFALL_G = 0.8             # magnitude de accel abaixo disso = queda livre
FREEFALL_MIN_MS = 0          # sem criterio de tempo minimo
IMPACT_G = 99.0              # sem criterio de impacto (nao usado)
IMPACT_JANELA_MS = 1000      # nao usado

# Modo debug: substitui OLED por tela com magnitude/min/max/freefalls
# para calibrar thresholds de queda. Nao usa WhatsApp.
MODO_DEBUG = False
DEBUG_RESET_MIN_MAX_SEG = 10   # periodicamente reseta min/max para ver janelas recentes

# Loop principal
# 0 = sem pausa extra (loop o mais rapido possivel). Na pratica o proprio
# HC-SR04 ja bloqueia ~5-18ms por medicao (tempo do echo), que e' o piso
# natural do loop -> nao gira infinito nem trava.
INTERVALO_LEITURA_MS = 0
# OLED via SoftI2C custa ~113ms por redesenho; atualiza no maximo a cada
# DISPLAY_INTERVALO_MS pra nao travar o loop de controle (buzzer/vibra/sensor).
DISPLAY_INTERVALO_MS = 250
