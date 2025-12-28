import requests
import os
import json

# ... (mantenha as variáveis de ambiente anteriores)
WEBHOOK_URL = "SUA_URL_DO_WEBHOOK_AQUI" # Ou envie via client_payload do Roblox

def send_to_discord(asset_name, asset_id, player_name):
    payload = {
        "content": f"# ✅ Asset Carregado!\n**Nome:** {asset_name}\n**ID:** {asset_id}\n**Enviado por:** {player_name}",
        "username": "Roblox Cloud Bot"
    }
    requests.post(WEBHOOK_URL, json=payload)

def upload_assets():
    for filename in os.listdir(ASSET_FOLDER):
        # ... (lógica de upload)
        response = requests.post(url, headers=headers, files=files)
        
        if response.status_code == 200:
            data = response.json()
            # O ID do asset só aparece aqui após o upload terminar!
            asset_id = data.get("assetId") 
            send_to_discord(filename, asset_id, PLAYER_NAME)
            
            # Avisa o Roblox que o ID X foi gerado
            feedback_url = f"https://apis.roblox.com/messaging-service/v1/universes/{EXPERIMENT_ID}/topics/AssetUploadFeedback"
            requests.post(feedback_url, headers=headers, json={"message": f"Asset {filename} pronto! ID: {asset_id}"})