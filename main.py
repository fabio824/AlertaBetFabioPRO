import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread

# Servidor web falso para o Render manter o bot ativo de graça
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot rodando!")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

Thread(target=run_server, daemon=True).start()

# --- SEU CÓDIGO DO BOT COMEÇA AQUI ---
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
