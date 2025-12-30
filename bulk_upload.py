import requests
import os
import json

# Carrega os dados enviados pelo Roblox
event_json = os.getenv("GITHUB_EVENT_PAYLOAD", "{}")
payload = json.loads(event_json).get("client_payload", {})

# CONFIGURAÇÃO DO GRUPO
API_KEY = os.getenv("ROBLOX_API_KEY")
MY_GROUP_ID = "633516837"
WEBHOOK_URL = payload.get("discord_webhook")

def main():
    # Detecta o arquivo no repositório
    file_path = "assets.rbxm" if os.path.exists("assets.rbxm") else "default.rbxm"
    msg = "Processado com sucesso!"
    new_id = "N/A"

    try:
        # Upload para Roblox API
        url = "https://apis.roblox.com/assets/v1/assets"
        asset_config = {
            "assetType": "Model",
            "displayName": f"Pacote: {payload.get('asset_id')}",
            "description": f"Este item foi gerado para {payload.get('player_name')}.",
            "creationContext": {
                "creator": {
                    "groupId": str(MY_GROUP_ID) # Alterado de userId para groupId
                }
            }
        }
        
        with open(file_path, "rb") as f:
            files = {
                "request": (None, json.dumps(asset_config), "application/json"),
                "fileContent": (file_path, f, "application/octet-stream")
            }
            
            response = requests.post(url, headers={"x-api-key": API_KEY}, files=files)
            
            if response.status_code == 200:
                new_id = response.json().get("assetId")
            else:
                msg = f"Erro no Upload: {response.status_code} - {response.text}"

    except Exception as e:
        msg = f"Erro Crítico: {str(e)}"

    # Envio para o Discord (Mantido igual)
    if WEBHOOK_URL:
        embed = {
            "title": "📦 Your Asset Is Ready!",
            "description": f"Olá **{payload.get('player_name')}**, seu arquivo foi gerado e enviado para o grupo!",
            "color": 3066993,
            "fields": [
                {"name": "ID Original", "value": f"`{payload.get('asset_id')}`", "inline": True},
                {"name": "Novo ID (Grupo)", "value": f"`{new_id}`", "inline": True}
            ],
            "footer": {"text": "Enviado via AssetManager 3.0"}
        }

        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                requests.post(WEBHOOK_URL, 
                    data={"payload_json": json.dumps({"embeds": [embed]})},
                    files={"file": (file_path, f)}
                )

if __name__ == "__main__":
    main()
