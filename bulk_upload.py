import requests
import os
import json
import time

MY_GROUP_ID = "633516837"
UNIVERSE_ID = "9469723620"
EVENT_PATH = os.getenv("GITHUB_EVENT_PATH")

def main():
    if not EVENT_PATH or not os.path.exists(EVENT_PATH):
        print("❌ Erro: Arquivo de evento não encontrado.")
        return

    with open(EVENT_PATH, 'r') as f:
        payload = json.load(f).get("client_payload", {})

    # Identifica qual token o script vai tentar usar
    category = payload.get("asset_type", "Model").upper()
    token_name = f"RBX_TOKEN_{category}"
    USER_TOKEN = os.getenv(token_name)

    # PRINT DE DIAGNÓSTICO (Aparecerá no log do GitHub)
    if not USER_TOKEN:
        print(f"❌ ERRO: O Secret '{token_name}' não foi encontrado no ambiente do GitHub!")
        print(f"⚠️ Verifique se você criou o segredo com esse nome exato nas configurações do repositório.")
        return
    else:
        print(f"✅ Token '{token_name}' carregado com sucesso (Início: {USER_TOKEN[:10]}...)")

    # Tenta o Upload
    url = "https://apis.roblox.com/assets/v1/assets"
    headers = {"Authorization": f"Bearer {USER_TOKEN.strip()}"}
    
    # ... (Restante do código de upload)
    # Se o erro "Failed to read token" persistir aqui, o token existe mas é INVÁLIDO ou expirou.
