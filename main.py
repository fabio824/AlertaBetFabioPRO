import os
import requests
import time
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from config import (
    TELEGRAM_TOKEN,
    CHAT_ID,
    API_FOOTBALL_KEY,
    INICIO_DO_PRIMEIRO_TEMPO,
    FIM_DA_PRIMEIRA_METADE,
    INICIO_DO_SEGUNDO_TEMPO,
    SEGUNDA_METADE_FIM,
    CANTOS_MIN,
)

# Servidor HTTP simples para manter o Render ativo (Health Check)
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot rodando com sucesso!")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

# Função para enviar mensagens no Telegram
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, json=payload)
        return response.json()
    except Exception as e:
        print(f"Erro ao enviar mensagem: {e}")

# Exemplo de teste para confirmar que o bot está vivo no Telegram
def main():
    print("Iniciando o bot Alerta Bet Fabio...")
    send_telegram_message("🚨 *Alerta Bet Fábio Conectado!* 🚨\nO robô foi iniciado com sucesso e está monitorando os jogos.")
    
    # Loop principal do bot (aqui depois colocaremos a varredura da API de futebol)
    while True:
        time.sleep(60)

if __name__ == "__main__":
    # Inicia o servidor HTTP em segundo plano para o Render não desligar
    server_thread = threading.Thread(target=run_server)
    server_thread.daemon = True
    server_thread.start()
    
    # Executa o bot principal
    main()
