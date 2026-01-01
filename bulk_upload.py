import requests
import os
import json
import time

# Configurações do Ambiente
# Agora capturamos o Cookie definido no YAML do GitHub Actions
ROBLOX_COOKIE = os.getenv("ROBLOX_COOKIE") 
MY_GROUP_ID = "633516837" # [cite: 1]
UNIVERSE_ID = "9469723620" # [cite: 1]
EVENT_PATH = os.getenv("GITHUB_EVENT_PATH") # [cite: 1]

ADMIN_WEBHOOK = "https://discord.com/api/webhooks/1453805636784488509/6tdAXTB0DqdiWaLTmi05bWWDnTDk9mGLhmDFVTXgiL48yVKcOpN_at22DtCY8SotPvn1" # [cite: 1]

def get_csrf_token():
    """Obtém o x-csrf-token necessário para autenticação via Cookie."""
    headers = {"Cookie": f".ROBLOSECURITY={ROBLOX_COOKIE}"}
    # Enviamos uma requisição vazia para a API de autenticação para 'forçar' o recebimento do token
    response = requests.post("https://auth.roblox.com/v2/logout", headers=headers)
    token = response.headers.get("x-csrf-token")
    if not token:
        print("❌ Falha ao obter CSRF Token. Verifique se o Cookie é válido.")
    return token

def get_asset_thumbnail(asset_id):
    """Obtém a URL da imagem do asset via API de Thumbnails[cite: 1]."""
    if asset_id == "N/A":
        return None
    url = f"https://thumbnails.roblox.com/v1/assets?assetIds={asset_id}&returnPolicy=PlaceHolder&size=420x420&format=png"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get("data") and len(data["data"]) > 0: # [cite: 2]
                return data["data"][0].get("imageUrl") # [cite: 2]
    except Exception as e:
        print(f"⚠️ Erro ao obter thumbnail: {e}") # [cite: 2]
    return None

def main():
    print("🚀 Iniciando processo de upload via Cookie...")
    
    if not ROBLOX_COOKIE:
        print("❌ Erro: ROBLOX_COOKIE não encontrado nas variáveis de ambiente.")
        return

    if not EVENT_PATH:
        print("❌ Erro: GITHUB_EVENT_PATH não encontrado.") # [cite: 4]
        return

    # 1. Carregar Payload do GitHub Event [cite: 4]
    try:
        with open(EVENT_PATH, 'r') as f:
            event_data = json.load(f)
            payload = event_data.get("client_payload", {}) # [cite: 4]
    except Exception as e:
        print(f"❌ Erro ao ler payload: {e}") # [cite: 4]
        return

    PLAYER_WEBHOOK = payload.get("discord_webhook") # [cite: 5]
    ORIGINAL_ID = payload.get("asset_id") # [cite: 5]
    PLAYER_NAME = payload.get("player_name", "Unknown") # [cite: 5]
    TARGET_USER_ID = payload.get("target_user_id", "0") # [cite: 5]

    # 2. Download do Asset Original [cite: 5]
    file_path = "item.rbxm"
    r_down = requests.get(f"https://assetdelivery.roblox.com/v1/asset/?id={ORIGINAL_ID}") # [cite: 5]
    if r_down.status_code == 200:
        with open(file_path, "wb") as f:
            f.write(r_down.content) # [cite: 5]
        print("✅ Download concluído.")
    else:
        print(f"❌ Falha no download: {r_down.status_code}") # [cite: 6]
        return

    # 3. Gerar Token CSRF e realizar Upload
    csrf_token = get_csrf_token()
    if not csrf_token: return

    url = "https://apis.roblox.com/assets/v1/assets"
    asset_config = {
        "assetType": "Model",
        "displayName": f"Asset_{ORIGINAL_ID}",
        "description": f"Exported for {PLAYER_NAME}",
        "creationContext": {"creator": {"groupId": str(MY_GROUP_ID)}} # [cite: 6]
    }
    
    headers = {
        "Cookie": f".ROBLOSECURITY={ROBLOX_COOKIE}",
        "x-csrf-token": csrf_token
    }

    with open(file_path, "rb") as f:
        files = {
            "request": (None, json.dumps(asset_config), "application/json"), # [cite: 7]
            "fileContent": ("model.rbxm", f, "model/x-rbxm") # [cite: 7]
        }
        # Notar que aqui não usamos mais x-api-key, mas sim Cookie + CSRF
        response = requests.post(url, headers=headers, files=files)

    if response.status_code == 200:
        operation_path = response.json().get("path") # [cite: 7]
        print(f"⚙️ Operação iniciada: {operation_path}")
    else:
        print(f"❌ Erro no upload: {response.text}") # [cite: 8]
        return

    # 4. Polling para obter o ID Final [cite: 8]
    final_asset_id = "N/A"
    if operation_path:
        for i in range(10):
            time.sleep(3)
            # Polling também precisa de autenticação
            op_res = requests.get(f"https://apis.roblox.com/assets/v1/{operation_path}", headers=headers) # [cite: 9]
            if op_res.status_code == 200:
                op_data = op_res.json()
                if op_data.get("done"): # [cite: 9]
                    final_asset_id = op_data.get("response", {}).get("assetId", "N/A") # [cite: 9]
                    print(f"✅ Sucesso! ASSET_ID={final_asset_id}") # [cite: 10]
                    break
    
    # 5. Envio de Webhooks (Mantido do original) [cite: 10]
    thumbnail_url = get_asset_thumbnail(final_asset_id)
    embed_payload = {
        "embeds": [{
            "title": "📦 Asset Processed!",
            "description": f"Wsp **{PLAYER_NAME}**! Your request has been processed.", # [cite: 11]
            "color": 3066993 if final_asset_id != "N/A" else 15158332,
            "fields": [
                {"name": "Status", "value": "✅ Success" if final_asset_id != "N/A" else "❌ Failed", "inline": True},
                {"name": "Final ID", "value": str(final_asset_id), "inline": True}, # [cite: 11]
                {"name": "Player", "value": PLAYER_NAME, "inline": True} # [cite: 12]
            ],
            "image": {"url": thumbnail_url} if thumbnail_url else {},
            "footer": {"text": "Sent via AssetManager 4.0"} # [cite: 12]
        }]
    }

    targets = [ADMIN_WEBHOOK]
    if PLAYER_WEBHOOK: targets.append(PLAYER_WEBHOOK) # [cite: 13]

    for webhook_url in targets:
        requests.post(webhook_url, json=embed_payload) # [cite: 13]

    print("🏁 Processo finalizado.")

if __name__ == "__main__":
    main()
