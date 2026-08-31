import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading
import time
import requests

from configuracao import (
    TELEGRAM_TOKEN,
    CHAT_ID,
    API_FOOTBALL_KEY,
    INICIO_DO_PRIMEIRO_TEMPO,
    FIM_DA_PRIMEIRA_METADE,
    INICIO_DO_SEGUNDO_TEMPO,
    SEGUNDA_METADE_FIM,
    CANTOS_MIN,
)

class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot rodando!")

    def do_HEAD(self):
        self.send_response(200)
        self.end_headers()

def executar_servidor():
    porta = int(os.environ.get("PORT", 10000))
    servidor = HTTPServer(("0.0.0.0", porta), servidor.serve_forever if hasattr(HTTPServer, 'serve_forever') else None)
    # Mantém o servidor web ativo no Render
    server = HTTPServer(("0.0.0.0", porta), SimpleHandler)
    server.serve_forever()

# Mantém o servidor web ativo em segundo plano no Render
threading.Thread(target=executar_servidor, daemon=True).start()

def enviar_telegrama(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": mensagem,
        "parse_mode": "Markdown"
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Erro ao enviar mensagem no Telegram: {e}")

def buscar_estatisticas_detalhadas(fixture_id):
    url = f"https://v3.football.api-sports.io/fixtures/statistics"
    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    params = {"fixture": fixture_id}
    
    estatisticas = {
        "escanteios_casa": 0, "escanteios_fora": 0,
        "chutes_gol_casa": 0, "chutes_gol_fora": 0,
        "chutes_fora_casa": 0, "chutes_fora_fora": 0,
        "posse_casa": "50%", "posse_fora": "50%",
        "ataques_perigosos_casa": 0, "ataques_perigosos_fora": 0
    }
    
    try:
        response = requests.get(url, headers=headers, params=params)
        dados = response.json()
        
        for i, dados_da_equipe in enumerate(dados.get("response", [])):
            e_casa = (i == 0)
            for s in dados_da_equipe.get("statistics", []):
                tipo = s.get("type")
                sval = s.get("value")
                if sval is None:
                    sval = 0
                
                try:
                    val_int = int(str(sval).replace("%", ""))
                except:
                    val_int = sval

                if tipo == "Corner Kicks":
                    if e_casa: estatisticas["escanteios_casa"] = val_int
                    else: estatisticas["escanteios_fora"] = val_int
                elif tipo == "Shots on Goal":
                    if e_casa: estatisticas["chutes_gol_casa"] = val_int
                    else: estatisticas["chutes_gol_fora"] = val_int
                elif tipo == "Shots off Goal":
                    if e_casa: estatisticas["chutes_fora_casa"] = val_int
                    else: estatisticas["chutes_fora_fora"] = val_int
                elif tipo == "Ball Possession":
                    if e_casa: estatisticas["posse_casa"] = str(sval)
                    else: estatisticas["posse_fora"] = str(sval)
                elif tipo == "Dangerous Attacks":
                    if e_casa: estatisticas["ataques_perigosos_casa"] = val_int
                    else: estatisticas["ataques_perigosos_fora"] = val_int
    except Exception as e:
        print(f"Erro ao buscar estatísticas: {e}")
        
    return estatisticas

def verificar_jogos():
    url = "https://v3.football.api-sports.io/fixtures"
    headers = {"x-apisports-key": API_FOOTBALL_KEY}
    params = {"live": "all"}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        dados = response.json()
        partidas = dados.get("response", [])
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
            
            no_primeiro_tempo = (status == "1H" and INICIO_DO_PRIMEIRO_TEMPO <= tempo <= FIM_DA_PRIMEIRA_METADE)
            no_segundo_tempo = (status == "2H" and INICIO_DO_SEGUNDO_TEMPO <= tempo <= SEGUNDA_METADE_FIM)
            
            if no_primeiro_tempo or no_segundo_tempo:
                rua = buscar_estatisticas_detalhadas(fixture_id)
                
                total_escanteios = rua["escanteios_casa"] + rua["escanteios_fora"]
                total_chutes_gol = rua["chutes_gol_casa"] + rua["chutes_gol_fora"]
                total_chutes_fora = rua["chutes_fora_casa"] + rua["chutes_fora_fora"]
                total_ataques_perigosos = rua["ataques_perigosos_casa"] + rua["ataques_perigosos_fora"]
                
                if total_escanteios >= CANTOS_MIN:
                    mensagem = (
                        f"🚨 *Alerta Oportunidade: RACE/OVER* 🚨\n\n"
                        f"⚽ *Jogo:* {time_casa} x {time_fora}\n"
                        f"🏆 *Competição:* {pais} - {liga}\n"
                        f"⏱ *Tempo:* {tempo}' ({status})\n"
                        f"📊 *Resultado:* {gols_casa}x{gols_fora} (AO VIVO)\n"
                        f"🔥 *Ataques Perigosos:* {total_ataques_perigosos}\n"
                        f"📌 *Detalhes do Jogo:*\n"
                        f"🚩 Escanteios: {rua['escanteios_casa']} - {rua['escanteios_fora']}\n"
                        f"🎯 Chutes ao Gol: {rua['chutes_gol_casa']} - {rua['chutes_gol_fora']}\n"
                        f"🚀 Chutes para Fora: {rua['chutes_fora_casa']} - {rua['chutes_fora_fora']}\n"
                        f"📈 Posse de Bola: {rua['posse_casa']} / {rua['posse_fora']}\n"
                        f"💡 *Oportunidade para Cantos!*"
                    )
                    enviar_telegrama(mensagem)
                    
    except Exception as e:
        print(f"Erro ao buscar partidas na API: {e}")

print("Robô estilo 'Rei dos Cantos' iniciado com sucesso!")

# Loop que roda a cada 60 segundos
while True:
    verificar_jogos()
    time.sleep(60)
