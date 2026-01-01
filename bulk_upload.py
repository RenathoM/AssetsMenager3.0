import requests
import os
import json
import time

MY_GROUP_ID = "633516837"
UNIVERSE_ID = "9469723620"
EVENT_PATH = os.getenv("GITHUB_EVENT_PATH")

def main():
    if not EVENT_PATH: return
    
    with open(EVENT_PATH, 'r') as f:
        payload = json.load(f).get("client_payload", {})

    # Identifica a categoria e o nome da variável esperada
    ASSET_CATEGORY = payload.get("asset_type", "Model") 
    token_env_name = f"RBX_TOKEN_{ASSET_CATEGORY.upper()}"
    USER_TOKEN = os.getenv(token_env_name)

    # VERIFICAÇÃO DE SEGURANÇA
    if not USER_TOKEN:
        print(f"❌ ERRO: O GitHub não forneceu a variável {token_env_name}")
        print(f"⚠️ Certifique-se de que o Secret '{token_env_name}' existe no GitHub.")
        return

    # Se chegou aqui, o token existe. Vamos tentar o upload:
    ORIGINAL_ID = payload.get("asset_id")
    headers = {"Authorization": f"Bearer {USER_TOKEN}"}
    
    # ... (Restante do código de download e upload)
    
    # Execute e veja o log. Se aparecer "Erro na API do Roblox", 
    # o token existe mas é INVÁLIDO (Expirou ou não tem permissão no grupo).
