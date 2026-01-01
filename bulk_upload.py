import requests
import os
import json
import time

# --- CONFIGURAÇÕES FIXAS ---
MY_GROUP_ID = "633516837"
EVENT_PATH = os.getenv("GITHUB_EVENT_PATH")

def main():
    print("🚀 Script iniciado...")

    # 1. Validação do arquivo de evento do GitHub
    if not EVENT_PATH or not os.path.exists(EVENT_PATH):
        print("❌ Erro: GITHUB_EVENT_PATH não encontrado.")
        return

    # 2. Leitura do Payload
    try:
        with open(EVENT_PATH, 'r') as f:
            event_data = json.load(f)
            payload = event_data.get("client_payload", {})
    except Exception as e:
        print(f"❌ Erro ao ler payload: {e}")
        return

    # 3. Seleção e Limpeza do Token
    asset_type = payload.get("asset_type", "Model")
    token_env_name = f"RBX_TOKEN_{asset_type.upper()}"
    raw_token = os.getenv(token_env_name)

    if not raw_token:
        print(f"❌ Erro Crítico: Secret {token_env_name} não encontrado.")
        return

    # Limpeza total para evitar o erro 401: remove prefixos e espaços invisíveis
    clean_token = raw_token.strip().replace("Bearer ", "").replace("bearer ", "")

    print(f"📦 Categoria: {asset_type}")
    print(f"✅ Token carregado (Inicia com: {clean_token[:5]}...)")

    # 4. Configuração da Requisição
    url = "https://apis.roblox.com/assets/v1/assets"
    
    # Se você estiver usando API Key do Creator Hub, troque "Authorization" por "x-api-key"
    # O erro 401 "Failed to read token" geralmente acontece por essa confusão de headers.
    headers = {
        "Authorization": f"Bearer {clean_token}"
    }

    asset_config = {
        "assetType": asset_type,
        "displayName": f"AutoUpload_{int(time.time())}",
        "description": "Upload automático via GitHub Actions",
        "creationContext": {
            "creator": {"groupId": str(MY_GROUP_ID)}
        }
    }

    # 5. Verificação do arquivo local
    file_path = "assets.rbxm"
    if not os.path.exists(file_path):
        print(f"❌ Erro: Arquivo {file_path} não encontrado.")
        return

    # 6. Upload Multipart
    try:
        with open(file_path, "rb") as f:
            files = {
                "request": (None, json.dumps(asset_config), "application/json"),
                "fileContent": (file_path, f, "model/x-rbxm")
            }
            
            print(f"📡 Enviando {file_path} para Roblox...")
            response = requests.post(url, headers=headers, files=files)

        # 7. Resposta e Polling
        if response.status_code == 200:
            op_path = response.json().get("path")
            print(f"✅ Operação iniciada: {op_path}")
            
            # Pequeno loop para verificar se o processamento terminou
            for _ in range(3):
                time.sleep(5)
                check = requests.get(f"https://apis.roblox.com/assets/v1/{op_path}", headers=headers)
                if check.ok and check.json().get("done"):
                    asset_id = check.json().get("response", {}).get("assetId")
                    print(f"🎉 Sucesso total! Novo Asset ID: {asset_id}")
                    return
        else:
            print(f"❌ Erro {response.status_code}: {response.text}")

    except Exception as e:
        print(f"❌ Erro fatal: {e}")

if __name__ == "__main__":
    main()
