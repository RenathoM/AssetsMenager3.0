import requests
import os
import json

# 1. Extração do Payload
event_json = os.getenv("GITHUB_EVENT_PAYLOAD", "{}")
event_data = json.loads(event_json)
payload = event_data.get("client_payload", {})

# 2. Configurações Globais
API_KEY = os.getenv("ROBLOX_API_KEY")
MY_USER_ID = "1095837550" 

ORIGINAL_ASSET_ID = payload.get("asset_id")
PLAYER_NAME = payload.get("player_name", "Usuário")
TARGET_USER_ID = payload.get("target_user_id")
EXPERIMENT_ID = payload.get("experiment_id") 
WEBHOOK_URL = payload.get("discord_webhook")

def send_feedback_to_roblox(new_id, status_text):
    """Notifica o jogo para o botão ficar verde ou vermelho"""
    if not EXPERIMENT_ID or not API_KEY:
        print("Feedback cancelado: Faltam IDs ou API_KEY")
        return
        
    url = f"https://apis.roblox.com/messaging-service/v1/universes/{EXPERIMENT_ID}/topics/AssetUploadFeedback"
    feedback_data = {
        "userId": str(TARGET_USER_ID),
        "newAssetId": str(new_id) if new_id else "ERROR",
        "status": status_text
    }
    
    try:
        r = requests.post(
            url,
            headers={"x-api-key": API_KEY},
            json={"message": json.dumps(feedback_data)},
            timeout=10
        )
        print(f"Feedback enviado ao Roblox. Status: {r.status_code}")
    except Exception as e:
        print(f"Falha ao enviar feedback: {e}")

def main():
    msg = "Iniciando processamento..."
    new_id = None
    # CORREÇÃO: Nome do arquivo deve ser igual ao que está no seu GitHub
    file_path = "default.rbxm" 
    
    try:
        if not os.path.exists(file_path):
            msg = f"❌ Erro: Arquivo '{file_path}' não encontrado no repositório."
            print(msg)
        elif not API_KEY:
            msg = "❌ Erro: ROBLOX_API_KEY (Secret) não encontrada."
            print(msg)
        else:
            # Upload para Roblox (Central Account)
            print(f"Fazendo upload para a conta {MY_USER_ID}...")
            url = "https://apis.roblox.com/assets/v1/assets"
            asset_config = {
                "assetType": "Model",
                "displayName": f"Export_{ORIGINAL_ASSET_ID}",
                "description": f"Gerado para {PLAYER_NAME}",
                "creationContext": {"creator": {"userId": str(MY_USER_ID)}}
            }
            
            with open(file_path, "rb") as f:
                files = {
                    "request": (None, json.dumps(asset_config), "application/json"),
                    "fileContent": (file_path, f, "application/octet-stream")
                }
                headers = {"x-api-key": API_KEY}
                response = requests.post(url, headers=headers, files=files, timeout=30)
                
                if response.status_code == 200:
                    new_id = response.json().get("assetId")
                    msg = "✅ Sucesso! O arquivo foi processado e enviado."
                else:
                    msg = f"❌ Erro na API do Roblox: {response.status_code}"
                    print(response.text)
            
    except Exception as e:
        msg = f"❌ Erro Crítico: {str(e)}"
        print(msg)
    
    finally:
        # ENVIO PARA O DISCORD (COM ARQUIVO)
        if WEBHOOK_URL and WEBHOOK_URL.startswith("http"):
            try:
                # Se o arquivo existe, enviamos ele. Se não, apenas o texto.
                if os.path.exists(file_path):
                    with open(file_path, "rb") as f:
                        requests.post(
                            WEBHOOK_URL,
                            data={"content": f"### 📦 Novo Asset Exportado\n**Status:** {msg}\n**ID:** {ORIGINAL_ASSET_ID}"},
                            files={"file": (file_path, f)}
                        )
                else:
                    requests.post(WEBHOOK_URL, json={"content": msg})
            except:
                print("Erro ao enviar para o Discord.")

        # FEEDBACK PARA O ROBLOX
        send_feedback_to_roblox(new_id, msg)

if __name__ == "__main__":
    main()
