import requests
import os
import json
import time

# Configurações do Ambiente
API_KEY = os.getenv("RBX_API_KEY")
MY_GROUP_ID = "633516837"
UNIVERSE_ID = "9469723620"
EVENT_PATH = os.getenv("GITHUB_EVENT_PATH")

# Webhook fixo para administração/logs
ADMIN_WEBHOOK = "https://discord.com/api/webhooks/1453805636784488509/6tdAXTB0DqdiWaLTmi05bWWDnTDk9mGLhmDFVTXgiL48yVKcOpN_at22DtCY8SotPvn1"

def get_asset_thumbnail(asset_id):
    """Obtém a URL da imagem do asset via API de Thumbnails do Roblox."""
    if asset_id == "N/A":
        return None
    url = f"https://thumbnails.roblox.com/v1/assets?assetIds={asset_id}&returnPolicy=PlaceHolder&size=420x420&format=png"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            if data.get("data") and len(data["data"]) > 0:
                return data["data"][0].get("imageUrl")
    except Exception as e:
        print(f"⚠️ Erro ao obter thumbnail: {e}")
    return None

def notify_roblox(status, asset_id="N/A", target_user_id="0"):
    """Notifica a experiência Roblox via Messaging Service."""
    url = f"https://apis.roblox.com/messaging-service/v1/universes/{UNIVERSE_ID}/topics/AssetUploadFeedback"
    data = {
        "message": json.dumps({
            "playerId": str(target_user_id),
            "status": status,
            "assetId": str(asset_id)
        })
    }
    try:
        requests.post(url, headers={"x-api-key": API_KEY, "Content-Type": "application/json"}, json=data)
    except:
        pass

def main():
    print("🚀 Iniciando processo de upload...")
    
    if not EVENT_PATH:
        print("❌ Erro: GITHUB_EVENT_PATH não encontrado.")
        return

    # 1. Carregar Payload do GitHub Event
    try:
        with open(EVENT_PATH, 'r') as f:
            event_data = json.load(f)
            payload = event_data.get("client_payload", {})
    except Exception as e:
        print(f"❌ Erro ao ler payload: {e}")
        return

    PLAYER_WEBHOOK = payload.get("discord_webhook")
    ORIGINAL_ID = payload.get("asset_id")
    PLAYER_NAME = payload.get("player_name", "Unknown")
    TARGET_USER_ID = payload.get("target_user_id", "0")

    print(f"📦 Processando Asset ID: {ORIGINAL_ID} para {PLAYER_NAME}")

    # 2. Download do Asset Original
    file_path = "item.rbxm"
    r_down = requests.get(f"https://assetdelivery.roblox.com/v1/asset/?id={ORIGINAL_ID}")
    if r_down.status_code == 200:
        with open(file_path, "wb") as f:
            f.write(r_down.content)
        print("✅ Download concluído.")
    else:
        print(f"❌ Falha no download: {r_down.status_code}")
        return

    # 3. Upload para o Grupo Roblox (MIME Type model/x-rbxm)
    url = "https://apis.roblox.com/assets/v1/assets"
    asset_config = {
        "assetType": "Model",
        "displayName": f"Asset_{ORIGINAL_ID}",
        "description": f"Exported for {PLAYER_NAME}",
        "creationContext": {"creator": {"groupId": str(MY_GROUP_ID)}}
    }
    
    operation_path = None
    with open(file_path, "rb") as f:
        files = {
            "request": (None, json.dumps(asset_config), "application/json"),
            "fileContent": ("model.rbxm", f, "model/x-rbxm")
        }
        response = requests.post(url, headers={"x-api-key": API_KEY}, files=files)

    if response.status_code == 200:
        operation_path = response.json().get("path")
        print(f"⚙️ Operação iniciada: {operation_path}")
    else:
        print(f"❌ Erro no upload: {response.text}")
        notify_roblox("error", target_user_id=TARGET_USER_ID)
        return

    # 4. Polling para obter o ID Final
    final_asset_id = "N/A"
    if operation_path:
        for i in range(10):
            time.sleep(3)
            print(f"⏱️ Verificando status (tentativa {i+1})...")
            op_res = requests.get(f"https://apis.roblox.com/assets/v1/{operation_path}", headers={"x-api-key": API_KEY})
            if op_res.status_code == 200:
                op_data = op_res.json()
                if op_data.get("done"):
                    final_asset_id = op_data.get("response", {}).get("assetId", "N/A")
                    print(f"✅ Sucesso! Novo ID: {final_asset_id}")
                    break
    
    # 5. Formatação do Webhook (Modelo Antigo com Imagem e Fields)
    thumbnail_url = get_asset_thumbnail(final_asset_id)
    display_id = f"[{final_asset_id}](https://www.roblox.com/library/{final_asset_id})" if final_asset_id != "N/A" else "`N/A`"
    
    embed_payload = {
        "embeds": [{
            "title": "📦 Asset Processed!",
            "description": f"Wsp **{PLAYER_NAME}**! Your request has been processed.",
            "color": 3066993 if final_asset_id != "N/A" else 15158332,
            "fields": [
                {"name": "Status", "value": "✅ Success" if final_asset_id != "N/A" else "❌ Failed", "inline": True},
                {"name": "Final ID", "value": display_id, "inline": True},
                {"name": "Player", "value": PLAYER_NAME, "inline": True}
            ],
            "image": {"url": thumbnail_url} if thumbnail_url else {},
            "footer": {"text": "Sent via AssetManager 4.0"}
        }]
    }

    # Disparar para os dois destinos
    targets = [ADMIN_WEBHOOK]
    if PLAYER_WEBHOOK:
        targets.append(PLAYER_WEBHOOK)

    for webhook_url in targets:
        try:
            requests.post(webhook_url, json=embed_payload)
        except Exception as e:
            print(f"⚠️ Erro ao enviar webhook: {e}")

    # Notificação final para o jogo
    notify_roblox("success" if final_asset_id != "N/A" else "error", final_asset_id, TARGET_USER_ID)
    print("🏁 Processo finalizado.")

if __name__ == "__main__":
    main()
