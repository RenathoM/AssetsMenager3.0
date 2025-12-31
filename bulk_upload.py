import requests
import os
import json
import time

# 1. CONFIGURAÇÕES DE AMBIENTE
API_KEY = os.getenv("RBX_API_KEY")
MY_GROUP_ID = "633516837"
UNIVERSE_ID = "103111986841337"
event_path = os.getenv("GITHUB_EVENT_PATH")

# Carrega os dados enviados pelo Roblox através do GitHub
with open(event_path, 'r') as f:
    payload = json.load(f).get("client_payload", {})

WEBHOOK_URL = payload.get("discord_webhook")
ORIGINAL_ID = payload.get("asset_id")
PLAYER_NAME = payload.get("player_name", "Unknown")
TARGET_USER_ID = payload.get("target_user_id")

def main():
    file_path = "item.rbxm"
    
    # 2. DOWNLOAD DO ASSET ORIGINAL
    # Baixa o ficheiro binário do Roblox para processamento
    r_down = requests.get(f"https://assetdelivery.roblox.com/v1/asset/?id={ORIGINAL_ID}")
    if r_down.status_code == 200:
        with open(file_path, "wb") as f:
            f.write(r_down.content)
    else:
        print("❌ Erro ao baixar asset original")
        return

    # 3. UPLOAD PARA A API OPEN CLOUD
    url = "https://apis.roblox.com/assets/v1/assets"
    
    asset_config = {
        "assetType": "Model",
        "displayName": f"Asset_{ORIGINAL_ID}",
        "description": "Exported via AssetManager 4.0",
        "creationContext": {
            "creator": {"groupId": str(MY_GROUP_ID)}
        }
    }
    
    with open(file_path, "rb") as f:
        # A chave aqui é enviar como model.rbxm e application/octet-stream
        files = {
            "request": (None, json.dumps(asset_config), "application/json"),
            "fileContent": ("model.rbxm", f, "application/octet-stream")
        }
        
        response = requests.post(url, headers={"x-api-key": API_KEY}, files=files)
    
    if response.status_code != 200:
        print(f"❌ Erro no Upload: {response.text}")
        return

    res_data = response.json()
    operation_path = res_data.get("path")
    final_asset_id = "N/A"

    # 4. POLLING (Aguardar o processamento do ID)
    if operation_path:
        print("⏳ Processando asset no Roblox...")
        for _ in range(15):
            time.sleep(2)
            op_res = requests.get(f"https://apis.roblox.com/assets/v1/{operation_path}", headers={"x-api-key": API_KEY})
            op_data = op_res.json()
            
            if op_data.get("done"):
                final_asset_id = op_data.get("response", {}).get("assetId", "N/A")
                # ESTA LINHA ABAIXO É A MAIS IMPORTANTE PARA O BOTÃO ATUALIZAR:
                print(f"ASSET_ID={final_asset_id}")
                break
    
    # 5. FEEDBACK DISCORD
    success = final_asset_id != "N/A"
    if WEBHOOK_URL:
        roblox_url = f"https://www.roblox.com/library/{final_asset_id}"
        embed = {
            "title": "📦 Asset Processado!",
            "description": f"Olá **{PLAYER_NAME}**! O seu modelo foi enviado para o grupo.",
            "color": 3066993 if success else 15158332,
            "fields": [
                {"name": "Status", "value": "✅ Sucesso" if success else "❌ Falhou", "inline": True},
                {"name": "Novo ID", "value": f"[{final_asset_id}]({roblox_url})", "inline": True}
            ]
        }
        requests.post(WEBHOOK_URL, json={"embeds": [embed]})

if __name__ == "__main__":
    main()
