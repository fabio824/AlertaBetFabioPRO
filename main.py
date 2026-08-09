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


API_URL = "https://v3.football.api-sports.io"


def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    dados = {
        "chat_id": CHAT_ID,
        "text": mensagem,
    }

    resposta = requests.post(url, data=dados, timeout=15)

    if resposta.status_code != 200:
        print("Erro Telegram:", resposta.text)


def buscar_jogos_ao_vivo():
    headers = {
        "x-apisports-key": API_FOOTBALL_KEY
    }

    resposta = requests.get(
        f"{API_URL}/fixtures?live=all",
        headers=headers,
        timeout=20
    )

    resposta.raise_for_status()

    return resposta.json().get("response", [])


def buscar_estatisticas(fixture_id):
    headers = {
        "x-apisports-key": API_FOOTBALL_KEY
    }

    resposta = requests.get(
        f"{API_URL}/fixtures/statistics",
        params={"fixture": fixture_id},
        headers=headers,
        timeout=20
    )

    resposta.raise_for_status()

    return resposta.json().get("response", [])


def obter_valor(estatisticas, nome):
    for item in estatisticas:
        if item.get("type") == nome:
            valor = item.get("value")

            if valor is None:
                return 0

            if isinstance(valor, str):
                valor = valor.replace("%", "")

            try:
                return int(valor)
            except:
                return 0

    return 0


def analisar_jogo(jogo):
    fixture = jogo["fixture"]
    teams = jogo["teams"]

    minuto = fixture["status"].get("elapsed")

    if not minuto:
        return None

    if not (
        FIRST_HALF_START <= minuto <= FIRST_HALF_END
        or SECOND_HALF_START <= minuto <= SECOND_HALF_END
    ):
        return None

    fixture_id = fixture["id"]

    estatisticas = buscar_estatisticas(fixture_id)

    if len(estatisticas) < 2:
        return None

    ataques = []
    finalizacoes = []
    escanteios = []

    for equipe in estatisticas:
        stats = equipe.get("statistics", [])

        ataques.append(obter_valor(stats, "Dangerous Attacks"))
        finalizacoes.append(obter_valor(stats, "Total Shots"))
        escanteios.append(obter_valor(stats, "Corner Kicks"))

    ataques_total = sum(ataques)
    finalizacoes_total = sum(finalizacoes)
    escanteios_total = sum(escanteios)

    if minuto <= 45:
        minimo_ataques = MIN_DANGEROUS_ATTACKS_HT
    else:
        minimo_ataques = MIN_DANGEROUS_ATTACKS_FT

    if ataques_total < minimo_ataques:
        return None

    if finalizacoes_total < MIN_SHOTS:
        return None

    if escanteios_total < MIN_CORNERS:
        return None

    casa = teams["home"]["name"]
    fora = teams["away"]["name"]

    placar_casa = fixture["goals"]["home"] or 0
    placar_fora = fixture["goals"]["away"] or 0

    mensagem = (
        "🚨 ALERTA BET FÁBIO PRO 🚨\n\n"
        f"⚽ {casa} x {fora}\n"
        f"⏱️ Minuto: {minuto}'\n"
        f"📊 Placar: {placar_casa} x {placar_fora}\n\n"
        f"🔥 Ataques perigosos: {ataques_total}\n"
        f"🎯 Finalizações: {finalizacoes_total}\n"
        f"🚩 Escanteios: {escanteios_total}\n\n"
        "📌 Jogo dentro dos critérios configurados.\n"
        "⚠️ Alerta estatístico — não é garantia de resultado."
    )

    return mensagem


def main():
    print("🤖 ALERTA BET FÁBIO PRO iniciado!")

    while True:
        try:
            jogos = buscar_jogos_ao_vivo()

            print(f"Jogos ao vivo encontrados: {len(jogos)}")

            for jogo in jogos:
                try:
                    alerta = analisar_jogo(jogo)

                    if alerta:
                        print(alerta)
                        enviar_telegram(alerta)

                except Exception as erro:
                    print("Erro ao analisar jogo:", erro)

            time.sleep(60)

        except Exception as erro:
            print("Erro principal:", erro)
            time.sleep(60)


if __name__ == "__main__":
    main()
