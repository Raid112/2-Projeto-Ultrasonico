# config.py — Configuracoes do projeto
# Projeto 2 - Lab de Sistemas Embarcados (FEEC/UNICAMP)
#
# IMPORTANTE: Edite os valores abaixo antes de usar!

# Wi-Fi
WIFI_SSID = "Caio-Rede‐--------------------"
WIFI_SENHA = "87654321"

# CallMeBot WhatsApp
# Para obter a apikey:
# 1. Adicione +34 644 71 98 32 nos contatos do WhatsApp
# 2. Envie "I allow callmebot to send me messages" para esse numero
# 3. Voce recebera a apikey por mensagem
TELEFONE = "5519971600151"
APIKEY = "9984181"

# Sensor
DISTANCIA_ALERTA_CM = 20     # distancia que dispara o alerta WhatsApp
COOLDOWN_ALERTA_SEG = 30     # tempo minimo entre alertas (evitar spam)

# Loop principal
INTERVALO_LEITURA_MS = 50    # intervalo entre leituras do sensor
