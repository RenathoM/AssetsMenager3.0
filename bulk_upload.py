import requests
import os
import json
import time

# Configurações extraídas do ambiente
API_KEY = os.getenv("RBX_API_KEY")
MY_GROUP_ID = "633516837"
UNIVERSE_ID = "103111986841337" # ID da sua experiência
event_path = os.getenv("GITHUB_EVENT_PATH")

# Carregamento do Payload enviado pelo Roblox
with open(event_path, 'r') as f:
    payload = json.load(f).get("client_payload", {})

WEBHOOK_URL = payload.get("discord_webhook")
ORIGINAL_ID = payload.get("asset_id")
PLAYER_NAME = payload.get("player_name", "Unknown")
TARGET_USER_ID = payload.get("target_user_id")

def notify_roblox(status, asset_id="N/A"):
    """ Envia o feedback em tempo real para o MessagingService do jogo """
    url = f"https://apis.roblox.com/messaging-service/v1/universes/{UNIVERSE_ID}/topics/AssetUploadFeedback"
    data = {
        "message": json.dumps({
            "playerId": TARGET_USER_ID,
            "status": status,
            "assetId": asset_id
        })
    }
    requests.post(url, headers={"x-api-key": API_KEY, "Content-Type": "application/json"}, json=data)

def main():
    file_path = "item.rbxm"
    
    print(f"🚀 Iniciando processamento para {PLAYER_NAME}...")
    
    # 1. Download do Asset Original
    r_down = requests.get(f"https://assetdelivery.roblox.com/v1/asset/?id={ORIGINAL_ID}")
    if r_down.status_code == 200:
        with open(file_path, "wb") as f:
            f.write(r_down.content)
        print("✅ Download do asset original concluído.")
    else:
        print(f"❌ Erro ao baixar asset: {r_down.status_code}")
        notify_roblox("error")
        return

    # 2. Upload para a API de Assets do Roblox
    url = "https://apis.roblox.com/assets/v1/assets"
    asset_config = {
        "assetType": "Model",
        "displayName": f"Pacote_{ORIGINAL_ID}",
        "description": f"Enviado por {PLAYER_NAME} via AssetManager 4.0",
        "creationContext": {"creator": {"groupId": str(MY_GROUP_ID)}}
    }
    
    with open(file_path, "rb") as f:
        files = {
            "request": (None, json.dumps(asset_config), "application/json"),
            "fileContent": (file_path, f, "model/x-rbxm")
        }
        response = requests.post(url, headers={"x-api-key": API_KEY}, files=files)
    
    if response.status_code not in [200, 201]:
        print(f"❌ Erro no upload: {response.text}")
        notify_roblox("error")
        return

    res_data = response.json()
    operation_path = res_data.get("path")
    final_asset_id = "N/A"

    # 3. Lógica de Polling para capturar o ID numérico final
    if operation_path:
        print("⏳ Aguardando validação do Roblox (Polling)...")
        for i in range(10): # Tenta por até 20 segundos
            time.sleep(2)
            op_res = requests.get(f"https://apis.roblox.com/assets/v1/{operation_path}", headers={"x-api-key": API_KEY})
            op_data = op_res.json()
            
            if op_data.get("done"):
                final_asset_id = op_data.get("response", {}).get("assetId", "N/A")
                print(f"✅ ID Final capturado: {final_asset_id}")
                break
            print(f"   ...ainda processando ({i+1}/10)")
    
    success = final_asset_id != "N/A"
    
    # 4. Notificar o Jogo (Feedback imediato para o cliente)
    notify_roblox("success" if success else "error", final_asset_id)
    
    # 5. Notificar o Discord (Link formatado)
    if WEBHOOK_URL:
        asset_link = f"https://www.roblox.com/library/{final_asset_id}"
        # Formato Markdown: [Texto](URL)
        formatted_id = f"[{final_asset_id}]({asset_link})" if success else "`N/A`"
        
        embed = {
            "title": "📦 Asset Processed!",
            "color": 3066993 if success else 15158332,
            "fields": [
                {"name": "Status", "value": "✅ Success" if success else "❌ Failed", "inline": True},
                {"name": "Final ID", "value": formatted_id, "inline": True},
                {"name": "Player", "value": f"`{PLAYER_NAME}`", "inline": True}
            ],
            "footer": {"text": "Sent via AssetManager 4.0 | Beta Test"}
        }
        
        # Envia o arquivo junto com o embed para conferência
        with open(file_path, "rb") as f:
            requests.post(
                WEBHOOK_URL, 
                data={"payload_json": json.dumps({"embeds": [embed]})},
                files={"file": ("result.rbxm", f)}
            )
        print("✅ Notificação enviada ao Discord.")

if __name__ == "__main__":
    main()
