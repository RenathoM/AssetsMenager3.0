import requests
import os
import json

# Extração do Payload
event_json = os.getenv("GITHUB_EVENT_PAYLOAD", "{}")
event_data = json.loads(event_json)
payload = event_data.get("client_payload", {})

API_KEY = os.getenv("ROBLOX_API_KEY")
MY_USER_ID = "1095837550"
WEBHOOK_URL = payload.get("discord_webhook")
EXPERIMENT_ID = payload.get("experiment_id")
TARGET_USER_ID = payload.get("target_user_id")

def main():
    # LÓGICA DE SELEÇÃO DE ARQUIVO
    if os.path.exists("assets.rbxm"):
        file_path = "assets.rbxm"
    elif os.path.exists("default.rbxm"):
        file_path = "default.rbxm"
    else:
        print("❌ Erro: Nenhum arquivo .rbxm encontrado!")
        return

    print(f"📂 Usando arquivo: {file_path}")

    try:
        # Upload para Roblox
        url = "https://apis.roblox.com/assets/v1/assets"
        asset_config = {
            "assetType": "Model",
            "displayName": f"Export_{payload.get('asset_id')}",
            "creationContext": {"creator": {"userId": str(MY_USER_ID)}}
        }
        
        with open(file_path, "rb") as f:
            files = {
                "request": (None, json.dumps(asset_config), "application/json"),
                "fileContent": (file_path, f, "application/octet-stream")
            }
            response = requests.post(url, headers={"x-api-key": API_KEY}, files=files)
            
            if response.status_code == 200:
                print("✅ Upload concluído com sucesso.")
            else:
                print(f"❌ Erro API Roblox: {response.text}")

    except Exception as e:
        print(f"❌ Erro: {e}")

    # O Webhook agora é enviado pelo YAML para garantir o anexo do arquivo,
    # mas o Python ainda pode enviar o feedback para o jogo:
    if EXPERIMENT_ID and API_KEY:
        feedback_url = f"https://apis.roblox.com/messaging-service/v1/universes/{EXPERIMENT_ID}/topics/AssetUploadFeedback"
        msg = {"userId": str(TARGET_USER_ID), "newAssetId": payload.get('asset_id'), "status": "Finalizado"}
        requests.post(feedback_url, headers={"x-api-key": API_KEY}, json={"message": json.dumps(msg)})

if __name__ == "__main__":
    main()
