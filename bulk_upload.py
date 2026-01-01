import requests
import os

cookie = os.getenv("ROBLOX_COOKIE")

def check():
    if not cookie:
        print("❌ ERRO: O segredo ROBLOX_COOKIE não foi encontrado pelo GitHub.")
        return

    headers = {"Cookie": f".ROBLOSECURITY={cookie}"}
    # Tentamos acessar os dados do usuário logado
    res = requests.get("https://users.roblox.com/v1/users/authenticated", headers=headers)
    
    if res.status_code == 200:
        data = res.json()
        print(f"✅ COOKIE VÁLIDO! Logado como: {data.get('name')} (ID: {data.get('id')})")
    else:
        print(f"❌ COOKIE INVÁLIDO OU EXPIRADO. Status: {res.status_code}")
        print("Dica: Certifique-se de que o valor começa com _|WARNING:-DO-NOT-SHARE-")

if __name__ == "__main__":
    check()
