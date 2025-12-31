import requests
import os
import json
import time

# Configurações do Ambiente
API_KEY = os.getenv("RBX_API_KEY")
MY_GROUP_ID = "633516837"
UNIVERSE_ID = "9469723620"
PUBLISHER_ID = "1162850942" # ID do usuário/grupo com permissão fornecido
EVENT_PATH = os.getenv("GITHUB_EVENT_PATH")

ADMIN_WEBHOOK = "https://discord.com/api/webhooks/1453805636784488509/6tdAXTB0DqdiWaLTmi05bWWDnTDk9mGLhmDFVTXgiL48yVKcOpN_at22DtCY8SotPvn1"

def get_asset_thumbnail(asset_id):
    if asset_id == "N/A": return None
    url = f"https://thumbnails.roblox.com/v1/assets?assetIds={asset_id}&returnPolicy=PlaceHolder&size=420x420&format=png"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get("data"): return data["data"][0].get("imageUrl")
    except: pass
    return None

def publish_asset(asset_id):
    """Tenta forçar a publicação do item na Creator Store."""
    print(f"🔧 Tentando publicar Asset {asset_id}...")
    url = f"https://apis.roblox.com/assets/v1/assets/{asset_id}"
    
    # Payload para tornar o item público e gratuito
    payload = {
        "description": "Publicado via Asset Manager 4.0",
        "isPublicDomain": True  # Isso tenta ativar o 'Obter Modelo'
    }
    
    headers = {
        "x-api-key": API_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        # Usamos PATCH para atualizar as permissões do asset existente
        response = requests.patch(url, headers=headers, json=payload)
        if response.status_code == 200:
            print("✅ Publicação solicitada com sucesso!")
            return True
        else:
            print(f"⚠️ Falha na publicação: {response.text}")
            return False
    except Exception as e:
        print(f"❌ Erro ao conectar na API de Assets: {e}")
        return False

def notify_roblox(status, asset_id="N/A", target_user_id="0"):
    url = f"https://apis.roblox.com/messaging-service/v1/universes/{UNIVERSE_ID}/topics/AssetUploadFeedback"
    data = {"message": json.dumps({"playerId": str(target_user_id), "status": status, "assetId": str(asset_id)})}
    try: requests.post(url, headers={"x-api-key": API_KEY, "Content-Type": "application/json"}, json=data)
    except: pass

def main():
    print("🚀 Iniciando processo...")
    if not EVENT_PATH: return

    try:
        with open(EVENT_PATH, 'r') as f:
            payload = json.load(f).get("client_payload", {})
    except: return

    PLAYER_WEBHOOK = payload.get("discord_webhook")
    ORIGINAL_ID = payload.get("asset_id")
    PLAYER_NAME = payload.get("player_name", "Unknown")
    TARGET_USER_ID = payload.get("target_user_id", "0")

    # 1. Download
    file_path = "item.rbxm"
    r_down = requests.get(f"https://assetdelivery.roblox.com/v1/asset/?id={ORIGINAL_ID}")
    if r_down.status_code != 200: return
    with open(file_path, "wb") as f: f.write(r_down.content)

    # 2. Upload
    url = "https://apis.roblox.com/assets/v1/assets"
    asset_config = {
        "assetType": "Model",
        "displayName": f"Asset_{ORIGINAL_ID}",
        "description": f"Exported for {PLAYER_NAME}",
        "creationContext": {"creator": {"groupId": str(MY_GROUP_ID)}}
    }
    
    with open(file_path, "rb") as f:
        files = {
            "request": (None, json.dumps(asset_config), "application/json"),
            "fileContent": ("model.rbxm", f, "model/x-rbxm")
        }
        response = requests.post(url, headers={"x-api-key": API_KEY}, files=files)

    if response.status_code != 200:
        notify_roblox("error", target_user_id=TARGET_USER_ID)
        return

    operation_path = response.json().get("path")
    final_asset_id = "N/A"
    
    # 3. Polling
    for i in range(10):
        time.sleep(3)
        op_res = requests.get(f"https://apis.roblox.com/assets/v1/{operation_path}", headers={"x-api-key": API_KEY})
        op_data = op_res.json()
        if op_data.get("done"):
            final_asset_id = op_data.get("response", {}).get("assetId", "N/A")
            break

    # 4. FORÇAR PUBLICAÇÃO
    publish_success = False
    if final_asset_id != "N/A":
        publish_success = publish_asset(final_asset_id)

    # 5. Webhooks
    thumbnail_url = get_asset_thumbnail(final_asset_id)
    status_text = "✅ Success (Public)" if publish_success else "✅ Success (Private/Pending)"
    
    embed_payload = {
        "embeds": [{
            "title": "📦 Asset Processed!",
            "description": f"Wsp **{PLAYER_NAME}**! Your request has been processed.",
            "color": 3066993 if final_asset_id != "N/A" else 15158332,
            "fields": [
                {"name": "Status", "value": status_text, "inline": True},
                {"name": "Final ID", "value": f"[{final_asset_id}](https://www.roblox.com/library/{final_asset_id})", "inline": True},
                {"name": "Player", "value": PLAYER_NAME, "inline": True}
            ],
            "image": {"url": thumbnail_url} if thumbnail_url else {},
            "footer": {"text": "Sent via AssetManager 4.0"}
        }]
    }

    for target in filter(None, [ADMIN_WEBHOOK, PLAYER_WEBHOOK]):
        try: requests.post(target, json=embed_payload)
        except: pass

    notify_roblox("success" if final_asset_id != "N/A" else "error", final_asset_id, TARGET_USER_ID)

if __name__ == "__main__":
    main()
