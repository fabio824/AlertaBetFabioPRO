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

# Mantém o servidor web ativo para o Render
threading.Thread(target=run_server, daemon=True).start()

# --- LÓGICA PRINCIPAL DO BOT ---
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

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensagem,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Erro ao enviar mensagem no Telegram: {e}")

def verificar_jogos():
    url = "https://v3.football.api-sports.io/fixtures"
    querystring = {"live": "all"}
    headers = {
        "x-apisports-key": API_FOOTBALL_KEY
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=15)
        dados = response.json()
        
        if "response" in dados:
            partidas = dados["response"]
            print(f"Jogos ao vivo encontrados: {len(partidas)}")
            
            for match in partidas:
                status = match["fixture"]["status"]["short"]
                tempo = match["fixture"]["status"]["elapsed"]
                time_casa = match["teams"]["home"]["name"]
                time_fora = match["teams"]["away"]["name"]
                
                # Exemplo de alerta base (você pode customizar os filtros conforme suas variáveis)
                # O bot vai monitorar o primeiro e o segundo tempo
                if status in ["1H", "2H"]:
                    # Aqui entram as estatísticas da API (ataques perigosos, chutes, etc.)
                    # Por enquanto, vamos deixar a estrutura pronta rodando em loop
                    pass
                    
    except Exception as e:
        print(f"Erro ao buscar partidas na API: {e}")

print("Robô de alertas iniciado com sucesso! Monitorando partidas...")

# Loop principal que roda a cada 60 segundos
while True:
    verificar_jogos()
    time.sleep(60)
