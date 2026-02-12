import os
import requests
import sys


def get_env_variable(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Variável de ambiente obrigatória ausente: {name}")
    return value


def send_telegram_message(token: str, chat_id: str, text: str) -> None:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    response = requests.post(
        url,
        data={
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        },
        timeout=15
    )

    if response.status_code != 200:
        raise RuntimeError(
            f"Erro ao enviar mensagem. "
            f"Status: {response.status_code} | Resposta: {response.text}"
        )


def main():
    bot_token = get_env_variable("BOT_TOKEN")
    chat_id = get_env_variable("CHAT_ID")

    send_telegram_message(
        bot_token,
        chat_id,
        "🚀 Sistema ativo no GitHub Actions."
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"ERRO: {e}")
        sys.exit(1)
