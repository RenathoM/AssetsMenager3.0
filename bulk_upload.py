import requests
import os
import json
import time

# 1. Carrega os dados enviados pelo Roblox (Client Payload)
# O GitHub armazena o evento em um arquivo cujo caminho está na variável GITHUB_EVENT_PATH
event_path = os.getenv("GITHUB_EVENT_PATH")
with open(event_path, 'r') as f:
    event_data = json.load(f)

payload = event_data.get("client_payload", {})

# 2. Configurações de Ambiente
API_KEY = os.getenv("RBX_API_KEY")
MY_GROUP_ID = "633516837"
WEBHOOK_URL = payload.get("discord_webhook")
ORIGINAL_ASSET_ID = payload.get("asset_id")
PLAYER_NAME = payload.get("player_name", "Unknown")

def main():
    file_path = "downloaded_asset.rbxm"
    new_id = "N/A"
    
    print(f"🚀 Iniciando processamento para: {PLAYER_NAME}")

    try:
        # --- PASSO 1: BAIXAR O ASSET REAL DO ROBLOX ---
        # Isso evita que o arquivo enviado ao grupo tenha 0 bytes ou seja o 'default.rbxm' antigo
        download_url = f"https://assetdelivery.roblox.com/v1/asset/?id={ORIGINAL_ASSET_ID}"
        print(f"📥 Baixando asset original ({ORIGINAL_ASSET_ID})...")
        r_down = requests.get(download_url)
        
        if r_down.status_code == 200:
            with open(file_path, "wb") as f:
                f.write(r_down.content)
            print("✅ Download concluído.")
        else:
            raise Exception(f"Falha no download: {r_down.status_code}")

        # --- PASSO 2: UPLOAD PARA O GRUPO VIA OPEN CLOUD ---
        url = "https://apis.roblox.com/assets/v1/assets"
        asset_config = {
            "assetType": "Model",
            "displayName": f"Pacote: {ORIGINAL_ASSET_ID}",
            "description": f"Gerado para {PLAYER_NAME} via AssetManager 4.0",
            "creationContext": {
                "creator": {
                    "groupId": str(MY_GROUP_ID)
                }
            }
        }
        
        print(f"📤 Enviando para o grupo {MY_GROUP_ID}...")
        with open(file_path, "rb") as f:
            files = {
                "request": (None, json.dumps(asset_config), "application/json"),
                "fileContent": (file_path, f, "application/octet-stream")
            }
            
            # O Open Cloud requer a API Key no header x-api-key
            response = requests.post(url, headers={"x-api-key": API_KEY}, files=files)
            
            if response.status_code in [200, 201]:
                # A API de Assets pode retornar o ID imediatamente ou um Operation Path
                resp_data = response.json()
                new_id = resp_data.get("assetId") or resp_data.get("path")
                print(f"✅ Sucesso! Novo ID/Path: {new_id}")
            else:
                print(f"❌ Erro no Upload: {response.status_code} - {response.text}")
                raise Exception(f"Roblox API Error: {response.text}")

    except Exception as e:
        print(f"💥 Erro Crítico: {str(e)}")
        new_id = f"ERROR: {str(e)[:20]}"

    # --- PASSO 3: NOTIFICAÇÃO DISCORD ---
    if WEBHOOK_URL:
        embed = {
            "title": "📦 Your Asset Is Ready!" if "ERROR" not in str(new_id) else "❌ Upload Failed",
            "description": f"Wsp **{PLAYER_NAME}!** Your file has been processed.",
            "color": 3066993 if "ERROR" not in str(new_id) else 15158332,
            "fields": [
                {"name": "Original ID", "value": f"`{ORIGINAL_ASSET_ID}`", "inline": True},
                {"name": "New ID (Group)", "value": f"`{new_id}`", "inline": True}
            ],
            "footer": {"text": "Sent via AssetManager 4.0"}
        }

        # Envia o embed e o arquivo baixado (para conferência)
        if os.path.exists(file_path):
            with open(file_path, "rb") as f:
                requests.post(WEBHOOK_URL, 
                    data={"payload_json": json.dumps({"embeds": [embed]})},
                    files={"file": ("result.rbxm", f)}
                )

if __name__ == "__main__":
    main()
