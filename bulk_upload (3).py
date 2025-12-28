import requests
import os
import json

# 1. Captura de dados enviados pelo Roblox (Payload)
try:
    event_json = os.getenv("GITHUB_EVENT_PAYLOAD")
    event_data = json.loads(event_json)
    # Extrai o client_payload enviado pelo seu script Luau
    payload = event_data.get("client_payload", {})
except Exception as e:
    print(f"Erro ao carregar Payload: {e}")
    payload = {}

# Variáveis de Controle
ASSET_ID = payload.get("asset_id")
ASSET_NAME = payload.get("asset_name", "Asset Desconhecido")
PLAYER_NAME = payload.get("player_name", "Usuário")
TARGET_USER_ID = payload.get("target_user_id")
WEBHOOK_URL = payload.get("discord_webhook") # Recebido dinamicamente do jogo
ROBLOX_API_KEY = os.getenv("ROBLOX_API_KEY")

def send_discord_feedback(status_msg, success=True, roblox_id=None):
    """Envia o relatório final para o Discord"""
    if not WEBHOOK_URL:
        print("Webhook URL não encontrada no payload.")
        return

    color = 3066993 if success else 15158332 # Verde se sucesso, Vermelho se erro
    
    embed = {
        "title": "🛰️ Asset Manager 3.0 | Relatório de Integração",
        "description": f"O processamento do Asset foi concluído pelo GitHub Actions.",
        "color": color,
        "fields": [
            {"name": "📦 Asset Name", "value": f"`{ASSET_NAME}`", "inline": True},
            {"name": "👤 Solicitado por", "value": f"`{PLAYER_NAME}`", "inline": True},
            {"name": "🆔 Roblox ID", "value": f"`{roblox_id or ASSET_ID}`", "inline": True},
            {"name": "📊 Status", "value": status_msg, "inline": False}
        ],
        "footer": {"text": "Powered by GitHub Actions & Roblox Open Cloud"}
    }

    if success and roblox_id:
        embed["description"] += f"\n\n🔗 [Ver no Roblox](https://www.roblox.com/library/{roblox_id})"

    requests.post(WEBHOOK_URL, json={"embeds": [embed]})

def run_upload():
    # Validação de API Key
    if not ROBLOX_API_KEY:
        send_discord_feedback("❌ Erro: ROBLOX_API_KEY não configurada nos Secrets do GitHub.", False)
        return

    # ENDPOINT DA ROBLOX CLOUD PARA ASSETS
    url = "https://apis.roblox.com/assets/v1/assets"
    
    # Configuração do Asset na Nuvem
    asset_config = {
        "assetType": "Model", # Ou Decal, conforme sua necessidade
        "displayName": f"{ASSET_NAME} (via GitHub)",
        "creationContext": {
            "creator": {"userId": str(TARGET_USER_ID)}
        }
    }

    # PROCURANDO O ARQUIVO NO REPOSITÓRIO
    # Ele procura um arquivo com o nome do ID (ex: 12345.rbxm) na pasta assets/
    file_to_upload = f"assets/{ASSET_ID}.rbxm"
    
    if not os.path.exists(file_to_upload):
        # Se não achar o arquivo específico, tenta pegar qualquer arquivo na pasta assets
        files_in_folder = os.listdir("assets/")
        if files_in_folder:
            file_to_upload = os.path.join("assets/", files_in_folder[0])
        else:
            send_discord_feedback("❌ Erro: Nenhum arquivo encontrado na pasta /assets para upload.", False)
            return

    # Realizando o Upload para o Roblox
    try:
        with open(file_to_upload, "rb") as f:
            files = {
                "request": (None, json.dumps(asset_config), "application/json"),
                "fileContent": (os.path.basename(file_to_upload), f, "application/octet-stream")
            }
            headers = {"x-api-key": ROBLOX_API_KEY}
            
            response = requests.post(url, headers=headers, files=files)
            
            if response.status_code == 200:
                data = response.json()
                new_asset_id = data.get("assetId", ASSET_ID)
                send_discord_feedback("✅ Arquivo carregado com sucesso na conta do jogador!", True, new_asset_id)
            else:
                send_discord_feedback(f"❌ Erro Roblox API: {response.status_code} - {response.text}", False)
    except Exception as e:
        send_discord_feedback(f"❌ Erro crítico no Python: {str(e)}", False)

if __name__ == "__main__":
    run_upload()