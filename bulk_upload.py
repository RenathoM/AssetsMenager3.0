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
        r = requests.get(url)
        if r.status_code == 200:
            data = r.json()
            if data.get("data"): return data["data"][0].get("imageUrl")
    except: pass
    return None

def publish_asset(asset_id):
    """Ativa o botão 'Obter Modelo'."""
    url = f"https://apis.roblox.com/assets/v1/assets/{asset_id}"
    try:
        r = requests.patch(url, headers={"x-api-key": API_KEY}, json={"isPublicDomain": True})
        return r.status_code == 200
    except: return False

def main():
    print("🚀 Iniciando processo de upload...")
    if not EVENT_PATH: return

    # 1. Carregar Dados do Evento
    try:
        with open(EVENT_PATH, 'r') as f:
            payload = json.load(f).get("client_payload", {})
    except: return

    PLAYER_WEBHOOK = payload.get("discord_webhook")
    ORIGINAL_ID = payload.get("asset_id")
    PLAYER_NAME = payload.get("player_name", "Unknown")
    TARGET_USER_ID = payload.get("target_user_id", "0")

    # 2. Download Robusto
    file_path = "item.rbxm"
    print(f"📥 Baixando {ORIGINAL_ID}...")
    r_down = requests.get(f"https://apis.roblox.com/assets/v1/assets/{ORIGINAL_ID}", headers={"x-api-key": API_KEY})
    
    if r_down.status_code != 200:
        print(f"❌ Erro Download: {r_down.status_code}")
        return
        
    with open(file_path, "wb") as f:
        f.write(r_down.content)
    print("✅ Download concluído.")

    # 3. Upload com Multipart/Form-Data correto
    asset_config = {
        "assetType": "Model",
        "displayName": f"Asset_{ORIGINAL_ID}",
        "description": f"Exported for {PLAYER_NAME}",
        "creationContext": {"creator": {"groupId": str(MY_GROUP_ID)}}
    }
    
    # Abrimos o arquivo aqui para garantir que ele seja lido do zero
    with open(file_path, "rb") as model_file:
        files = {
        "request": (None, json.dumps(asset_config), "application/json"),
        "fileContent": ("model.rbxm", model_file, "application/octet-stream") # Alterado para stream genérico
    }
        print("⚙️ Enviando para Roblox...")
        response = requests.post("https://apis.roblox.com/assets/v1/assets", 
                                 headers={"x-api-key": API_KEY}, 
                                 files=files)
        
    if response.status_code != 200:
        print(f"❌ Erro Upload: {response.text}")
        return

    operation_path = response.json().get("path")
    final_asset_id = "N/A"
    error_detail = "Roblox rejected content"

    # 4. Polling (Aguardando processamento)
    for i in range(12):
        time.sleep(4)
        print(f"⏱️ Verificando status {i+1}...")
        op_res = requests.get(f"https://apis.roblox.com/assets/v1/{operation_path}", headers={"x-api-key": API_KEY})
        if op_res.status_code == 200:
            op_data = op_res.json()
            if op_data.get("done"):
                if "response" in op_data:
                    final_asset_id = op_data["response"].get("assetId", "N/A")
                    print(f"✅ Sucesso! ID: {final_asset_id}")
                else:
                    error_detail = op_data.get("error", {}).get("message", "Invalid Content")
                    print(f"❌ Erro no processamento: {error_detail}")
                break

    # 5. Publicação e Feedback
    publish_asset(final_asset_id) if final_asset_id != "N/A" else None
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
        requests.post(target, json=embed)

if __name__ == "__main__":
    main()
