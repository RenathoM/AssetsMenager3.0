import requests
import os
import json
import time

# Configurações do Ambiente
API_KEY = os.getenv("RBX_API_KEY")
MY_GROUP_ID = "633516837"
UNIVERSE_ID = "103111986841337"
event_path = os.getenv("GITHUB_EVENT_PATH")

with open(event_path, 'r') as f:
    payload = json.load(f).get("client_payload", {})

WEBHOOK_URL = payload.get("discord_webhook")
ORIGINAL_ID = payload.get("asset_id")
PLAYER_NAME = payload.get("player_name", "Unknown")
TARGET_USER_ID = payload.get("target_user_id")

def notify_roblox(status, asset_id="N/A"):
    """ Envia o feedback para o jogo via MessagingService """
    url = f"https://apis.roblox.com/messaging-service/v1/universes/{UNIVERSE_ID}/topics/AssetUploadFeedback"
    data = {
        "message": json.dumps({
            "playerId": TARGET_USER_ID,
            "status": status,
            "assetId": asset_id
        })
    }
    requests.post(url, headers={"x-api-key": API_KEY, "Content-Type": "application/json"}, json=data)

def main():
    file_path = "item.rbxm"
    
    # 1. Download do Asset Original
    r_down = requests.get(f"https://assetdelivery.roblox.com/v1/asset/?id={ORIGINAL_ID}")
    if r_down.status_code == 200:
        with open(file_path, "wb") as f:
            f.write(r_down.content)
    else:
        notify_roblox("error")
        return

    # 2. Upload para o Roblox
    url = "https://apis.roblox.com/assets/v1/assets"
    
    asset_config = {
        "assetType": "Model",
        "displayName": f"Asset_{ORIGINAL_ID}",
        "description": "Exported via AssetManager 4.0",
        "creationContext": {
            "creator": {"groupId": str(MY_GROUP_ID)}
        }
    }
    
    with open(file_path, "rb") as f:
        # A chave aqui é o Content-Type 'application/octet-stream' 
        # e garantir que o nome do arquivo termine em .rbxm
        files = {
            "request": (None, json.dumps(asset_config), "application/json"),
            "fileContent": ("model.rbxm", f, "application/octet-stream")
        }
        
        response = requests.post(
            url, 
            headers={"x-api-key": API_KEY}, 
            files=files
        )
    
    with open(file_path, "rb") as f:
        files = {
            "request": (None, json.dumps(asset_config), "application/json"),
            "fileContent": (file_path, f, "model/x-rbxm")
        }
        response = requests.post(url, headers={"x-api-key": API_KEY}, files=files)
    
    res_data = response.json()
    operation_path = res_data.get("path")
    final_asset_id = "N/A"

    # 3. Polling para obter o ID Final
    if operation_path:
        for _ in range(15):
            time.sleep(2)
            op_res = requests.get(f"https://apis.roblox.com/assets/v1/{operation_path}", headers={"x-api-key": API_KEY})
            op_data = op_res.json()
            if op_data.get("done"):
                final_asset_id = op_data.get("response", {}).get("assetId", "N/A")
                break
    
    success = final_asset_id != "N/A"
    
    # 4. Envio para o Discord com Link Automático
    if WEBHOOK_URL:
        # Criação do link no formato Markdown solicitado
        roblox_url = f"https://www.roblox.com/library/{final_asset_id}"
        display_id = f"[{final_asset_id}]({roblox_url})" if success else "`N/A`"

        embed = {
            "title": "📦 Asset Processed!",
            "description": f"Wsp **{PLAYER_NAME}**! Your request has been processed.",
            "color": 3066993 if success else 15158332,
            "fields": [
                {"name": "Status", "value": "✅ Success" if success else "❌ Failed", "inline": True},
                {"name": "Final ID", "value": display_id, "inline": True},
                {"name": "Player", "value": PLAYER_NAME, "inline": True}
            ],
            "footer": {"text": "Sent via AssetManager 4.0"}
        }
        requests.post(WEBHOOK_URL, json={"embeds": [embed]})

    # 5. Notifica o Jogo
    notify_roblox("success" if success else "error", final_asset_id)

if __name__ == "__main__":
    main()
