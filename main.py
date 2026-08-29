import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot rodando!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

# Inicia o servidor web em segundo plano para o Render não reclamar
threading.Thread(target=run_server, daemon=True).start()

# --- SEU CÓDIGO DO BOT COMEÇA AQUI ---
try:
    import time
    import requests

    from config import (
        TELEGRAM_TOKEN,
        CHAT_ID,
        API_FOOTBALL_KEY,
        FIRST_HALF_START,
        FIRST_HALF_END,
        SECOND_HALF_START,
        SECOND_HALF_END,
        MIN_DANGEROUS_ATTACKS_HT,
        MIN_DANGEROUS_ATTACKS_FT,
        MIN_SHOTS,
        MIN_CORNERS,
    )
    
    print("Configurações carregadas com sucesso! Iniciando loops...")
    
    # Deixe o servidor rodando em loop infinito para o app não fechar
    while True:
        time.sleep(60)

except Exception as e:
    print(f"Erro ao iniciar o bot: {e}")
    while True:
        time.sleep(60)
