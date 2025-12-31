import requests
import os
import json
import time

# Configurações do Ambiente
API_KEY = os.getenv("RBX_API_KEY")
MY_GROUP_ID = "633516837"
UNIVERSE_ID = "9469723620"
event_path = os.getenv("GITHUB_EVENT_PATH")

with open(event_path, 'r') as f:
    payload = json.load(f).get("client_payload", {})

WEBHOOK_URL = payload.get("discord_webhook")
ORIGINAL_ID = payload.get("asset_id")
PLAYER_NAME = payload.get("player_name", "Unknown")
TARGET_USER_ID = payload.get("target_user_id")

def distribute_asset(asset_id):
    """ Tenta tornar o asset público na Creator Store """
    url = f"https://apis.roblox.com/assets/v1/assets/{asset_id}"
    # O Roblox exige que o asset seja 'Public' para aparecer na loja
    data = {"isPublic": True}
    headers = {"x-api-key": API_KEY, "Content-Type": "application/json"}
    try:
        res = requests.patch(url, headers=headers, json=data)
        return res.status_code == 200
    except:
        return False

def notify_roblox(status, asset_id="N/A"):
    url = f"https://apis.roblox.com/messaging-service/v1/universes/{UNIVERSE_ID}/topics/AssetUploadFeedback"
    data = {
        "message": json.dumps({
            "playerId": str(TARGET_USER_ID),
            "status": status,
            "assetId": str(asset_id)
        })
    }
    requests.post(url, headers={"x-api-key": API_KEY, "Content-Type": "application/json"}, json=data)

def main():
    print("🚀 Script iniciado...")
    file_path = "item.rbxm"
    
    print(f"📦 Verificando Asset ID: {ORIGINAL_ID}")
    # 1. Download do Asset Original
    r_down = requests.get(f"https://assetdelivery.roblox.com/v1/asset/?id={ORIGINAL_ID}")
    print(f"🌐 Status do Download: {r_down.status_code}")
    
    if r_down.status_code == 200:
        with open(file_path, "wb") as f:
            f.write(r_down.content)
        print("✅ Arquivo salvo com sucesso.")
    else:
        print("❌ Erro ao baixar asset da Roblox.")
        return

    # 2. Upload para o Grupo
    url = "https://apis.roblox.com/assets/v1/assets"
    asset_config = {
        "assetType": "Model",
        "displayName": f"Asset_{ORIGINAL_ID}",
        "description": f"Criado para {PLAYER_NAME}",
        "creationContext": {"creator": {"groupId": str(MY_GROUP_ID)}}
    }
    
    with open(file_path, "rb") as f:
        files = {
            "request": (None, json.dumps(asset_config), "application/json"),
            "fileContent": ("model.rbxm", f, "application/octet-stream")
        }
        response = requests.post(url, headers={"x-api-key": API_KEY}, files=files)
    
    if response.status_code != 200:
        return

    operation_path = response.json().get("path")
    final_asset_id = "N/A"

    # 3. Esperar Processamento (Polling)
    if operation_path:
        for _ in range(15):
            time.sleep(2)
            op_res = requests.get(f"https://apis.roblox.com/assets/v1/{operation_path}", headers={"x-api-key": API_KEY})
            if op_res.status_code == 200 and op_res.json().get("done"):
                final_asset_id = op_res.json().get("response", {}).get("assetId", "N/A")
                break

    if final_asset_id != "N/A":
        # 4. TENTAR TORNAR PÚBLICO (Creator Store)
        was_distributed = distribute_asset(final_asset_id)
        print(f"ASSET_ID={final_asset_id}")
        
        # Enviar para o Discord
        if WEBHOOK_URL:
            status_txt = "✅ Público na Loja" if was_distributed else "⚠️ Criado no Grupo (Privado)"
            embed = {
                "title": "📦 Novo Asset Disponível!",
                "description": f"Jogador: {PLAYER_NAME}\nStatus: {status_txt}",
                "url": f"https://www.roblox.com/library/{final_asset_id}",
                "color": 3066993 if was_distributed else 15158332
            }
            requests.post(WEBHOOK_URL, json={"embeds": [embed]})
        
        notify_roblox("success", final_asset_id)
    else:
        notify_roblox("error")

if __name__ == "__main__":
    main()
