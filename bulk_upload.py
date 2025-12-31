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

def get_asset_thumbnail(asset_id):
    if not asset_id or asset_id == "N/A": return None
    url = f"https://thumbnails.roblox.com/v1/assets?assetIds={asset_id}&returnPolicy=PlaceHolder&size=420x420&format=png"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            if data.get("data"): return data["data"][0].get("imageUrl")
    except: pass
    return None

def notify_roblox(status, asset_id="N/A", target_user_id="0"):
    """Envia feedback via Messaging Service com proteção contra falhas."""
    url = f"https://apis.roblox.com/messaging-service/v1/universes/{UNIVERSE_ID}/topics/AssetUploadFeedback"
    data = {"message": json.dumps({"playerId": str(target_user_id), "status": status, "assetId": str(asset_id)})}
    try:
        requests.post(url, headers={"x-api-key": API_KEY, "Content-Type": "application/json"}, json=data, timeout=10)
    except: pass

def main():
    print("🚀 Iniciando processo de upload...")
    if not EVENT_PATH: sys.exit(0)

    try:
        with open(EVENT_PATH, 'r') as f:
            payload = json.load(f).get("client_payload", {})
    except: sys.exit(0)

    PLAYER_WEBHOOK = payload.get("discord_webhook")
    ORIGINAL_ID = payload.get("asset_id")
    PLAYER_NAME = payload.get("player_name", "Unknown")
    TARGET_USER_ID = payload.get("target_user_id", "0")

    # 1. Download Autenticado
    file_path = "item.rbxm"
    try:
        r_down = requests.get(f"https://apis.roblox.com/assets/v1/assets/{ORIGINAL_ID}", headers={"x-api-key": API_KEY}, timeout=30)
        if r_down.status_code == 200:
            with open(file_path, "wb") as f: f.write(r_down.content)
            print("✅ Download concluído.")
        else:
            print(f"❌ Erro Download: {r_down.status_code}")
            notify_roblox("error", target_user_id=TARGET_USER_ID)
            sys.exit(0)
    except: sys.exit(0)

    # 2. Upload para Roblox
    asset_config = {
        "assetType": "Model",
        "displayName": f"Asset_{ORIGINAL_ID}",
        "description": f"Exported for {PLAYER_NAME}",
        "creationContext": {"creator": {"groupId": str(MY_GROUP_ID)}}
    }
    
    try:
        with open(file_path, "rb") as f:
            files = {
                "request": (None, json.dumps(asset_config), "application/json"),
                "fileContent": ("model.rbxm", f, "model/x-rbxm")
            }
            response = requests.post("https://apis.roblox.com/assets/v1/assets", headers={"x-api-key": API_KEY}, files=files, timeout=60)

        if response.status_code != 200:
            notify_roblox("error", target_user_id=TARGET_USER_ID)
            sys.exit(0)

        operation_path = response.json().get("path")
    except: sys.exit(0)

    # 3. Polling (Aguardando processamento)
    final_asset_id = "N/A"
    error_detail = "Unknown error"
    for i in range(12):
        time.sleep(5)
        print(f"⏱️ Verificando status (tentativa {i+1})...")
        try:
            op_res = requests.get(f"https://apis.roblox.com/assets/v1/{operation_path}", headers={"x-api-key": API_KEY}, timeout=15)
            if op_res.status_code == 200:
                op_data = op_res.json()
                if op_data.get("done"):
                    if "response" in op_data:
                        final_asset_id = op_data["response"].get("assetId", "N/A")
                        print(f"✅ Sucesso! Novo ID: {final_asset_id}")
                    else:
                        error_detail = op_data.get("error", {}).get("message", "Invalid Content")
                        print(f"❌ Erro: {error_detail}")
                    break
        except: pass

    # 4. Feedback via Webhook
    thumb = get_asset_thumbnail(final_asset_id)
    status_msg = "✅ Success" if final_asset_id != "N/A" else f"❌ Failed: {error_detail}"
    embed = {
        "embeds": [{
            "title": "📦 Asset Processado!",
            "description": f"Wsp **{PLAYER_NAME}**! Your request has been processed.",
            "color": 3066993 if final_asset_id != "N/A" else 15158332,
            "fields": [
                {"name": "Status", "value": status_msg, "inline": False},
                {"name": "Final ID", "value": f"[{final_asset_id}](https://www.roblox.com/library/{final_asset_id})" if final_asset_id != "N/A" else "N/A", "inline": True},
                {"name": "Player", "value": PLAYER_NAME, "inline": True}
            ],
            "image": {"url": thumb} if thumb else {},
            "footer": {"text": "Sent via AssetManager 4.0"}
        }]
    }

    for target in filter(None, [ADMIN_WEBHOOK, PLAYER_WEBHOOK]):
        try: requests.post(target, json=embed, timeout=10)
        except: pass

    notify_roblox("success" if final_asset_id != "N/A" else "error", final_asset_id, TARGET_USER_ID)
    print("🏁 Processo finalizado com sucesso.")
    sys.exit(0)

if __name__ == "__main__":
    main()
