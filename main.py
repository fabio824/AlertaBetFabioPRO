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

# Mantém o servidor web ativo no Render
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

def buscar_estatisticas_detalhadas(fixture_id, headers):
    url = "https://v3.football.api-sports.io/fixtures/statistics"
    params = {"fixture": fixture_id}
    stats = {
        "escanteios_casa": 0, "escanteios_fora": 0,
        "chutes_gol_casa": 0, "chutes_gol_fora": 0,
        "chutes_fora_casa": 0, "chutes_fora_fora": 0,
        "posse_casa": "50%", "posse_fora": "50%",
        "ataques_perigosos_casa": 0, "ataques_perigosos_fora": 0
    }
    try:
        response = requests.get(url, headers=headers, params=params, timeout=10)
        dados = response.json()
        if "response" in dados and len(dados["response"]) >= 2:
            for i, team_data in enumerate(dados["response"]):
                is_home = (i == 0)
                for s in team_data.get("statistics", []):
                    stype = s.get("type")
                    sval = s.get("value")
                    if sval is None:
                        sval = 0
                    
                    if stype == "Corner Kicks":
                        if is_home: stats["escanteios_casa"] = int(sval)
                        else: stats["escanteios_fora"] = int(sval)
                    elif stype == "Shots on Goal":
                        if is_home: stats["chutes_gol_casa"] = int(sval)
                        else: stats["chutes_gol_fora"] = int(sval)
                    elif stype == "Shots off Goal":
                        if is_home: stats["chutes_fora_casa"] = int(sval)
                        else: stats["chutes_fora_fora"] = int(sval)
                    elif stype == "Ball Possession":
                        if is_home: stats["posse_casa"] = str(sval)
                        else: stats["posse_fora"] = str(sval)
                    elif stype == "Dangerous Attacks":
                        if is_home: stats["ataques_perigosos_casa"] = int(sval)
                        else: stats["ataques_perigosos_fora"] = int(sval)
    except Exception as e:
        print(f"Erro ao buscar estatísticas: {e}")
    return stats

def verificar_jogos():
    url = "https://v3.football.api-sports.io/fixtures"
    querystring = {"live": "all"}
    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    
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
                
                if tempo is None:
                    continue
                
                time_casa = match["teams"]["home"]["name"]
                time_fora = match["teams"]["away"]["name"]
                liga = match["league"]["name"]
                pais = match["league"]["country"]
                gols_casa = match["goals"]["home"] or 0
                gols_fora = match["goals"]["away"] or 0
                
                # Verifica se está no intervalo configurado (1º ou 2º tempo)
                no_primeiro_tempo = (status == "1H" and FIRST_HALF_START <= tempo <= FIRST_HALF_END)
                no_segundo_tempo = (status == "2H" and SECOND_HALF_START <= tempo <= SECOND_HALF_END)
                
                if no_primeiro_tempo or no_segundo_tempo:
                    st = buscar_estatisticas_detalhadas(fixture_id, headers)
                    
                    total_escanteios = st["escanteios_casa"] + st["escanteios_fora"]
                    total_chutes_gol = st["chutes_gol_casa"] + st["chutes_gol_fora"]
                    total_chutes_fora = st["chutes_fora_casa"] + st["chutes_fora_fora"]
                    total_ataques_perigosos = st["ataques_perigosos_casa"] + st["ataques_perigosos_fora"]
                    
                    # Dispara o alerta se atingir o mínimo de escanteios configurado
                    if total_escanteios >= MIN_CORNERS:
                        mensagem = (
                            f"🚨 *Alerta Oportunidade: RACE/OVER* 🚨\n\n"
                            f"⚽ *Jogo:* {time_casa} x {time_fora}\n"
                            f"🏆 *Competição:* {pais} - {liga}\n"
                            f"⏱ *Tempo:* {tempo}' ({status})\n"
                            f"📊 *Resultado:* {gols_casa} x {gols_fora} (LIVE)\n\n"
                            f"🔥 *Ataques Perigosos:* {st['ataques_perigosos_casa']} - {st['ataques_perigosos_fora']}\n\n"
                            f"📌 *Detalhes do Jogo:*\n"
                            f"🚩 Escanteios: {st['escanteios_casa']} - {st['escanteios_fora']} (Total: {total_escanteios})\n"
                            f"🎯 Chutes ao Gol: {st['chutes_gol_casa']} - {st['chutes_gol_fora']} (Total: {total_chutes_gol})\n"
                            f"🚀 Chutes para Fora: {st['chutes_fora_casa']} - {st['chutes_fora_fora']} (Total: {total_chutes_fora})\n"
                            f"📈 Posse de Bola: {st['posse_casa']} / {st['posse_fora']}\n\n"
                            f"💡 *Oportunidade para Cantos!*"
                        )
                        enviar_telegram(mensagem)
                        
    except Exception as e:
        print(f"Erro ao buscar partidas na API: {e}")

print("Robô estilo 'Rei dos Cantos' iniciado com sucesso!")

# Loop que roda a cada 60 segundos
while True:
    verificar_jogos()
    time.sleep(60)
