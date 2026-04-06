"""Dashboard do Projeto Ultrasonico — servidor Flask.

Recebe dados de distancia do ESP8266 via HTTP POST
e serve pagina HTML com grafico em tempo real.

Uso: python dashboard.py
Acesse: http://localhost:5000
"""

from flask import Flask, request, jsonify, send_file
from datetime import datetime
from collections import deque

app = Flask(__name__)

# Historico: ultimos 300 pontos (~5 min a 1 leitura/s)
historico = deque(maxlen=300)
alertas = deque(maxlen=50)


@app.route("/")
def index():
    return send_file("index.html")


@app.route("/api/dados", methods=["POST"])
def receber_dados():
    dist = request.form.get("dist", type=float, default=-1)
    alerta = request.form.get("alerta", type=int, default=0)
    agora = datetime.now().strftime("%H:%M:%S")

    historico.append({"t": agora, "dist": dist})

    if alerta:
        alertas.append({"t": agora, "dist": dist})

    print(f"[{agora}] dist={dist} cm  alerta={alerta}")
    return "ok", 200


@app.route("/api/dados", methods=["GET"])
def enviar_dados():
    return jsonify({
        "historico": list(historico),
        "alertas": list(alertas),
    })


if __name__ == "__main__":
    print("Dashboard rodando em http://0.0.0.0:5000")
    app.run(host="0.0.0.0", port=5000, debug=False)
