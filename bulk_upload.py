import requests
import os
import json
import time
import sys

# Configurações do Ambiente
API_KEY = os.getenv("RBX_API_KEY")
MY_GROUP_ID = "633516837"
UNIVERSE_ID = "9469723620"
EVENT_PATH = os.getenv("GITHUB_EVENT_PATH")
ADMIN_WEBHOOK = "https://discord.com/api/webhooks/1453805636784488509/6tdAXTB0DqdiWaLTmi05bWWDnTDk9mGLhmDFVTXgiL48yVKcOpN_at22DtCY8SotPvn1"

def safe_request(func, *args, **kwargs):
    """Executa requisições de forma segura com timeout."""
    try:
        kwargs['timeout'] = kwargs.get('timeout', 15)
        return func(*args, **kwargs)
    except:
        return None

def get_thumbnail(asset_id):
    if not asset_id or asset_id == "N/A": return None
    url = f"https://thumbnails.roblox.com/v1/assets?assetIds={asset_id}&returnPolicy=PlaceHolder&size=420x420&format=png"
    r = safe_request(requests.get, url)
    if r and r.status_code == 200:
        data = r.json()
        if data.get("data"): return data["data"][0].get("imageUrl")
    return None

def notify_roblox(status, asset_id="N/A", player_id="0"):
    url = f"https://apis.roblox.com/messaging-service/v1/universes/{UNIVERSE_ID}/topics/AssetUploadFeedback"
    data = {"message": json.dumps({"playerId": str(player_id), "status": status, "assetId": str(asset_id)})}
    safe_request(requests.post, url, headers={"x-api-key": API_KEY, "Content-Type": "application/json"}, json=data)

def main():
    print("🚀 Iniciando processo de upload...")
    if not EVENT_PATH or not os.path.exists(EVENT_PATH): sys.exit(0)

    try:
        with open(EVENT_PATH, 'r') as f:
            payload = json.load(f).get("client_payload", {})
    except: sys.exit(0)

    PLAYER_WEBHOOK = payload.get("discord_webhook")
    ORIGINAL_ID = payload.get("asset_id")
    PLAYER_NAME = payload.get("player_name", "Unknown")
    TARGET_ID = payload.get("target_user_id", "0")

    # 1. Download
    file_path = "item.rbxm"
    r_down = safe_request(requests.get, f"https://apis.roblox.com/assets/v1/assets/{ORIGINAL_ID}", headers={"x-api-key": API_KEY})
    if not r_down or r_down.status_code != 200:
        notify_roblox("error", player_id=TARGET_ID)
        sys.exit(0)
    
    with open(file_path, "wb") as f: f.write(r_down.content)

    # 2. Upload
    asset_config = {
        "assetType": "Model",
        "displayName": f"Asset_{ORIGINAL_ID}",
        "description": f"Exported for {PLAYER_NAME}",
        "creationContext": {"creator": {"groupId": str(MY_GROUP_ID)}}
    }
    
    with open(file_path, "rb") as f:
        files = {"request": (None, json.dumps(asset_config), "application/json"), "fileContent": ("model.rbxm", f, "model/x-rbxm")}
        r_up = safe_request(requests.post, "https://apis.roblox.com/assets/v1/assets", headers={"x-api-key": API_KEY}, files=files, timeout=60)

    if not r_up or r_up.status_code != 200:
        notify_roblox("error", player_id=TARGET_ID)
        sys.exit(0)

    op_path = r_up.json().get("path")
    final_id = "N/A"
    err = "Processing failed"

    # 3. Polling
    for _ in range(12):
        time.sleep(5)
        r_op = safe_request(requests.get, f"https://apis.roblox.com/assets/v1/{op_path}", headers={"x-api-key": API_KEY})
        if r_op and r_op.status_code == 200:
            data = r_op.json()
            if data.get("done"):
                if "response" in data:
                    final_id = data["response"].get("assetId", "N/A")
                else:
                    err = data.get("error", {}).get("message", "Invalid Content")
                break

    # 4. Notificações
    thumb = get_thumbnail(final_id)
    embed = {
        "embeds": [{
            "title": "📦 Asset Processed!",
            "description": f"Wsp **{PLAYER_NAME}**! Your request has been processed.",
            "color": 3066993 if final_id != "N/A" else 15158332,
            "fields": [
                {"name": "Status", "value": "✅ Success" if final_id != "N/A" else f"❌ Failed: {err}", "inline": False},
                {"name": "Final ID", "value": f"[{final_id}](https://www.roblox.com/library/{final_id})" if final_id != "N/A" else "N/A", "inline": True},
                {"name": "Player", "value": PLAYER_NAME, "inline": True}
            ],
            "image": {"url": thumb} if thumb else {},
            "footer": {"text": "Sent via AssetManager 4.0"}
        }]
    }

    for target in filter(None, [ADMIN_WEBHOOK, PLAYER_WEBHOOK]):
        safe_request(requests.post, target, json=embed)

    notify_roblox("success" if final_id != "N/A" else "error", final_id, TARGET_ID)
    print("🏁 Processo finalizado com sucesso.")
    sys.exit(0)

if __name__ == "__main__":
    main()
