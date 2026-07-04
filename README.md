# Projeto 2 — Sensor de Queda com Alerta WhatsApp

**Lab de Sistemas Embarcados (FEE-246 · FEEC/UNICAMP)**
Plataforma: **BitDogLab V7 (RP2040)** + ESP8266 + HC-SR04 + MPU6050 · MicroPython

---

## O que faz

Dispositivo vestível/de bancada que combina dois papéis:

1. **Sensor de ré sonoro** — o **HC-SR04** mede a distância de um obstáculo e
   aciona três canais de feedback proporcionais à proximidade:
   - **Buzzer** (bip em degraus, ~400 Hz → 1 kHz — quanto mais perto, mais agudo e frequente);
   - **Motor vibratório** (canal háptico análogo ao som, cadência que acelera com a proximidade);
   - **LED RGB / matriz NeoPixel** (cor por faixa de distância).
2. **Detector de queda** — o **MPU6050** identifica queda livre (`freefall`) e,
   ao detectar, dispara um **alerta de WhatsApp** via ESP8266 + [CallMeBot](https://www.callmebot.com/).

O **botão C** muta/desmuta o buzzer e a vibração ao mesmo tempo.

---

## Estrutura

```
firmware/
├── main.py          # loop principal (orquestra tudo)
├── cfg.py           # configuração: WiFi, CallMeBot, thresholds, timings
├── ultrasonico.py   # driver HC-SR04 (medição por eco, com timeout)
├── imu.py           # driver MPU6050 + detector de queda livre
├── wifi.py          # ESP8266 via AT (UART) + envio CallMeBot
├── buzzer.py        # buzzer PWM (bip por proximidade, em degraus)
├── vibra.py         # motor vibratório ERM (PWM proporcional à distância)
├── feedback.py      # LED RGB + matriz NeoPixel 5×5
├── display.py       # OLED SSD1306 (opcional)
├── debug_esp.py     # varredura de fiação/baud do ESP8266
├── debug_zap.py     # teste isolado de envio WhatsApp
└── rascunhos/       # scripts de teste arquivados (por periférico)

hardware.md          # pinagem completa, conectores V7 e fiação
Relatorio/           # relatório LaTeX da disciplina (não versionado)
```

---

## Ligações (resumo)

Pinagem completa, conectores V7 e avisos de fiação em **[`hardware.md`](hardware.md)**.

| Periférico          | GPIO / Conector          | Módulo          |
|---------------------|--------------------------|-----------------|
| HC-SR04 TRIG/ECHO   | GP8 / GP9 (IDC 14p)      | `ultrasonico.py`|
| MPU6050 (I2C1)      | GP2/GP3 · J5 · `0x68`    | `imu.py`        |
| ESP8266 (UART0)     | GP0/GP1 · J6 · 19200 bd  | `wifi.py`       |
| Buzzer A (PWM)      | GP21                     | `buzzer.py`     |
| Motor vibratório    | GP14 → driver (transistor)| `vibra.py`     |
| NeoPixel 5×5        | GP7                      | `feedback.py`   |
| LED RGB (R/G/B)     | GP13 / GP11 / GP12       | `feedback.py`   |
| OLED SSD1306        | GP2/GP3 · I2C1 · `0x3C`  | `display.py`    |
| Botão C (mute)      | GP10 (pull-up)           | `main.py`       |

> ⚠️ O ECHO do HC-SR04 sai em 5 V — usar divisor de tensão (ex.: 1k+2k) para o
> GP9 (3.3 V). ⚠️ O motor vibratório **não** liga direto no GPIO: precisa de um
> circuito driver (transistor) no GP14, pois excede a corrente segura do pino.

---

## Configuração

Antes de usar, edite **`firmware/cfg.py`**:

- `WIFI_SSID` / `WIFI_SENHA` — rede à qual o ESP8266 se conecta.
- `TELEFONE` / `APIKEY` — obtidos no CallMeBot:
  1. adicione **+34 644 71 98 32** aos contatos;
  2. envie `I allow callmebot to send me messages`;
  3. você recebe a `apikey` por mensagem.
- Escala do sensor (`DISTANCIA_MAX_CM`, `DISTANCIA_ALERTA_CM`), thresholds de
  queda (`FREEFALL_G`) e timings do loop também ficam aqui.

## Como rodar

Com a BitDogLab conectada por USB, suba o conteúdo de `firmware/` e reinicie:

```bash
mpremote connect auto fs cp firmware/*.py :
mpremote connect auto reset
```

> Sempre reinicie a placa após o upload — senão o `main.py` novo não roda.

---

## Notas de projeto

- **Loop responsivo:** OLED e matriz NeoPixel podem ser desligados por toggle
  hardcoded no topo do `main.py` (`USAR_OLED` / `USAR_MATRIZ`). O redesenho do
  OLED via SoftI2C custa ~113 ms e travaria o loop de controle.
- **Distância filtrada** por mediana móvel (rejeita spikes do HC-SR04 sem o
  lag de uma janela temporal).
- **WhatsApp:** o envio AT lê a resposta de forma incremental e sai assim que
  vê o token esperado (`OK`, `>`, `CLOSED`…) em vez de esperar o timeout inteiro.
  O código `209` da CallMeBot (rate-limit) **não** conta como envio bem-sucedido.
