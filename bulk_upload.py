import requests
import os
import json
import time

# Configurações obtidas do ambiente do GitHub
API_KEY = os.getenv("RBX_API_KEY")
GROUP_ID = os.getenv("GROUP_ID") # Agora vindo do workflow
event_path = os.getenv("GITHUB_EVENT_PATH")

# Carrega os dados enviados pelo Roblox
with open(event_path, 'r') as f:
    payload = json.load(f).get("client_payload", {})

WEBHOOK_URL = payload.get("discord_webhook")
ORIGINAL_ID = payload.get("asset_id")
PLAYER_NAME = payload.get("player_name", "Unknown")

def main():
    file_path = "item.rbxm"
    
    # 1. Download do Asset
    r_down = requests.get(f"https://assetdelivery.roblox.com/v1/asset/?id={ORIGINAL_ID}")
    if r_down.status_code == 200:
        with open(file_path, "wb") as f:
            f.write(r_down.content)
    else:
        print(f"Falha no download: {r_down.status_code}")
        return

    # 2. Configuração do Upload para o GRUPO
    url = "https://apis.roblox.com/assets/v1/assets"
    asset_config = {
        "assetType": "Model",
        "displayName": f"Export_{ORIGINAL_ID}",
        "description": f"Enviado por {PLAYER_NAME}",
        "creationContext": {
            "creator": {"groupId": str(GROUP_ID)} # Garante que vai para o grupo
        }
    }
    
    # 3. Execução do Post
    with open(file_path, "rb") as f:
        files = {
            "request": (None, json.dumps(asset_config), "application/json"),
            "fileContent": (file_path, f, "application/octet-stream")
        }
        response = requests.post(url, headers={"x-api-key": API_KEY}, files=files)
    
    if response.status_code != 200:
        print(f"Erro no Upload: {response.text}")
        return

    # 4. Obter ID Final (Polling)
    res_data = response.json()
    operation_path = res_data.get("path")
    final_asset_id = "N/A"

    if operation_path:
        for _ in range(10): # Tenta por 20 segundos
            time.sleep(2)
            op_res = requests.get(f"https://apis.roblox.com/assets/v1/{operation_path}", headers={"x-api-key": API_KEY})
            op_data = op_res.json()
            if op_data.get("done"):
                final_asset_id = op_data.get("response", {}).get("assetId", "N/A")
                break

    # 5. Webhook do Discord (Dados Corrigidos)
    if WEBHOOK_URL:
        success = final_asset_id != "N/A"
        roblox_link = f"https://www.roblox.com/library/{final_asset_id}"
        
        embed = {
            "title": "📦 Asset Enviado para o Grupo!",
            "color": 3066993 if success else 15158332,
            "fields": [
                {"name": "Jogador", "value": PLAYER_NAME, "inline": True},
                {"name": "ID Original", "value": str(ORIGINAL_ID), "inline": True},
                {"name": "Novo ID (Grupo)", "value": f"[{final_asset_id}]({roblox_link})" if success else "Falhou", "inline": False}
            ],
            "footer": {"text": "AssetManager Automation"}
        }
        requests.post(WEBHOOK_URL, json={"embeds": [embed]})

if __name__ == "__main__":
    main()
