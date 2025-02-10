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
API_BASE_URL = "http://127.0.0.1:1026"
BASE_URL = API_BASE_URL
LOGIN_URL = f"{BASE_URL}/api/auth/login"
USERS_MAP_URL = f"{BASE_URL}/api/users/users_map"

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
        # 使用 form-data 格式发送数据
        data = {
            "username": username,
            "password": password,
            "grant_type": "password"  # OAuth2 要求的字段
        }
        
        lprint(f"发送登录请求到 {LOGIN_URL}")
        lprint(f"请求数据: {data}")
        
        response = requests.post(
            LOGIN_URL,
            data=data,  # 使用 data 而不是 json
            headers={
                "accept": "application/json",
                "Content-Type": "application/x-www-form-urlencoded"  # 指定 form-data 格式
            }
        )
        
        # 记录响应状态和内容
        lprint(f"响应状态码: {response.status_code}")
        lprint(f"响应头: {dict(response.headers)}")
        
        try:
            response_json = response.json()
            lprint(f"响应内容: {response_json}")
        except:
            lprint(f"响应内容(非JSON): {response.text}")
            
        response.raise_for_status()
        return response.json()
        
    except requests.exceptions.RequestException as e:
        lprint(f"登录请求失败: {str(e)}")
        traceback.print_exc()
        raise
    except Exception as e:
        lprint(f"登录过程中发生错误: {str(e)}")
        traceback.print_exc()
        raise

def get_users_map(token: str) -> Dict[str, Any]:
    """获取用户映射信息"""
    try:
        lprint("尝试获取用户映射信息", locals())
        headers = {
            "Authorization": f"Bearer {token}",
            "accept": "application/json"
        }
        params = { "token": token }  # 加入query参数以满足依赖需求
        response = requests.get(
            USERS_MAP_URL,
            headers=headers,
            params=params,
            timeout=5
        )
        lprint(f"用户映射API响应状态码: {response.status_code}", level=logging.INFO)
        if response.status_code == 200:
            users_map = response.json()
            lprint(f"成功获取用户映射: {json.dumps(users_map, indent=2, ensure_ascii=False)}", level=logging.INFO)
            return users_map
        elif response.status_code == 401:
            lprint("认证失败，token可能已过期", level=logging.ERROR)
            raise Exception("认证失败，请重新登录")
        else:
            lprint(f"获取用户映射失败，响应内容: {response.text}", level=logging.ERROR)
            raise Exception(response.text)
    except Exception as e:
        traceback.print_exc()
        raise

def main():
    """主函数"""
    try:
        # 登录并获取token
        username = "admin01"
        password = "666"
        login_result = login(username, password)
        lprint(f"登录成功: {login_result}", level=logging.INFO)
        
        # 获取token
        token = login_result.get("access_token")
        if not token:
            raise Exception("登录响应中没有access_token")
        
        # 获取用户映射
        response = get_users_map(token)
        lprint(response)
        
    except Exception as e:
        lprint(f"测试失败: {str(e)}", level=logging.ERROR)
        lprint(traceback.format_exc(), level=logging.ERROR)
        raise

if __name__ == "__main__":
    main()
