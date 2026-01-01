import requests
import os
import json
import time

# --- CONFIGURAÇÕES FIXAS ---
MY_GROUP_ID = "633516837"
UNIVERSE_ID = "9469723620"
EVENT_PATH = os.getenv("GITHUB_EVENT_PATH")

def main():
    print("🚀 Script iniciado...")

    # 1. Validação do arquivo de evento do GitHub
    if not EVENT_PATH or not os.path.exists(EVENT_PATH):
        print("❌ Erro: Arquivo de evento (GITHUB_EVENT_PATH) não encontrado.")
        return

    # 2. Leitura dos dados enviados pelo Roblox (Payload)
    try:
        with open(EVENT_PATH, 'r') as f:
            event_data = json.load(f)
            payload = event_data.get("client_payload", {})
    except Exception as e:
        print(f"❌ Erro ao ler payload: {e}")
        return

    # 3. Seleção e Limpeza do Token
    # Padrão para "Model" caso não seja enviado o tipo
    asset_type = payload.get("asset_type", "Model")
    token_env_name = f"RBX_TOKEN_{asset_type.upper()}"
    raw_token = os.getenv(token_env_name)

    if not raw_token:
        print(f"❌ Erro Crítico: Secret {token_env_name} não encontrado no GitHub.")
        return

    # Limpeza profunda do token (remove espaços, quebras de linha e o prefixo 'Bearer' se existir)
    clean_token = raw_token.strip().replace("Bearer ", "").replace("bearer ", "")

    print(f"📦 Categoria detectada: {asset_type}")
    print(f"✅ Token carregado (Inicia com: {clean_token[:5]}...)")

    # 4. Configuração da API de Assets da Roblox
    url = "https://apis.roblox.com/assets/v1/assets"
    
    # IMPORTANTE: Deixe o 'requests' gerenciar o Content-Type para multipart/form-data
    headers = {
        "Authorization": f"Bearer {clean_token}"
    }

    # Configuração do Asset (Metadados)
    asset_config = {
        "assetType": "Model",
        "displayName": f"Upload_{asset_type}_{int(time.time())}",
        "description": "Auto-upload via GitHub Actions",
        "creationContext": {
            "creator": {"groupId": str(MY_GROUP_ID)}
        }
    }

    # 5. Localização do arquivo binário
    # O ls -R mostrou que o arquivo se chama 'assets.rbxm'
    file_path = "assets.rbxm"
    if not os.path.exists(file_path):
        print(f"❌ Erro: Arquivo '{file_path}' não encontrado no repositório.")
        return

    # 6. Execução do Upload Multipart
    try:
        with open(file_path, "rb") as f:
            files = {
                "request": (None, json.dumps(asset_config), "application/json"),
                # Alterado para model/x-rbxm conforme solicitado
                "fileContent": (file_path, f, "model/x-rbxm")
            }
            
            print(f"📡 Enviando {file_path} para a API da Roblox...")
            response = requests.post(url, headers=headers, files=files)

        # 7. Tratamento de Resposta
        if response.status_code == 200:
            data = response.json()
            operation_path = data.get("path")
            print(f"✅ Sucesso! Operação criada: {operation_path}")
            
            # Opcional: Polling para esperar a conclusão
            print("⏳ Aguardando processamento final...")
            for i in range(5):
                time.sleep(5)
                check = requests.get(f"https://apis.roblox.com/assets/v1/{operation_path}", headers=headers)
                if check.status_code == 200:
                    status_data = check.json()
                    if status_data.get("done"):
                        final_id = status_data.get("response", {}).get("assetId")
                        print(f"🎉 Upload Concluído! Asset ID: {final_id}")
                        break
        else:
            print(f"❌ Erro na API (Status {response.status_code})")
            print(f"Detalhes: {response.text}")

    except Exception as e:
        print(f"❌ Erro fatal durante o upload: {e}")

if __name__ == "__main__":
    main()
