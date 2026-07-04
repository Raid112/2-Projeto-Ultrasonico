# Projeto Final — Bengala Assistiva

**Lab de Sistemas Embarcados (FEE-246 · FEEC/UNICAMP)**
Plataforma: **BitDogLab V7 (RP2040)** + ESP8266 + HC-SR04 + MPU6050 · **MicroPython**

Bengala eletrônica de apoio para pessoas com deficiência visual. O sensor
ultrassônico detecta obstáculos à frente e comunica a proximidade por **som e
vibração** (quanto mais perto, mais intenso). Em paralelo, um acelerômetro
detecta **queda** do usuário e dispara um **alerta de emergência via WhatsApp**.

---

## Sumário

- [Visão geral](#visão-geral)
- [Raiz do projeto](#raiz-do-projeto)
- [Arquitetura de software](#arquitetura-de-software)
- [O orquestrador (`main.py`)](#o-orquestrador-mainpy)
- [Rotinas principais (com código)](#rotinas-principais-com-código)
- [Configuração](#configuração)
- [Como rodar](#como-rodar)
- [Hardware](#hardware)

---

## Visão geral

A bengala tem **dois subsistemas independentes** que rodam no mesmo loop:

| Subsistema | Sensor | Ação |
|------------|--------|------|
| **Detecção de obstáculo** | HC-SR04 (ultrassom) | Buzzer + motor vibratório + LED, proporcionais à distância |
| **Detecção de queda** | MPU6050 (IMU) | Envia WhatsApp de emergência (ESP8266 + CallMeBot) |

Princípios de design do firmware:

- **Módulos desacoplados** — cada periférico é uma classe (`Ultrasonico`, `Buzzer`,
  `Vibra`, `IMU`, `WiFi`, `Feedback`, `Display`). O `main.py` só orquestra.
- **Loop não-bloqueante** — nenhuma rotina do loop dorme; buzzer/vibra decidem
  ligar/desligar por *timestamp* (`time.ticks_ms()`), não por `sleep`. O único
  bloqueio é o próprio eco do HC-SR04 (~5–18 ms), que vira o piso natural do loop.
- **Periféricos lentos são *throttled* ou desligáveis** — o OLED (SoftI2C, ~113 ms
  por redesenho) e a matriz NeoPixel podem ser cortados por toggle no topo do
  `main.py` para não travar o controle de tempo-real.

---

## Raiz do projeto

```
2-Projeto-Ultrasonico/
├── README.md              # este arquivo
├── hardware.md            # pinout completo, conectores V7, avisos de fiação
│
└── firmware/              # código que roda na BitDogLab (MicroPython)
    ├── main.py            # ORQUESTRADOR: setup + loop principal
    ├── cfg.py             # configuração central (WiFi, CallMeBot, thresholds, timings)
    │
    ├── ultrasonico.py     # driver HC-SR04  — Ultrasonico.medir_cm()
    ├── imu.py             # driver MPU6050  — IMU.atualizar_detector()  (máquina de estados de queda)
    ├── wifi.py            # ESP8266 via AT  — WiFi.conectar() / enviar_whatsapp()
    │
    ├── buzzer.py          # buzzer PWM      — Buzzer.beep_proximidade()  (freq em degraus)
    ├── vibra.py           # motor ERM PWM   — Vibra.vibrar_proximidade() (intensidade+cadência lineares)
    ├── feedback.py        # LED RGB + NeoPixel 5×5 — Feedback.atualizar()
    ├── display.py         # OLED SSD1306 (opcional)
    │
    ├── debug_esp.py       # varre fiação/baud do ESP8266 (diagnóstico)
    ├── debug_zap.py       # testa envio WhatsApp isolado
    └── rascunhos/         # scripts de teste arquivados, um por periférico
```

Fluxo de dependências (quem importa quem):

```
                 cfg.py  (constantes; não importa ninguém)
                    │
   ┌────────────────┼──────────────────────────────┐
main.py ──▶ ultrasonico · imu · wifi · buzzer · vibra · feedback · display
   (instancia cada classe e chama seus métodos dentro do loop)
```

---

## Arquitetura de software

Cada módulo expõe uma classe com estado próprio e uma API pequena. O `main.py`
não conhece registradores nem GPIOs — ele só chama métodos de alto nível:

| Módulo | Classe | API usada pelo orquestrador |
|--------|--------|------------------------------|
| `ultrasonico.py` | `Ultrasonico` | `medir_cm() -> float` (ou `-1` em timeout) |
| `imu.py` | `IMU` | `atualizar_detector(agora_ms) -> bool` (True = queda) |
| `wifi.py` | `WiFi` | `iniciar()`, `conectar(ssid, senha)`, `enviar_whatsapp(...)`, `.conectado` |
| `buzzer.py` | `Buzzer` | `beep_proximidade(dist, t)`, `toggle_mute()`, `beep_curto(f, ms)` |
| `vibra.py` | `Vibra` | `vibrar_proximidade(dist, t)`, `toggle_mute()`, `pulso_curto(ms)` |
| `feedback.py` | `Feedback` | `atualizar(dist)` |
| `display.py` | `Display` | `mostrar_*()`, `atualizar(...)` |

Todas as constantes ajustáveis (escala de distância, thresholds de queda,
timings) vivem em **`cfg.py`** e são importadas pelo `main.py` — nenhum número
mágico espalhado pelo código.

---

## O orquestrador (`main.py`)

### 1. Setup

Um único barramento I²C (SoftI2C em GP2/GP3) é criado e **injetado** no OLED e no
IMU, que dividem o barramento com o INA226 onboard sem conflito de endereço:

```python
i2c_bus = SoftI2C(scl=Pin(3), sda=Pin(2), freq=100000)

sensor = Ultrasonico(echo_timeout_us=ECHO_TIMEOUT_US)
wifi   = WiFi()
bz     = Buzzer(dist_max=DISTANCIA_MAX_CM, dist_alerta=DISTANCIA_ALERTA_CM)
vb     = Vibra(dist_max=DISTANCIA_MAX_CM, dist_alerta=DISTANCIA_ALERTA_CM)
fb     = Feedback(dist_max=DISTANCIA_MAX_CM, dist_alerta=DISTANCIA_ALERTA_CM, usar_matriz=USAR_MATRIZ)
imu    = IMU(freefall_g=FREEFALL_G, ..., i2c=i2c_bus)
```

Toggles hardcoded no topo do arquivo permitem desligar periféricos lentos sem
mexer no resto:

```python
USAR_OLED   = False   # corta o redesenho SoftI2C (~113 ms) -> loop mais rápido
USAR_MATRIZ = False   # apaga a NeoPixel; o LED RGB continua
```

Quando `USAR_OLED=False`, um `_DisplayNulo` (todos os métodos viram *no-op*)
substitui o `Display` real — o resto do código chama `disp.atualizar(...)` sem
saber que o OLED está desligado.

### 2. Loop principal — pipeline por iteração

Cada volta do `while True` executa este pipeline (nenhuma etapa bloqueia):

```
┌─ botão C ─────▶ toggle mute do buzzer E da vibração
│
├─ HC-SR04 ─────▶ medir_cm() ─▶ mediana móvel (N amostras) ─▶ dist
│
├─ obstáculo ───▶ bz.beep_proximidade(dist, agora)   ← papel do ultrassom
│                 vb.vibrar_proximidade(dist, agora)
│
├─ MPU6050 ─────▶ imu.atualizar_detector(agora)
│                 └─ se queda E wifi.conectado E fora do cooldown:
│                        wifi.enviar_whatsapp(...) ─▶ beep+pulso de confirmação
│
├─ LED ─────────▶ fb.atualizar(dist)   (vermelho piscante durante alerta)
│
└─ OLED ────────▶ throttled: redesenha no máx. a cada DISPLAY_INTERVALO_MS
```

A distância bruta do HC-SR04 passa por uma **mediana móvel** que atualiza a cada
loop (sem o *lag* de uma janela temporal) mas ainda rejeita os *spikes* do sensor:

```python
amostra = sensor.medir_cm()
if amostra < 0:
    _ultimas = []; dist = -1
else:
    _ultimas.append(amostra)
    if len(_ultimas) > MEDIANA_N:
        _ultimas.pop(0)
    dist = sorted(_ultimas)[len(_ultimas) // 2]   # mediana

bz.beep_proximidade(dist, agora)
vb.vibrar_proximidade(dist, agora)
```

O disparo de queda respeita um **cooldown** para não floodar o WhatsApp:

```python
queda = imu.atualizar_detector(agora)
if queda and wifi.conectado:
    if time.ticks_diff(agora, ultimo_alerta) / 1000 > COOLDOWN_ALERTA_SEG or ultimo_alerta == 0:
        if wifi.enviar_whatsapp(TELEFONE, APIKEY, "ALERTA! Queda detectada"):
            ultimo_alerta = agora
            alerta_flag = True
            bz.beep_curto(2500, 200)   # confirmação sonora + háptica
            vb.pulso_curto(200)
```

---

## Rotinas principais (com código)

### HC-SR04 — medição por eco (`ultrasonico.py`)

Dispara um pulso de 10 µs no TRIG e cronometra o ECHO. `time_pulse_us` já traz
timeout embutido (retorna `-1`), então "sem obstáculo" nunca trava o loop:

```python
def medir_cm(self):
    self.trig.value(0); time.sleep_us(2)
    self.trig.value(1); time.sleep_us(10)   # pulso de trigger
    self.trig.value(0)

    duracao = time_pulse_us(self.echo, 1, self.echo_timeout_us)
    if duracao < 0:
        return -1                            # timeout = sem eco
    return round((duracao / 2.0) / 29.15, 1) # 29.15 µs/cm (ida e volta)
```

### Buzzer — pitch em degraus por faixa (`buzzer.py`)

Frequências **discretas** (não contínuas) por faixa de distância — mais perto,
mais agudo. As faixas são as mesmas do LED, então som e cor andam juntos:

```python
FREQ_FAIXA = (1000, 800, 600, 400)   # índice 0 = mais perto ... 3 = mais longe

def beep_proximidade(self, distancia_cm, tempo_ms=0):
    if self.mute or distancia_cm < 0 or distancia_cm > self.dist_max:
        self.parar(); return
    # divide [dist_alerta, dist_max] em 3 terços + a zona crítica
    faixa_total = self.dist_max - self.dist_alerta
    t1 = self.dist_alerta + faixa_total / 3
    t2 = self.dist_alerta + 2 * faixa_total / 3
    faixa = 0 if distancia_cm < self.dist_alerta else \
            1 if distancia_cm < t1 else \
            2 if distancia_cm < t2 else 3
    self._tocar(self.FREQ_FAIXA[faixa])
```

### Motor vibratório — canal háptico linear (`vibra.py`)

Análogo ao som, mas **contínuo**: a intensidade (duty) e a **cadência** dos pulsos
variam linearmente com a proximidade. Na zona crítica vira vibração contínua.
O ERM só parte acima de ~75% de duty, por isso o mapeamento é restrito a
`[DUTY_MIN, DUTY_MAX]` e a distância é comunicada sobretudo pela cadência:

```python
prox = (self.dist_max - distancia_cm) / self.dist_max      # 0.0 longe → 1.0 colado
duty = int(self.DUTY_MIN + prox * (self.DUTY_MAX - self.DUTY_MIN))

if distancia_cm < self.dist_alerta:
    self._vibrar(duty); return                              # crítico → contínuo

intervalo = int(self.INTERVALO_LONGE - prox * (self.INTERVALO_LONGE - self.INTERVALO_PERTO))
ciclo = time.ticks_diff(tempo_ms, self._ultimo_pulso)
if ciclo >= intervalo * 2:
    self._ultimo_pulso = tempo_ms; ciclo = 0
self._vibrar(duty) if ciclo < intervalo else self.parar()  # liga/desliga por timestamp
```

### MPU6050 — detector de queda por queda livre (`imu.py`)

Máquina de estados `normal → freefall → normal`. Quando a magnitude do vetor
aceleração cai abaixo de `freefall_g` (≈ queda livre), confirma a queda **na hora**
e retorna `True` uma única vez:

```python
def atualizar_detector(self, agora_ms=None):
    mag = self.magnitude_accel()          # √(ax²+ay²+az²) em g
    if mag is None:
        return False                       # leitura I²C falhou → mantém estado
    self.ultima_magnitude = mag

    if self._estado == "normal" and mag < self.freefall_g:
        self._estado = "freefall"
        self.freefalls_detectados += 1
        return True                        # QUEDA
    if self._estado == "freefall" and mag >= self.freefall_g:
        self._estado = "normal"            # rearma
    return False
```

### ESP8266 — envio WhatsApp via CallMeBot (`wifi.py`)

Fala AT por UART e monta um `GET` HTTP para a API da CallMeBot. O helper
`_enviar_at` lê a resposta **incrementalmente e sai assim que vê o token esperado**
(`>`, `CLOSED`, `+IPD`…) em vez de esperar o timeout inteiro — o que reduz muito
a latência no caminho feliz. O código `209` (rate-limit) **não** conta como envio:

```python
def enviar_whatsapp(self, telefone, apikey, mensagem):
    path = "/whatsapp.php?phone={}&text={}&apikey={}".format(
        telefone, mensagem.replace(" ", "+"), apikey)

    resp = self._enviar_at('AT+CIPSTART="TCP","api.callmebot.com",80', 5000,
                           ate=("CONNECT", "OK", "ERROR"))
    if "ERROR" in resp and "ALREADY" not in resp:
        return False

    http_req = "GET {} HTTP/1.1\r\nHost: api.callmebot.com\r\nConnection: close\r\n\r\n".format(path)
    self._enviar_at("AT+CIPSEND={}".format(len(http_req)), 1000, ate=(">",))
    resp = self._enviar_at(http_req, 8000, ate=("CLOSED", "+IPD", "SEND FAIL"))
    self._enviar_at("AT+CIPCLOSE", 800)                 # best-effort

    if "209" in resp:                                    # rate-limit CallMeBot
        return False
    return "SEND OK" in resp or "+IPD" in resp
```

---

## Configuração

Tudo em **`firmware/cfg.py`**. Principais chaves:

```python
WIFI_SSID, WIFI_SENHA        # rede à qual o ESP8266 se conecta
TELEFONE, APIKEY             # destino do alerta + chave CallMeBot
DISTANCIA_MAX_CM = 30        # acima disso = "sem obstáculo" (silêncio)
DISTANCIA_ALERTA_CM = 5      # zona crítica → som/vibração contínuos
COOLDOWN_ALERTA_SEG = 10     # intervalo mínimo entre alertas WhatsApp
MEDIANA_N = 3                # janela do filtro de mediana
ECHO_TIMEOUT_US = 18000      # ~300 cm de alcance máx. do HC-SR04
FREEFALL_G = 0.8             # abaixo disso = queda livre
```

**CallMeBot (uma vez):** adicione **+34 644 71 98 32** aos contatos, envie
`I allow callmebot to send me messages`, e use a `apikey` que voltar por mensagem.

## Como rodar

Com a BitDogLab conectada por USB:

```bash
mpremote connect auto fs cp firmware/*.py :   # sobe o firmware
mpremote connect auto reset                   # reinicia (obrigatório!)
```

> Sempre reinicie a placa após o upload — senão o `main.py` novo não roda.
> Para desenvolvimento interativo, o **Thonny** conectado à placa também funciona.

## Hardware

Pinout completo, designadores de conector V7 e avisos de fiação em
**[`hardware.md`](hardware.md)**. Resumo:

| Periférico | GPIO / Conector | Módulo |
|------------|-----------------|--------|
| HC-SR04 TRIG/ECHO | GP8 / GP9 (IDC 14p) | `ultrasonico.py` |
| MPU6050 (I²C1, `0x68`) | GP2/GP3 · J5 | `imu.py` |
| ESP8266 (UART0, 19200 bd) | GP0/GP1 · J6 | `wifi.py` |
| Buzzer A (PWM) | GP21 | `buzzer.py` |
| Motor vibratório | GP14 → driver (transistor) | `vibra.py` |
| NeoPixel 5×5 / LED RGB | GP7 / GP13·GP11·GP12 | `feedback.py` |
| OLED SSD1306 (`0x3C`) | GP2/GP3 · I²C1 | `display.py` |
| Botão C (mute) | GP10 (pull-up) | `main.py` |

> ⚠️ ECHO do HC-SR04 sai em 5 V → usar divisor de tensão para o GP9 (3.3 V).
> ⚠️ O motor **não** liga direto no GPIO: precisa de driver (transistor) no GP14.
