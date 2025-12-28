# TITULO: bulk_upload.py (Python Script)
import requests
import os
import json

# Pegando os dados do Roblox
event_data = json.loads(os.getenv("GITHUB_EVENT_PAYLOAD", "{}"))
payload = event_data.get("client_payload", {})

API_KEY = os.getenv("ROBLOX_API_KEY")
MY_USER_ID = "SEU_ID_ROBLOX_AQUI" # COLOQUE SEU ID ROBLOX AQUI
WEBHOOK_URL = payload.get("discord_webhook")
ASSET_NAME = payload.get("asset_name")
PLAYER_NAME = payload.get("player_name")

def send_discord(msg, success=True, new_id=None):
    if not WEBHOOK_URL: return
    color = 3066993 if success else 15158332
    data = {
        "embeds": [{
            "title": "📦 Asset Manager 3.0",
            "description": msg,
            "color": color,
            "fields": [
                {"name": "Jogador", "value": PLAYER_NAME, "inline": True},
                {"name": "Novo ID", "value": str(new_id) if new_id else "N/A", "inline": True}
            ]
        }]
    }
    requests.post(WEBHOOK_URL, json=data)

def main():
    if not API_KEY:
        send_discord("Erro: ROBLOX_API_KEY não configurada no GitHub.", False)
        return

    # Procura arquivo na pasta assets/ (ex: um modelo.rbxm padrão)
    file_path = "assets/default.rbxm" # Certifique-se que este arquivo existe no seu GitHub
    
    if not os.path.exists(file_path):
        send_discord("Erro: Arquivo base 'assets/default.rbxm' não encontrado no repositório.", False)
        return

    url = "https://apis.roblox.com/assets/v1/assets"
    asset_config = {
        "assetType": "Model",
        "displayName": f"Gerado para {PLAYER_NAME}",
        "creationContext": {"creator": {"userId": str(MY_USER_ID)}}
    }

    with open(file_path, "rb") as f:
        files = {
            "request": (None, json.dumps(asset_config), "application/json"),
            "fileContent": ("model.rbxm", f, "application/octet-stream")
        }
        headers = {"x-api-key": API_KEY}
        response = requests.post(url, headers=headers, files=files)
        
        if response.status_code == 200:
            new_id = response.json().get("assetId")
            send_discord(f"✅ Seu asset foi processado e está na conta central!", True, new_id)
        else:
            send_discord(f"❌ Erro Roblox API: {response.status_code}", False)

if __name__ == "__main__":
    main()