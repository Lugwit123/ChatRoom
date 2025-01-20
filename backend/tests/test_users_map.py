import os
import sys
import json
import logging
import requests
from datetime import datetime
from zoneinfo import ZoneInfo
import traceback
from typing import Dict, Any

# 添加项目根目录到Python路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

# 导入日志模块
import Lugwit_Module as LM
lprint = LM.lprint

# API配置
BASE_URL = "http://127.0.0.1:1026"
LOGIN_URL = f"{BASE_URL}/api/auth/login"
USERS_MAP_URL = f"{BASE_URL}/api/user/users_map"
API_BASE_URL = BASE_URL

def login(username: str, password: str) -> dict:
    """登录用户并获取token
    
    Args:
        username: 用户名
        password: 密码
        
    Returns:
        登录响应信息
    """
    try:
        lprint(f"尝试登录用户: {username}", level=logging.INFO)
        response = requests.post(
            LOGIN_URL,
            data={
                "username": username,
                "password": password,
                "grant_type": "password"  # OAuth2 要求的字段
            }
        )
        response.raise_for_status()
        return response.json()
    except Exception as e:
        lprint(f"登录失败: {str(e)}", level=logging.ERROR)
        raise

def get_users_map(token: str) -> Dict[str, Any]:
    """获取用户映射信息"""
    try:
        lprint("尝试获取用户映射信息", level=logging.INFO)
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.get(
            f"{API_BASE_URL}/api/user/users_map",
            headers=headers,
            timeout=5
        )
        lprint(f"用户映射API响应状态码: {response.status_code}", level=logging.INFO)
        if response.status_code == 200:
            users_map = response.json()
            lprint(f"成功获取用户映射: {json.dumps(users_map, indent=2, ensure_ascii=False)}", level=logging.INFO)
            return users_map
        else:
            lprint(f"获取用户映射失败，响应内容: {response.text}", level=logging.ERROR)
            raise Exception(response.text)
    except Exception as e:
        lprint(f"获取用户映射失败: {str(e)}", level=logging.ERROR)
        lprint(traceback.format_exc(), level=logging.ERROR)
        raise

def main():
    """主函数"""
    try:
        # 登录用户
        username = "admin01"
        password = "666"  # 修改为正确的密码
        login_result = login(username, password)
        lprint(f"登录成功: {json.dumps(login_result, indent=2, ensure_ascii=False)}", level=logging.INFO)
        
        # 获取token
        token = login_result["access_token"]
        
        # 获取用户映射
        response = get_users_map(token)

        
        # 检查当前用户信息
        current_user = response["current_user"]
        assert isinstance(current_user, dict), "当前用户信息必须是字典类型"
        
        # 检查用户映射
        user_map = response["user_map"]
        lprint(user_map)

            
        lprint("测试通过！所有字段类型和格式验证成功")
        
    except Exception as e:
        lprint(f"测试失败: {str(e)}", level=logging.ERROR)
        lprint(traceback.format_exc(), level=logging.ERROR)
        raise

if __name__ == "__main__":
    main()
