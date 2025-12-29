import requests
import os
import json

# Carrega os dados enviados pelo Roblox
event_json = os.getenv("GITHUB_EVENT_PAYLOAD", "{}")
payload = json.loads(event_json).get("client_payload", {})

# CONFIGURAÇÃO ÚNICA DO DESENVOLVEDOR (SÓ VOCÊ PRECISA DISSO)
API_KEY = os.getenv("ROBLOX_API_KEY")
MY_USER_ID = "1095837550" 
WEBHOOK_URL = payload.get("discord_webhook")

def main():
    # Detecta o arquivo no repositório
    file_path = "assets.rbxm" if os.path.exists("assets.rbxm") else "default.rbxm"
    msg = "Processado com sucesso!"
    new_id = "N/A"

    try:
        # 1. Faz o upload para a SUA conta (Fábrica)
        url = "https://apis.roblox.com/assets/v1/assets"
        asset_config = {
            "assetType": "Model",
            "displayName": f"Export_{payload.get('asset_id')}",
            "creationContext": {"creator": {"userId": str(MY_USER_ID)}}
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
                msg = f"Erro no Upload: {response.status_code}"

    except Exception as e:
        msg = f"Erro Crítico: {str(e)}"

    # 2. ENTREGA FINAL PERSONALIZADA NO DISCORD DO JOGADOR
    if WEBHOOK_URL:
        embed = {
            "title": "📦 Your Asset Is Ready!",
            "description": f"Olá **{payload.get('player_name')}**, seu arquivo foi gerado!",
            "color": 3066993, # Verde
            "fields": [
                {"name": "ID Original", "value": f"`{payload.get('asset_id')}`", "inline": True},
                {"name": "Novo ID (Gerado)", "value": f"`{new_id}`", "inline": True}
            ],
            "footer": {"text": "Enviado via AssetManager 3.0"}
        }

        # Envia o arquivo físico + a mensagem bonita
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                requests.post(WEBHOOK_URL, 
                    data={"payload_json": json.dumps({"embeds": [embed]})},
                    files={"file": (file_path, f)}
                )
