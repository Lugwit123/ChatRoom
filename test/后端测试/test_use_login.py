import requests
import json
import sys
import os
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# 导入日志模块
import Lugwit_Module as LM
lprint = LM.lprint

# API配置
BASE_URL = "http://127.0.0.1:1026"
LOGIN_URL = f"{BASE_URL}/api/auth/login"
USERS_MAP_URL = f"{BASE_URL}/api/users/map"


def login(username: str, password: str) -> dict:
    """
    登录并获取token
    """
    try:
        lprint(f"尝试登录用户: {username}", level=logging.INFO)
        response = requests.post(
            LOGIN_URL,
            data={
                "username": username,
                "password": password
            }
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        lprint(f"登录失败: {str(e)}", level=logging.ERROR)
        return None

def get_users_map(token: str) -> dict:
    """
    获取用户映射信息
    """
    try:
        lprint("尝试获取用户映射信息", level=logging.INFO)
        headers = {
            "Authorization": f"Bearer {token}"
        }
        response = requests.get(USERS_MAP_URL, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        lprint(f"获取用户映射失败: {str(e)}", level=logging.ERROR)
        return None

def test_login():
    """测试登录功能"""
    try:
        # 发送登录请求
        response = requests.post(
            LOGIN_URL,
            data={
                "username": "system01",
                "password": "666",
                "grant_type": "password"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        # 打印响应结果
        lprint(f"响应状态码: {response.status_code}")
        lprint(f"响应内容: {response.text}")
        
        # 验证结果
        assert response.status_code == 200, f"登录失败: {response.text}"
        data = response.json()
        assert "access_token" in data, "响应中没有access_token"
        lprint("登录成功")
            
    except Exception as e:
        lprint(f"测试出错: {str(e)}")
        raise
            
def main():
    # 1. 登录测试
    username = "admin01"
    password = "666"
    
    login_result = login(username, password)
    if not login_result:
        lprint("登录失败，测试终止", level=logging.ERROR)
        return
    
    lprint(f"登录成功: {json.dumps(login_result, indent=2, ensure_ascii=False)}", level=logging.INFO)
    
    # 2. 获取用户映射
    token = login_result.get("access_token")
    if not token:
        lprint("未获取到token，测试终止", level=logging.ERROR)
        return

if __name__ == "__main__":
    main()
