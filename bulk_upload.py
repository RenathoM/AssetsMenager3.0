import requests
import os
import json
import time

# Configurações do Ambiente
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE")
API_KEY = os.getenv("RBX_API_KEY") 
MY_GROUP_ID = "633516837"
UNIVERSE_ID = "9469723620"
EVENT_PATH = os.getenv("GITHUB_EVENT_PATH")

ADMIN_WEBHOOK = "https://discord.com/api/webhooks/1453805636784488509/6tdAXTB0DqdiWaLTmi05bWWDnTDk9mGLhmDFVTXgiL48yVKcOpN_at22DtCY8SotPvn1"

def set_asset_public(asset_id, headers):
    """Tenta tornar o asset público e gratuito usando o escopo Creator Store."""
    # Usando a API de Creator Store que corresponde ao escopo 'creator-store-products:write'
    url = f"https://apis.roblox.com/creator-store-products/v1/assets/{asset_id}"
    
    payload = {
        "status": "Published",
        "price": 0
    }
    
    try:
        # Patch é usado para atualizar configurações de produtos existentes
        response = requests.patch(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            print(f"💰 Asset {asset_id} publicado na Creator Store com sucesso (Grátis).")
        else:
            # Segunda tentativa: Tentar via Asset Permissions para garantir acesso
            print(f"⚠️ Creator Store falhou ({response.status_code}). Tentando permissões de acesso...")
            perm_url = f"https://apis.roblox.com/assets/v1/assets/{asset_id}/permissions"
            perm_payload = {"action": "Public"} # Tenta tornar o modelo copiável
            requests.patch(perm_url, headers=headers, json=perm_payload, timeout=5)
            
    except Exception as e:
        print(f"⚠️ Erro ao tentar habilitar venda: {e}")

def get_csrf_token():
    if not ROBLOX_COOKIE: return None
    headers = {"Cookie": f".ROBLOSECURITY={ROBLOX_COOKIE}"}
    try:
        response = requests.post("https://auth.roblox.com/v2/logout", headers=headers, timeout=10)
        return response.headers.get("x-csrf-token")
    except: return None

def get_asset_thumbnail(asset_id):
    if not asset_id or asset_id == "N/A": return None
    url = f"https://thumbnails.roblox.com/v1/assets?assetIds={asset_id}&returnPolicy=PlaceHolder&size=420x420&format=png"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("data") and len(data["data"]) > 0:
                return data["data"][0].get("imageUrl")
    except: pass
    return None

def main():
    if not EVENT_PATH: return
    try:
        with open(EVENT_PATH, 'r') as f:
            event_data = json.load(f)
            payload = event_data.get("client_payload", {})
    except: return

    PLAYER_WEBHOOK = payload.get("discord_webhook")
    ORIGINAL_ID = payload.get("asset_id")
    PLAYER_NAME = payload.get("player_name", "Unknown")

    file_path = "item.rbxm"
    r_down = requests.get(f"https://assetdelivery.roblox.com/v1/asset/?id={ORIGINAL_ID}")
    if r_down.status_code == 200:
        with open(file_path, "wb") as f: f.write(r_down.content)
    else: return

    headers = {}
    csrf = get_csrf_token()
    if csrf:
        headers = {"Cookie": f".ROBLOSECURITY={ROBLOX_COOKIE}", "x-csrf-token": csrf}
    elif API_KEY:
        headers = {"x-api-key": API_KEY}
    else: return

    url = "https://apis.roblox.com/assets/v1/assets"
    asset_config = {
        "assetType": "Model",
        "displayName": f"Asset_{ORIGINAL_ID}",
        "description": f"Public model for {PLAYER_NAME}. Free to use.",
        "creationContext": {"creator": {"groupId": str(MY_GROUP_ID)}}
    }
    
    with open(file_path, "rb") as f:
        files = {
            "request": (None, json.dumps(asset_config), "application/json"),
            "fileContent": ("model.rbxm", f, "model/x-rbxm")
        }
        response = requests.post(url, headers=headers, files=files)

    final_asset_id = "N/A"
    if response.status_code == 200:
        operation_path = response.json().get("path")
        for i in range(15):
            time.sleep(3)
            op_res = requests.get(f"https://apis.roblox.com/assets/v1/{operation_path}", headers=headers)
            if op_res.status_code == 200:
                op_data = op_res.json()
                if op_data.get("done"):
                    final_asset_id = op_data.get("response", {}).get("assetId", "N/A")
                    print(f"✅ Sucesso! ASSET_ID={final_asset_id}")
                    
                    # TENTA HABILITAR A VENDA (Se falhar, o script continua)
                    set_asset_public(final_asset_id, headers)
                    break

    # Webhooks
    thumb_original = get_asset_thumbnail(ORIGINAL_ID)
    store_link = f"https://create.roblox.com/store/asset/{final_asset_id}"
    display_id = f"[{final_asset_id}]({store_link})" if final_asset_id != "N/A" else "`N/A`"
    
    embed_payload = {
        "embeds": [{
            "title": "📦 Asset Processed!",
            "description": f"Wsp **{PLAYER_NAME}**! Your request has been processed.",
            "color": 3066993 if final_asset_id != "N/A" else 15158332,
            "fields": [
                {"name": "Status", "value": "✅ Success" if final_asset_id != "N/A" else "❌ Failed", "inline": True},
                {"name": "Final ID (Click to Get)", "value": display_id, "inline": True},
                {"name": "Player", "value": PLAYER_NAME, "inline": True}
            ],
            "image": {"url": thumb_original} if thumb_original else {},
            "footer": {"text": "Public Asset - Store Ready"}
        }]
    }

    for webhook_url in [ADMIN_WEBHOOK, PLAYER_WEBHOOK]:
        if webhook_url: requests.post(webhook_url, json=embed_payload)

if __name__ == "__main__":
    main()
