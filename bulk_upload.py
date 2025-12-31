import requests
import os
import json
import time

# Configurações do Ambiente
API_KEY = os.getenv("RBX_API_KEY")
MY_GROUP_ID = "633516837"
UNIVERSE_ID = "9469723620"
EVENT_PATH = os.getenv("GITHUB_EVENT_PATH")
ADMIN_WEBHOOK = "https://discord.com/api/webhooks/1453805636784488509/6tdAXTB0DqdiWaLTmi05bWWDnTDk9mGLhmDFVTXgiL48yVKcOpN_at22DtCY8SotPvn1"

def get_asset_thumbnail(asset_id):
    if not asset_id or asset_id == "N/A": return None
    url = f"https://thumbnails.roblox.com/v1/assets?assetIds={asset_id}&returnPolicy=PlaceHolder&size=420x420&format=png"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get("data"): return data["data"][0].get("imageUrl")
    except: pass
    return None

def publish_asset(asset_id):
    """Tenta forçar a publicação do modelo."""
    url = f"https://apis.roblox.com/assets/v1/assets/{asset_id}"
    payload = {"isPublicDomain": True}
    try:
        r = requests.patch(url, headers={"x-api-key": API_KEY}, json=payload)
        return r.status_code == 200
    except: return False

def notify_roblox(status, asset_id="N/A", target_user_id="0"):
    url = f"https://apis.roblox.com/messaging-service/v1/universes/{UNIVERSE_ID}/topics/AssetUploadFeedback"
    data = {"message": json.dumps({"playerId": str(target_user_id), "status": status, "assetId": str(asset_id)})}
    try: requests.post(url, headers={"x-api-key": API_KEY, "Content-Type": "application/json"}, json=data)
    except: pass

def main():
    print("🚀 Iniciando processo de upload...")
    if not EVENT_PATH: return

    try:
        with open(EVENT_PATH, 'r') as f:
            payload = json.load(f).get("client_payload", {})
    except: return

    PLAYER_WEBHOOK = payload.get("discord_webhook")
    ORIGINAL_ID = payload.get("asset_id")
    PLAYER_NAME = payload.get("player_name", "Unknown")
    TARGET_USER_ID = payload.get("target_user_id", "0")

    # 1. Download Autenticado
    file_path = "item.rbxm"
    r_down = requests.get(f"https://apis.roblox.com/assets/v1/assets/{ORIGINAL_ID}", headers={"x-api-key": API_KEY})
    if r_down.status_code == 200:
        with open(file_path, "wb") as f: f.write(r_down.content)
    else:
        print(f"❌ Erro Download: {r_down.status_code}")
        return

    # 2. Upload
    asset_config = {
        "assetType": "Model",
        "displayName": f"Asset_{ORIGINAL_ID}",
        "description": f"Exported for {PLAYER_NAME}",
        "creationContext": {"creator": {"groupId": str(MY_GROUP_ID)}}
    }
    
    files = {
        "request": (None, json.dumps(asset_config), "application/json"),
        "fileContent": ("model.rbxm", open(file_path, "rb"), "model/x-rbxm")
    }
    response = requests.post("https://apis.roblox.com/assets/v1/assets", headers={"x-api-key": API_KEY}, files=files)

    if response.status_code != 200:
        print(f"❌ Erro Upload: {response.text}")
        return

    operation_path = response.json().get("path")
    final_asset_id = "N/A"
    error_detail = "Unknown Error"

    # 3. Polling Melhorado (Verifica resposta real)
    for i in range(12): # Aumentado para 36 segundos total
        time.sleep(3)
        print(f"⏱️ Verificando status {i+1}...")
        op_res = requests.get(f"https://apis.roblox.com/assets/v1/{operation_path}", headers={"x-api-key": API_KEY})
        if op_res.status_code == 200:
            op_data = op_res.json()
            if op_data.get("done"):
                # Tenta pegar o ID da resposta de sucesso
                final_asset_id = op_data.get("response", {}).get("assetId", "N/A")
                if final_asset_id == "N/A":
                    # Se não houver ID, tenta capturar a mensagem de erro da Roblox
                    error_detail = op_data.get("error", {}).get("message", "Roblox rejected the asset")
                break

    # 4. Publicação e Webhook
    is_public = publish_asset(final_asset_id) if final_asset_id != "N/A" else False
    thumb = get_asset_thumbnail(final_asset_id)
    
    status_val = "✅ Success" if final_asset_id != "N/A" else f"❌ Failed: {error_detail}"
    color = 3066993 if final_asset_id != "N/A" else 15158332

    embed = {
        "embeds": [{
            "title": "📦 Asset Processed!",
            "description": f"Wsp **{PLAYER_NAME}**! Your request has been processed.",
            "color": color,
            "fields": [
                {"name": "Status", "value": status_val, "inline": False},
                {"name": "Final ID", "value": f"[{final_asset_id}](https://www.roblox.com/library/{final_asset_id})" if final_asset_id != "N/A" else "N/A", "inline": True},
                {"name": "Player", "value": PLAYER_NAME, "inline": True}
            ],
            "image": {"url": thumb} if thumb else {},
            "footer": {"text": "Sent via AssetManager 4.0"}
        }]
    }

    for target in filter(None, [ADMIN_WEBHOOK, PLAYER_WEBHOOK]):
        requests.post(target, json=embed)

    notify_roblox("success" if final_asset_id != "N/A" else "error", final_asset_id, TARGET_USER_ID)

if __name__ == "__main__":
    main()
