# -*- coding: utf-8 -*-
"""
认证API
处理用户登录、登出、注册等
"""

from flask import Blueprint, request, jsonify
from flask_login import login_user, logout_user, current_user
from datetime import datetime
from models.user import db, User
from utils.auth import login_required, log_operation

auth_bp = Blueprint('auth', __name__, url_prefix='/api/v1/auth')


@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'code': 400, 'message': '用户名和密码不能为空', 'data': None})

    user = User.query.filter_by(username=username).first()

    if not user or not user.check_password(password):
        return jsonify({'code': 401, 'message': '用户名或密码错误', 'data': None})

    if user.status == 0:
        return jsonify({'code': 403, 'message': '账户已被禁用', 'data': None})

    # 更新最后登录时间
    user.last_login = datetime.now()
    db.session.commit()

    # 登录用户
    login_user(user, remember=data.get('remember', False))

    # 记录操作日志
    log_operation(user.id, 'login', '用户登录')

    return jsonify({
        'code': 200,
        'message': '登录成功',
        'data': user.to_dict()
    })


@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """用户登出"""
    if current_user.is_authenticated:
        log_operation(current_user.id, 'logout', '用户登出')

    logout_user()
    return jsonify({'code': 200, 'message': '已登出', 'data': None})


@auth_bp.route('/info', methods=['GET'])
@login_required
def get_user_info():
    """获取当前用户信息"""
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': current_user.to_dict()
    })


@auth_bp.route('/password', methods=['PUT'])
@login_required
def change_password():
    """修改密码"""
    data = request.get_json()
    old_password = data.get('old_password', '')
    new_password = data.get('new_password', '')

    if not old_password or not new_password:
        return jsonify({'code': 400, 'message': '密码不能为空', 'data': None})

    if not current_user.check_password(old_password):
        return jsonify({'code': 400, 'message': '原密码错误', 'data': None})

    if len(new_password) < 6:
        return jsonify({'code': 400, 'message': '新密码长度不能少于6位', 'data': None})

    current_user.set_password(new_password)
    db.session.commit()

    log_operation(current_user.id, 'change_password', '修改密码')

    return jsonify({'code': 200, 'message': '密码修改成功', 'data': None})


@auth_bp.route('/profile', methods=['PUT'])
@login_required
def update_profile():
    """更新个人信息"""
    data = request.get_json()

    if 'email' in data:
        current_user.email = data['email']
    if 'real_name' in data:
        current_user.real_name = data['real_name']

    db.session.commit()

    log_operation(current_user.id, 'update_profile', '更新个人信息')

    return jsonify({
        'code': 200,
        'message': '更新成功',
        'data': current_user.to_dict()
    })
