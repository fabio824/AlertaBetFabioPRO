import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot rodando!")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(("0.0.0.0", port), SimpleHandler)
    server.serve_forever()

threading.Thread(target=run_server, daemon=True).start()

import time
import requests

from config import (
    TELEGRAM_TOKEN,
    ID_DO_CHAT,
    API_FOOTBALL_KEY,
    INÍCIO_DO_PRIMEIRO_TEMPO,
    PRIMEIRA_METADE_FIM,
    INÍCIO_DO_SEGUNDO_TEMPO,
    SEGUNDA_METADE_FIM,
    MIN_DANGEROUS_ATTACKS_HT,
    MIN_ATAQUES_PERIGOSOS_FT,
    MIN_SHOTS,
    CANTOS_MIN,
)
