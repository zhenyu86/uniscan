# -*- coding: utf-8 -*-
"""
认证工具
提供登录验证和权限控制
"""

from functools import wraps
from flask import session, redirect, url_for, request, jsonify, g
from flask_login import current_user, login_required as flask_login_required
from datetime import datetime
from models.user import db, User, OperationLog


def login_required(f):
    """登录验证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查API请求
        if request.path.startswith('/api/'):
            if not current_user.is_authenticated:
                return jsonify({'code': 401, 'message': '请先登录', 'data': None}), 401
            return f(*args, **kwargs)

        # 页面请求
        if not current_user.is_authenticated:
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            if request.path.startswith('/api/'):
                return jsonify({'code': 401, 'message': '请先登录', 'data': None}), 401
            return redirect(url_for('login'))

        if current_user.role != 'admin':
            if request.path.startswith('/api/'):
                return jsonify({'code': 403, 'message': '权限不足', 'data': None}), 403
            return redirect(url_for('index'))

        return f(*args, **kwargs)

    return decorated_function


def role_required(*roles):
    """角色权限装饰器"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                if request.path.startswith('/api/'):
                    return jsonify({'code': 401, 'message': '请先登录', 'data': None}), 401
                return redirect(url_for('login'))

            if current_user.role not in roles:
                if request.path.startswith('/api/'):
                    return jsonify({'code': 403, 'message': '权限不足', 'data': None}), 403
                return redirect(url_for('index'))

            return f(*args, **kwargs)

        return decorated_function

    return decorator


def log_operation(user_id, action, target=None):
    """
    记录操作日志

    Args:
        user_id: 用户ID
        action: 操作类型
        target: 操作对象
    """
    try:
        log = OperationLog(
            user_id=user_id,
            action=action,
            target=target,
            ip_address=request.remote_addr if request else None,
            user_agent=request.user_agent.string if request else None
        )
        db.session.add(log)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"记录操作日志失败: {e}")


def get_current_user_info():
    """
    获取当前用户信息

    Returns:
        dict: 用户信息
    """
    if current_user.is_authenticated:
        return current_user.to_dict()
    return None


def check_permission(user, permission):
    """
    检查用户权限

    Args:
        user: 用户对象
        permission: 权限名称

    Returns:
        bool: 是否有权限
    """
    # 权限映射
    permission_map = {
        'admin': ['all'],
        'manager': ['view', 'detect', 'alert', 'scene', 'rule', 'analytics'],
        'operator': ['view', 'detect', 'alert'],
        'viewer': ['view']
    }

    user_permissions = permission_map.get(user.role, [])
    return 'all' in user_permissions or permission in user_permissions
