import requests
import os
import json
import time

# Configurações
API_KEY = os.getenv("RBX_API_KEY")
MY_GROUP_ID = "633516837"
event_path = os.getenv("GITHUB_EVENT_PATH")

with open(event_path, 'r') as f:
    payload = json.load(f).get("client_payload", {})

WEBHOOK_URL = payload.get("discord_webhook")
ORIGINAL_ID = payload.get("asset_id")
PLAYER_NAME = payload.get("player_name", "Unknown")
UNIVERSE_ID = "103111986841337" # ID da sua experiência

def notify_roblox(status, asset_id="N/A"):
    """ Envia o feedback de volta para o MessagingService do Roblox """
    url = f"https://apis.roblox.com/messaging-service/v1/universes/{UNIVERSE_ID}/topics/AssetUploadFeedback"
    data = {
        "message": json.dumps({
            "playerId": payload.get("target_user_id"),
            "status": status,
            "assetId": asset_id
        })
    }
    requests.post(url, headers={"x-api-key": API_KEY, "Content-Type": "application/json"}, json=data)

def main():
    file_path = "item.rbxm"
    
    # Download do Asset
    r_down = requests.get(f"https://assetdelivery.roblox.com/v1/asset/?id={ORIGINAL_ID}")
    with open(file_path, "wb") as f:
        f.write(r_down.content)

    # Upload Inicial
    url = "https://apis.roblox.com/assets/v1/assets"
    asset_config = {
        "assetType": "Model",
        "displayName": f"Asset_{ORIGINAL_ID}",
        "creationContext": {"creator": {"groupId": str(MY_GROUP_ID)}}
    }
    
    with open(file_path, "rb") as f:
        response = requests.post(url, headers={"x-api-key": API_KEY}, 
                                 files={"request": (None, json.dumps(asset_config), "application/json"),
                                        "fileContent": (file_path, f, "model/x-rbxm")})
    
    res_data = response.json()
    operation_path = res_data.get("path")
    final_asset_id = "N/A"

    # --- LÓGICA DE POLLING (CAPTURAR ID REAL) ---
    if operation_path:
        print("⏳ Aguardando processamento do ID final...")
        for _ in range(10): # Tenta por 20 segundos
            time.sleep(2)
            op_res = requests.get(f"https://apis.roblox.com/assets/v1/{operation_path}", headers={"x-api-key": API_KEY})
            op_data = op_res.json()
            if op_data.get("done"):
                final_asset_id = op_data.get("response", {}).get("assetId", "N/A")
                break
    
    # Sucesso ou Falha
    success = final_asset_id != "N/A"
    
    # 1. Notifica o Jogo (Messaging Service)
    notify_roblox("success" if success else "error", final_asset_id)
    
    # 2. Notifica o Discord (Apenas uma vez)
    if WEBHOOK_URL:
        embed = {
            "title": "📦 Asset Processed!",
            "color": 3066993 if success else 15158332,
            "fields": [
                {"name": "Status", "value": "✅ Success" if success else "❌ Failed"},
                {"name": "Final ID", "value": f"`{final_asset_id}`"},
                {"name": "Player", "value": PLAYER_NAME}
            ]
        }
        requests.post(WEBHOOK_URL, json={"embeds": [embed]})

if __name__ == "__main__":
    main()
