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
    try:
        requests.post(url, headers={"x-api-key": API_KEY, "Content-Type": "application/json"}, json=data)
    except:
        pass

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
    except Exception as e:
        print(f"❌ Erro ao ler payload: {e}")
        return

    WEBHOOK_URL = payload.get("discord_webhook")
    ORIGINAL_ID = payload.get("asset_id")
    PLAYER_NAME = payload.get("player_name", "Unknown")
    TARGET_USER_ID = payload.get("target_user_id", "0")

    print(f"📦 Processando Asset ID: {ORIGINAL_ID} para {PLAYER_NAME}")

    # 2. Download
    file_path = "item.rbxm"
    r_down = requests.get(f"https://assetdelivery.roblox.com/v1/asset/?id={ORIGINAL_ID}")
    if r_down.status_code == 200:
        with open(file_path, "wb") as f:
            f.write(r_down.content)
        print("✅ Download concluído.")
    else:
        print(f"❌ Falha no download: {r_down.status_code}")
        return

    # 3. Upload (Correção do MIME Type e Variável)
    print(f"📤 Enviando para o grupo {MY_GROUP_ID}...")
    url = "https://apis.roblox.com/assets/v1/assets"
    asset_config = {
        "assetType": "Model",
        "displayName": f"Asset_{ORIGINAL_ID}",
        "description": f"Exported for {PLAYER_NAME}",
        "creationContext": {"creator": {"groupId": str(MY_GROUP_ID)}}
    }
    
    operation_path = None # Inicializa a variável para evitar o NameError

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
        return # Para o script aqui se falhar

    # 4. Polling (Só entra aqui se operation_path existir)
    final_asset_id = "N/A"
    if operation_path:
        for _ in range(15):
            time.sleep(2)
            op_res = requests.get(f"https://apis.roblox.com/assets/v1/{operation_path}", headers={"x-api-key": API_KEY})
            op_data = op_res.json()
            
            if op_data.get("done"):
                final_asset_id = op_data.get("response", {}).get("assetId", "N/A")
                # ESSENCIAL: Imprime para o GitHub Actions capturar o ID
                print(f"ASSET_ID={final_asset_id}")
                break
                
     # 5. Envio para o Discord (Sempre funciona, independente do jogo)
    if WEBHOOK_URL:
        roblox_url = f"https://www.roblox.com/library/{final_asset_id}"
        display_id = f"[{final_asset_id}]({roblox_url})" if success else "`N/A`"

        embed = {
            "title": ":package: Asset Processed!",
            "description": f"Wsp **{PLAYER_NAME}**! Your request has been processed.",
            "color": 3066993 if success else 15158332,
            "fields": [
                {"name": "Status", "value": ":white_check_mark: Success" if success else ":x: Failed", "inline": True},
                {"name": "Final ID", "value": display_id, "inline": True},
                {"name": "Player", "value": PLAYER_NAME, "inline": True}
            ],
            "footer": {"text": "Sent via AssetManager 4.0"}

    notify_roblox("success" if final_asset_id != "N/A" else "error", final_asset_id, TARGET_USER_ID)
    print("🏁 Processo finalizado.")

if __name__ == "__main__":
    main()
