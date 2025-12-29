# TITULO: bulk_upload.py (Versão Final com Feedback)
import requests
import os
import json
import time

# 1. Extração do Payload (OBRIGATÓRIO VIR PRIMEIRO)
event_json = os.getenv("GITHUB_EVENT_PAYLOAD", "{}")
event_data = json.loads(event_json)
payload = event_data.get("client_payload", {})

# 2. Configurações Globais
API_KEY = os.getenv("ROBLOX_API_KEY")
MY_USER_ID = "1095837550" # Seu ID Roblox

# Dados do Roblox (Vindos do Luau)
ORIGINAL_ASSET_ID = payload.get("asset_id")
ASSET_NAME = payload.get("asset_name", "Asset Desconhecido")
PLAYER_NAME = payload.get("player_name", "Usuário")
TARGET_USER_ID = payload.get("target_user_id")
EXPERIMENT_ID = payload.get("experiment_id") # Universe ID
WEBHOOK_URL = payload.get("discord_webhook")

def send_feedback_to_roblox(new_id, status_text):
    """Envia o sinal de volta para o botão no jogo ficar verde"""
    if not EXPERIMENT_ID or not API_KEY:
        return
        
    url = f"https://apis.roblox.com/messaging-service/v1/universes/{EXPERIMENT_ID}/topics/AssetUploadFeedback"
    feedback_data = {
        "userId": TARGET_USER_ID,
        "newAssetId": new_id or "ERROR",
        "status": status_text
    }
    
    try:
        requests.post(
            url,
            headers={"x-api-key": API_KEY},
            json={"message": json.dumps(feedback_data)},
            timeout=10
        )
    except:
        print("Falha ao enviar feedback para o Roblox")

def main():
    msg = "Iniciando..."
    new_id = None
    
    # 3. Verificação de Arquivo
    file_path = "assets/default.rbxm" # Certifique-se que este arquivo existe no seu repo!
    
    try:
        if not os.path.exists(file_path):
            msg = "❌ Erro: Arquivo 'assets/default.rbxm' não encontrado."
        elif not API_KEY:
            msg = "❌ Erro: ROBLOX_API_KEY não configurada."
        else:
            # 4. Upload para Roblox
            url = "https://apis.roblox.com/assets/v1/assets"
            asset_config = {
                "assetType": "Model",
                "displayName": f"Gerado para {PLAYER_NAME}",
                "creationContext": {"creator": {"userId": str(MY_USER_ID)}}
            }
            
            with open(file_path, "rb") as f:
                files = {
                    "request": (None, json.dumps(asset_config), "application/json"),
                    "fileContent": ("model.rbxm", f, "application/octet-stream")
                }
                headers = {"x-api-key": API_KEY}
                response = requests.post(url, headers=headers, files=files, timeout=30)
                
                if response.status_code == 200:
                    new_id = response.json().get("assetId")
                    msg = "✅ Sucesso! O asset foi criado na conta central."
                else:
                    msg = f"❌ Erro Roblox API: {response.status_code} - {response.text}"
            
    except Exception as e:
        msg = f"❌ Erro Crítico GitHub: {str(e)}"
    
    finally:
        # 5. Feedback Final (Sempre executa)
        # Envia para o Discord
        if WEBHOOK_URL:
            discord_payload = {
                "content": f"### Relatório de Processamento\n> **Status:** {msg}\n> **ID Original:** {ORIGINAL_ASSET_ID}\n> **Novo ID:** `{new_id or 'Falhou'}`"
            }
            requests.post(WEBHOOK_URL, json=discord_payload)
        
        # Envia para o Jogo (Faz o botão ficar verde)
        send_feedback_to_roblox(new_id, msg)

if __name__ == "__main__":
    main()

    # NO PYTHON (bulk_upload.py)
def send_feedback_to_roblox(new_id, status_text):
    if not EXPERIMENT_ID or EXPERIMENT_ID == "None":
        print("Erro: EXPERIMENT_ID não recebido do Roblox!")
        return
        
    url = f"https://apis.roblox.com/messaging-service/v1/universes/{EXPERIMENT_ID}/topics/AssetUploadFeedback"
    
    feedback_data = {
        "userId": TARGET_USER_ID,
        "newAssetId": new_id or "ERROR",
        "status": status_text
    }
    
    # IMPORTANTE: A API Key precisa de permissão para Messaging Service no Dashboard do Roblox
    r = requests.post(
        url,
        headers={"x-api-key": API_KEY},
        json={"message": json.dumps(feedback_data)}
    )
    print(f"Feedback enviado ao Roblox. Status: {r.status_code}")
