# config.py — Configuracoes do projeto
# Projeto 2 - Lab de Sistemas Embarcados (FEEC/UNICAMP)
#
# IMPORTANTE: Edite os valores abaixo antes de usar!

# Wi-Fi
WIFI_SSID = "Caio-Rede"
WIFI_SENHA = "87654321"

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
JANELA_MEDIA_MS = 3000       # janela de tempo para media da distancia

# Deteccao de queda (MPU6050)
# Algoritmo: queda livre (accel baixo) seguida de impacto (accel alto) dentro de uma janela.
FREEFALL_G = 0.8             # magnitude de accel abaixo disso = queda livre
FREEFALL_MIN_MS = 0          # sem criterio de tempo minimo
IMPACT_G = 99.0              # sem criterio de impacto (nao usado)
IMPACT_JANELA_MS = 1000      # nao usado

# Modo debug: substitui OLED por tela com magnitude/min/max/freefalls
# para calibrar thresholds de queda. Nao usa WhatsApp.
MODO_DEBUG = True
DEBUG_RESET_MIN_MAX_SEG = 10   # periodicamente reseta min/max para ver janelas recentes

# Loop principal
INTERVALO_LEITURA_MS = 50    # intervalo entre leituras do sensor
