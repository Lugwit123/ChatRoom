# send_api.py
import requests

def send_message(api_url, username, message):
    url = f"{api_url}/send_message"
    payload = {
        "username": username,
        "message": message
    }
    try:
        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()
        print("发送成功:", data)
    except requests.exceptions.RequestException as e:
        print("发送失败:", e)

if __name__ == "__main__":
    API_URL = "http://localhost:1026"      # 服务器API地址
    target_username = "send_api"           # 目标用户名
    message = "Hello from API!"

    send_message(API_URL, target_username, message)
