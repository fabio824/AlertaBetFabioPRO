import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
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

def verificar_estatisticas(fixture_id, headers):
    url = f"https://v3.football.api-sports.io/fixtures/statistics"
    querystring = {"fixture": fixture_id}
    try:
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        dados = response.json()
        if "response" in dados and len(dados["response"]) >= 2:
            stats_casa = {s["type"]: s["value"] for s in dados["response"][0]["statistics"]}
            stats_fora = {s["type"]: s["value"] for s in dados["response"][1]["statistics"]}
            return stats_casa, stats_fora
    except Exception as e:
        print(f"Erro ao buscar estatísticas: {e}")
    return {}, {}

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
                fixture_id = match["fixture"]["id"]
                status = match["fixture"]["status"]["short"]
                tempo = match["fixture"]["status"]["elapsed"]
                time_casa = match["teams"]["home"]["name"]
                time_fora = match["teams"]["away"]["name"]
                gols_casa = match["goals"]["home"] or 0
                gols_fora = match["goals"]["away"] or 0
                
                # Monitora primeiro tempo e segundo tempo dentro dos intervalos configurados
                if (status == "1H" and FIRST_HALF_START <= tempo <= FIRST_HALF_END) or \
                   (status == "2H" and SECOND_HALF_START <= tempo <= SECOND_HALF_END):
                    
                    stats_casa, stats_fora = verificar_estatisticas(fixture_id, headers)
                    
                    # Exemplo de captura de estatísticas (caso a API retorne os dados)
                    chutes_casa = stats_casa.get("Shots on Goal", 0) or 0
                    chutes_fora = stats_fora.get("Shots on Goal", 0) or 0
                    total_chutes = int(chutes_casa) + int(chutes_fora)
                    
                    escanteios_casa = stats_casa.get("Corner Kicks", 0) or 0
                    escanteios_fora = stats_fora.get("Corner Kicks", 0) or 0
                    total_escanteios = int(escanteios_casa) + int(escanteios_fora)
                    
                    # Dispara alerta se passar nos filtros mínimos
                    if total_chutes >= MIN_SHOTS or total_escanteios >= MIN_CORNERS:
                        mensagem = (
                            f"🚨 *ALERTA DE OPORTUNIDADE!* 🚨\n\n"
                            f"⚽ *{time_casa} {gols_casa} x {gols_fora} {time_fora}*\n"
                            f"⏱ Tempo: *{tempo}' ({status})*\n\n"
                            f"📊 *Estatísticas Atuais:*\n"
                            f"• Chutes ao gol: {total_chutes}\n"
                            f"• Escanteios: {total_escanteios}\n\n"
                            f"🔥 Fique de olho para entrada!"
                        )
                        enviar_telegram(mensagem)
                        
    except Exception as e:
        print(f"Erro ao buscar partidas na API: {e}")

print("Robô de alertas inteligente iniciado com sucesso!")

# Loop principal que roda a cada 60 segundos
while True:
    verificar_jogos()
    time.sleep(60)
