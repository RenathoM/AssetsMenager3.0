import requests
import os
import json

# Pega dados do Payload enviado pelo Roblox
event_payload = json.loads(os.getenv("GITHUB_EVENT_PAYLOAD", "{}"))
client_payload = event_payload.get("client_payload", {})

# Prioridade: ID enviado pelo jogo > ID fixo no segredo do GitHub
USER_ID = client_payload.get("target_user_id") or os.getenv("USER_ID")
EXPERIMENT_ID = client_payload.get("experiment_id")
PLAYER_NAME = client_payload.get("player_name", "Sistema")
API_KEY = os.getenv("ROBLOX_API_KEY")

ASSET_FOLDER = "assets/"
headers = {"x-api-key": API_KEY}

def upload_assets():
    results = [f"Relatório para {PLAYER_NAME}:"]
    
    for filename in os.listdir(ASSET_FOLDER):
        file_path = os.path.join(ASSET_FOLDER, filename)
        ext = filename.split('.')[-1].lower()
        asset_type = "Decal" if ext in ['png', 'jpg'] else "Model" if ext in ['fbx'] else "Audio"

        asset_config = {
            "assetType": asset_type,
            "displayName": f"{filename} (por {PLAYER_NAME})",
            "creationContext": {"creator": {"userId": USER_ID}}
        }

        with open(file_path, "rb") as f:
            files = {
                "request": (None, json.dumps(asset_config), "application/json"),
                "fileContent": (filename, f, "application/octet-stream")
            }
            response = requests.post("https://apis.roblox.com/assets/v1/assets", headers=headers, files=files)
            
            status = "✅" if response.status_code == 200 else "❌"
            results.append(f"{status} {filename}")

    # Envia feedback de volta para o jogo
    feedback_url = f"https://apis.roblox.com/messaging-service/v1/universes/{EXPERIMENT_ID}/topics/AssetUploadFeedback"
    requests.post(feedback_url, headers=headers, json={"message": json.dumps(results)})

if __name__ == "__main__":
    upload_assets()