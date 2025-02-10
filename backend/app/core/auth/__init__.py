"""认证模块"""
from .facade.auth_facade import AuthFacade, get_current_user

__all__ = ['AuthFacade', 'get_current_user']
