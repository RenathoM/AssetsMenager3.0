import requests
import os
import json
import time

# Configurações fixas
MY_GROUP_ID = "633516837"
UNIVERSE_ID = "9469723620"
EVENT_PATH = os.getenv("GITHUB_EVENT_PATH")

def main():
    print("🚀 Script iniciado...")

    # 1. Verificar se o arquivo do GitHub existe
    if not EVENT_PATH or not os.path.exists(EVENT_PATH):
        print("❌ Erro: Arquivo de evento (GITHUB_EVENT_PATH) não encontrado.")
        return

    # 2. Ler os dados enviados pelo Roblox (Payload)
    try:
        with open(EVENT_PATH, 'r') as f:
            data = json.load(f)
            payload = data.get("client_payload", {})
    except Exception as e:
        print(f"❌ Erro ao ler o arquivo JSON: {e}")
        return

    # 3. Identificar o tipo de asset e o Token correspondente
    # Se o Roblox não enviar nada, o padrão é "Model"
    asset_type = payload.get("asset_type", "Model")
    token_env_name = f"RBX_TOKEN_{asset_type.upper()}"
    user_token = os.getenv(token_env_name)

    print(f"📦 Categoria detectada: {asset_type}")

    # 4. Validar o Token
    if not user_token:
        print(f"❌ Erro Crítico: A variável {token_env_name} está vazia no GitHub Secrets!")
        return
    else:
        # Mostra apenas os 5 primeiros caracteres por segurança
        print(f"✅ Token {token_env_name} encontrado (Inicia com: {user_token[:5]}...)")

    # 5. Configurar Cabeçalhos para a API do Roblox
    url = "https://apis.roblox.com/assets/v1/assets"
    headers = {
        "Authorization": f"Bearer {user_token.strip()}",
        "Content-Type": "application/json"
    }

    # --- DAQUI PARA BAIXO SEGUE O RESTANTE DO SEU CÓDIGO DE UPLOAD ---
    print("📡 Tentando conexão com a API do Roblox...")
    # (Adicione aqui as funções de requests.post para o arquivo rbxm)

if __name__ == "__main__":
    main()
