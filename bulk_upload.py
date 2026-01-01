import requests
import os
import json
import time

# O Python vai procurar por estes nomes exatos que você configurou no YAML
def main():
    # ... (leitura do payload)
    ASSET_CATEGORY = payload.get("asset_type", "Model") 
    token_env_name = f"RBX_TOKEN_{ASSET_CATEGORY.upper()}"
    USER_TOKEN = os.getenv(token_env_name)

    if not USER_TOKEN:
        print(f"❌ Erro Crítico: A variável {token_env_name} está vazia!")
        return

    with open(EVENT_PATH, 'r') as f:
        payload = json.load(f).get("client_payload", {})

    # Identifica qual token o script vai tentar usar
    category = payload.get("asset_type", "Model").upper()
    token_name = f"RBX_TOKEN_{category}"
    USER_TOKEN = os.getenv(token_name)

    # PRINT DE DIAGNÓSTICO (Aparecerá no log do GitHub)
    if not USER_TOKEN:
        print(f"❌ ERRO: O Secret '{token_name}' não foi encontrado no ambiente do GitHub!")
        print(f"⚠️ Verifique se você criou o segredo com esse nome exato nas configurações do repositório.")
        return
    else:
        print(f"✅ Token '{token_name}' carregado com sucesso (Início: {USER_TOKEN[:10]}...)")

    # Tenta o Upload
    url = "https://apis.roblox.com/assets/v1/assets"
    headers = {"Authorization": f"Bearer {USER_TOKEN.strip()}"}
    
    # ... (Restante do código de upload)
    # Se o erro "Failed to read token" persistir aqui, o token existe mas é INVÁLIDO ou expirou.
