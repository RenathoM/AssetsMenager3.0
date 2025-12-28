import requests
import os
import json

# Variáveis de Ambiente (Configuradas nos Secrets do GitHub)
API_KEY = os.getenv("ROBLOX_API_KEY")
WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK") # Adicione este Secret no GitHub
EVENT_PAYLOAD = json.loads(os.getenv("GITHUB_EVENT_PAYLOAD", "{}"))
CLIENT_PAYLOAD = EVENT_PAYLOAD.get("client_payload", {})

USER_ID = CLIENT_PAYLOAD.get("target_user_id")
PLAYER_NAME = CLIENT_PAYLOAD.get("player_name", "Usuário")
EXPERIMENT_ID = CLIENT_PAYLOAD.get("experiment_id")

def send_to_discord(filename, asset_id, status_code):
    if status_code == 200:
        # Link para baixar/ver o asset no site do Roblox
        asset_url = f"https://www.roblox.com/library/{asset_id}"
        # Link que o Studio usa para carregar o rbxm (exige permissão no Studio)
        rbxm_link = f"rbxassetid://{asset_id}"
        
        description = (
            f"**Dono:** {PLAYER_NAME} ({USER_ID})\n"
            f"**Arquivo:** `{filename}`\n"
            f"**Asset ID:** `{asset_id}`\n\n"
            f"🔗 [Ver no Site]({asset_url})\n"
            f"📦 **Referência:** `{rbxm_link}`"
        )
        color = 3066993 # Verde
    else:
        description = f"❌ Erro ao subir `{filename}`. Status: {status_code}"
        color = 15158332 # Vermelho

    payload = {
        "username": "Asset Manager 3.0",
        "embeds": [{
            "title": "📦 Asset Integrado com Sucesso!",
            "description": description,
            "color": color,
            "footer": {"text": "GitHub Integration | Asset Manager 3.0"}
        }]
    }
    requests.post(WEBHOOK_URL, json=payload)

def start_process():
    assets_path = "assets/"
    for filename in os.listdir(assets_path):
        file_path = os.path.join(assets_path, filename)
        
        # Lógica de Upload para Roblox Cloud
        asset_config = {
            "assetType": "Model", 
            "displayName": filename,
            "creationContext": {"creator": {"userId": USER_ID}}
        }
        
        with open(file_path, "rb") as f:
            files = {
                "request": (None, json.dumps(asset_config), "application/json"),
                "fileContent": (filename, f, "application/octet-stream")
            }
            headers = {"x-api-key": API_KEY}
            response = requests.post("https://apis.roblox.com/assets/v1/assets", headers=headers, files=files)
            
            if response.status_code == 200:
                asset_id = response.json().get("assetId")
                send_to_discord(filename, asset_id, 200)
            else:
                send_to_discord(filename, None, response.status_code)

if __name__ == "__main__":
    start_process()