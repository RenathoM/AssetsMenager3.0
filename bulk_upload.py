import requests
import os
import json
import time

API_KEY = os.getenv("RBX_API_KEY")
MY_GROUP_ID = "633516837"
UNIVERSE_ID = "103111986841337"
event_path = os.getenv("GITHUB_EVENT_PATH")

with open(event_path, 'r') as f:
    payload = json.load(f).get("client_payload", {})

WEBHOOK_URL = payload.get("discord_webhook")
ORIGINAL_ID = payload.get("asset_id")
PLAYER_NAME = payload.get("player_name", "Unknown")
TARGET_USER_ID = payload.get("target_user_id")

def main():
    file_path = "item.rbxm"
    r_down = requests.get(f"https://assetdelivery.roblox.com/v1/asset/?id={ORIGINAL_ID}")
    
    if r_down.status_code == 200:
        with open(file_path, "wb") as f:
            f.write(r_down.content)
    else:
        return

    url = "https://apis.roblox.com/assets/v1/assets"
    asset_config = {
        "assetType": "Model",
        "displayName": f"Asset_{ORIGINAL_ID}",
        "creationContext": {"creator": {"groupId": str(MY_GROUP_ID)}}
    }
    
    with open(file_path, "rb") as f:
        files = {
            "request": (None, json.dumps(asset_config), "application/json"),
            "fileContent": ("model.rbxm", f, "application/octet-stream")
        }
        response = requests.post(url, headers={"x-api-key": API_KEY}, files=files)
    
    res_data = response.json()
    operation_path = res_data.get("path")
    final_asset_id = "N/A"

    if operation_path:
        for _ in range(15):
            time.sleep(2)
            op_res = requests.get(f"https://apis.roblox.com/assets/v1/{operation_path}", headers={"x-api-key": API_KEY})
            op_data = op_res.json()
            if op_data.get("done"):
                final_asset_id = op_data.get("response", {}).get("assetId", "N/A")
                print(f"ASSET_ID={final_asset_id}") # Crucial para o YAML
                break
    
    if WEBHOOK_URL and final_asset_id != "N/A":
        requests.post(WEBHOOK_URL, json={"content": f"✅ Asset Processed! ID: {final_asset_id}"})

if __name__ == "__main__":
    main()
