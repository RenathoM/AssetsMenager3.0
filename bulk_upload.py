import requests
import os
import json
import time

# Configurações do Ambiente
API_KEY = os.getenv("RBX_API_KEY")
MY_GROUP_ID = "633516837"
UNIVERSE_ID = "103111986841337"
EVENT_PATH = os.getenv("GITHUB_EVENT_PATH")

def notify_roblox(status, asset_id="N/A", target_user_id="0"):
    url = f"https://apis.roblox.com/messaging-service/v1/universes/{UNIVERSE_ID}/topics/AssetUploadFeedback"
    data = {
        "message": json.dumps({
            "playerId": str(target_user_id),
            "status": status,
            "assetId": str(asset_id)
        })
    }
    requests.post(url, headers={"x-api-key": API_KEY, "Content-Type": "application/json"}, json=data)

def main():
    print("🚀 Iniciando processo de upload...")
    
    if not EVENT_PATH:
        print("❌ Erro: GITHUB_EVENT_PATH não encontrado.")
        return

    # 1. Carregar Payload
    try:
        with open(EVENT_PATH, 'r') as f:
            event_data = json.load(f)
            payload = event_data.get("client_payload", {})
        print("✅ Dados do evento carregados.")
    except Exception as e:
        print(f"❌ Erro ao ler payload: {e}")
        return

    WEBHOOK_URL = payload.get("discord_webhook")
    ORIGINAL_ID = payload.get("asset_id")
    PLAYER_NAME = payload.get("player_name", "Unknown")
    TARGET_USER_ID = payload.get("target_user_id", "0")

    print(f"📦 Processando Asset ID: {ORIGINAL_ID} para o jogador {PLAYER_NAME}")

    # 2. Download do Asset
    file_path = "item.rbxm"
    r_down = requests.get(f"https://assetdelivery.roblox.com/v1/asset/?id={ORIGINAL_ID}")
    
    if r_down.status_code == 200:
        with open(file_path, "wb") as f:
            f.write(r_down.content)
        print("✅ Download concluído.")
    else:
        print(f"❌ Falha no download. Status: {r_down.status_code}")
        notify_roblox("error", target_user_id=TARGET_USER_ID)
        return

    # 3. Upload para Roblox
    print(f"📤 Enviando para o grupo {MY_GROUP_ID}...")
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
            "fileContent": ("model.rbxm", f, "application/octet-stream")
        }
        response = requests.post(url, headers={"x-api-key": API_KEY}, files=files)

    if response.status_code != 200:
        print(f"❌ Erro no upload: {response.text}")
        return

    operation_path = response.json().get("path")
    print(f"⚙️ Operação iniciada: {operation_path}")

    # 4. Polling
    final_asset_id = "N/A"
    for i in range(10):
        time.sleep(3)
        print(f"⏱️ Verificando status (tentativa {i+1})...")
        op_res = requests.get(f"https://apis.roblox.com/assets/v1/{operation_path}", headers={"x-api-key": API_KEY})
        op_data = op_res.json()
        if op_data.get("done"):
            final_asset_id = op_data.get("response", {}).get("assetId", "N/A")
            print(f"✅ Sucesso! Novo ID: {final_asset_id}")
            break

    # 5. Discord e Finalização
    if WEBHOOK_URL:
        embed = {
            "title": "📦 Asset Processado!",
            "description": f"Jogador: **{PLAYER_NAME}**\nID: **{final_asset_id}**",
            "color": 3066993 if final_asset_id != "N/A" else 15158332
        }
        requests.post(WEBHOOK_URL, json={"embeds": [embed]})
        print("✉️ Webhook do Discord enviado.")

    notify_roblox("success" if final_asset_id != "N/A" else "error", final_asset_id, TARGET_USER_ID)
    print("🏁 Processo finalizado.")

if __name__ == "__main__":
    main()
