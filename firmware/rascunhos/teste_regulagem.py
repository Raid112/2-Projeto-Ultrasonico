# teste_regulagem.py — Calibracao e diagnostico do HC-SR04
# Coleta N leituras, imprime min/max/media/desvio/taxa de timeout.
# Use para:
#   1. Achar a "zona morta" (< ~2cm retorna -1 ou valores malucos)
#   2. Verificar ruido (desvio padrao) a uma distancia fixa
#   3. Ajustar DISTANCIA_ALERTA_CM com folga sobre o ruido

from machine import Pin, time_pulse_us
import time

TRIG_PIN = 8
ECHO_PIN = 9
N_AMOSTRAS = 30        # leituras por janela
INTERVALO_MS = 60      # entre leituras (>=50ms recomendado p/ HC-SR04)
JANELAS = 0            # 0 = infinito, >0 = quantas janelas de N amostras rodar

trig = Pin(TRIG_PIN, Pin.OUT)
echo = Pin(ECHO_PIN, Pin.IN)
trig.value(0)


def medir_us():
    trig.value(0)
    time.sleep_us(2)
    trig.value(1)
    time.sleep_us(10)
    trig.value(0)
    return time_pulse_us(echo, 1, 30000)


def us_para_cm(us):
    if us < 0:
        return -1
    return (us / 2.0) / 29.15


def stats(amostras):
    validas = [a for a in amostras if a >= 0]
    if not validas:
        return None
    mn = min(validas)
    mx = max(validas)
    media = sum(validas) / len(validas)
    var = sum((a - media) ** 2 for a in validas) / len(validas)
    dp = var ** 0.5
    timeouts = len(amostras) - len(validas)
    return mn, mx, media, dp, timeouts


print("=== Calibracao HC-SR04 ===")
print("Coloque um alvo fixo a uma distancia conhecida.")
print("Ctrl-C para parar.\n")
print("{:>4} {:>7} {:>7} {:>7} {:>7} {:>4}".format(
    "jan", "min", "max", "med", "dp", "TO"))
print("-" * 40)

janela = 0
try:
    while True:
        amostras = []
        for _ in range(N_AMOSTRAS):
            amostras.append(us_para_cm(medir_us()))
            time.sleep_ms(INTERVALO_MS)

        s = stats(amostras)
        janela += 1
        if s is None:
            print("{:>4} {:>7} {:>7} {:>7} {:>7} {:>4}".format(
                janela, "--", "--", "--", "--", N_AMOSTRAS))
        else:
            mn, mx, med, dp, to = s
            print("{:>4} {:>7.1f} {:>7.1f} {:>7.1f} {:>7.2f} {:>4}".format(
                janela, mn, mx, med, dp, to))

        if JANELAS and janela >= JANELAS:
            break
except KeyboardInterrupt:
    print("\nparado.")
