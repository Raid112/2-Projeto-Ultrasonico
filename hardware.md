# Hardware — Projeto 2 (Sensor de Queda com Alerta WhatsApp)

**Plataforma:** BitDogLab V7 (RP2040) + ESP8266 + HC-SR04 + MPU6050
**Lab de Sistemas Embarcados (FEEC/UNICAMP)**

Funcionalidade: o HC-SR04 atua como sensor de ré sonoro (buzzer), o MPU6050
detecta queda real (freefall + impacto) e dispara um alerta WhatsApp via ESP8266
(CallMeBot). Feedback visual em NeoPixel + LED RGB; botão C muta o buzzer.

---

## Designadores de conector V7 (serigrafia da placa)

> A doc oficial (BIH) nomeia os conectores só por função. Os rótulos de silk
> da placa física V7 são:
>
> - **Conector I2C1 = J5** (canto superior **esquerdo**) — GP2/GP3
> - **Conector I2C0 = J6** (canto superior **direito**) — GP0/GP1

---

## Periféricos externos (fiação)

### HC-SR04 (ultrassom) — `firmware/ultrasonico.py`

| Sensor | GPIO BitDog | Conector |
|--------|-------------|----------|
| TRIG   | GP8 (saída) | IDC pino 4 |
| ECHO   | GP9 (entrada) | IDC pino 6 |
| VCC    | 5V          | IDC pino 2 |
| GND    | GND         | IDC pino 1 |

> ⚠️ O ECHO do HC-SR04 sai em **5V** e o RP2040 é 3.3V. Recomenda-se divisor de
> tensão (ex.: 1k + 2k) no ECHO para não estressar o GPIO.

### MPU6050 (IMU) — `firmware/imu.py`, endereço `0x68` (AD0=GND)

| IMU | GPIO BitDog | Conector  |
|-----|-------------|-----------|
| SDA | GP2 (I2C1)  | J5 (I2C1) |
| SCL | GP3 (I2C1)  | J5 (I2C1) |
| VCC | 3V3         | J5 (I2C1) |
| GND | GND         | J5 (I2C1) |

### ESP8266 (WiFi/WhatsApp via AT) — `firmware/wifi.py`, UART0 @ 19200 baud

| ESP       | GPIO BitDog      | Conector  |
|-----------|------------------|-----------|
| RX do ESP | GP0 (TX do Pico) | J6 (I2C0) |
| TX do ESP | GP1 (RX do Pico) | J6 (I2C0) |
| VCC       | 3V3              | J6 (I2C0) |
| GND       | GND              | J6 (I2C0) |

> ⚠️ Erro clássico: TX/RX invertidos. Existe `firmware/debug_esp.py` que varre
> as combinações (GP0/GP1 padrão, invertido, e UART1 GP4/GP5).

---

## Periféricos onboard (sem fiação externa)

| Periférico       | GPIO              | Módulo        |
|------------------|-------------------|---------------|
| Buzzer A (PWM)   | GP21              | `buzzer.py`   |
| NeoPixel 5×5     | GP7 (25 LEDs)     | `feedback.py` |
| LED RGB — R      | GP13 (PWM 1 kHz)  | `feedback.py` |
| LED RGB — G      | GP11 (PWM 1 kHz)  | `feedback.py` |
| LED RGB — B      | GP12 (PWM 1 kHz)  | `feedback.py` |
| Botão C (mute)   | GP10 (pull-up)    | `main.py`     |
| OLED SSD1306 `0x3C` | GP2/GP3 (I2C1) | `display.py`  |

---

## Barramento I2C1 (GP2/GP3 = J5) — dispositivos compartilhados

Três dispositivos no mesmo barramento, sem conflito de endereço:

| Dispositivo         | Endereço | Origem            |
|---------------------|----------|-------------------|
| OLED SSD1306        | `0x3C`   | onboard           |
| MPU6050 (IMU)       | `0x68`   | externo (J5)      |
| INA226 (BMS)        | `0x40`   | onboard (V7)      |

> O OLED onboard compartilha GP2/GP3 com o conector I2C1 (J5) e com a barra
> de terminais DIG2/DIG3. Ao ligar o MPU6050 em J5, ele convive com OLED e INA226.

---

## Resumo de conectores

| Periférico | Conector V7 | Barramento  |
|------------|-------------|-------------|
| MPU6050    | **J5**      | I2C1        |
| ESP8266    | **J6**      | I2C0 (UART0)|
| HC-SR04    | IDC 14p     | GPIO8/9     |
