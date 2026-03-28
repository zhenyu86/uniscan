# -*- coding: utf-8 -*-
"""
系统设置API
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from flask_login import current_user
from models.user import db, User, OperationLog
from models.config import SystemConfig, ModelVersion, DashboardConfig
from utils.auth import login_required, admin_required, log_operation

settings_bp = Blueprint('settings', __name__, url_prefix='/api/v1/settings')


# ==================== 用户管理 ====================

@settings_bp.route('/users', methods=['GET'])
@admin_required
def get_users():
    """获取用户列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    role = request.args.get('role')
    status = request.args.get('status', type=int)
    keyword = request.args.get('keyword', '').strip()

    query = User.query

    if role:
        query = query.filter_by(role=role)
    if status is not None:
        query = query.filter_by(status=status)
    if keyword:
        query = query.filter(
            db.or_(
                User.username.contains(keyword),
                User.real_name.contains(keyword),
                User.email.contains(keyword)
            )
        )

    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'items': [u.to_dict() for u in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page
        }
    })


@settings_bp.route('/users', methods=['POST'])
@admin_required
def create_user():
    """创建用户"""
    data = request.get_json()
    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return jsonify({'code': 400, 'message': '用户名和密码不能为空', 'data': None})

    if len(password) < 6:
        return jsonify({'code': 400, 'message': '密码长度不能少于6位', 'data': None})

    # 检查用户名是否存在
    if User.query.filter_by(username=username).first():
        return jsonify({'code': 400, 'message': '用户名已存在', 'data': None})

    user = User(
        username=username,
        email=data.get('email'),
        real_name=data.get('real_name'),
        role=data.get('role', 'viewer'),
        status=data.get('status', 1)
    )
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    log_operation(current_user.id, 'create_user', f'创建用户: {username}')

    return jsonify({
        'code': 200,
        'message': '创建成功',
        'data': user.to_dict()
    })


@settings_bp.route('/users/<int:user_id>', methods=['GET'])
@admin_required
def get_user(user_id):
    """获取用户详情"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'code': 404, 'message': '用户不存在', 'data': None})

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': user.to_dict()
    })


@settings_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """更新用户"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'code': 404, 'message': '用户不存在', 'data': None})

    data = request.get_json()

    if 'email' in data:
        user.email = data['email']
    if 'real_name' in data:
        user.real_name = data['real_name']
    if 'role' in data:
        user.role = data['role']
    if 'status' in data:
        user.status = data['status']

    db.session.commit()

    log_operation(current_user.id, 'update_user', f'更新用户: {user.username}')

    return jsonify({
        'code': 200,
        'message': '更新成功',
        'data': user.to_dict()
    })


@settings_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """删除用户"""
    if user_id == current_user.id:
        return jsonify({'code': 400, 'message': '不能删除当前用户', 'data': None})

    user = User.query.get(user_id)
    if not user:
        return jsonify({'code': 404, 'message': '用户不存在', 'data': None})

    db.session.delete(user)
    db.session.commit()

    log_operation(current_user.id, 'delete_user', f'删除用户: {user.username}')

    return jsonify({'code': 200, 'message': '删除成功', 'data': None})


@settings_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@admin_required
def reset_user_password(user_id):
    """重置用户密码"""
    user = User.query.get(user_id)
    if not user:
        return jsonify({'code': 404, 'message': '用户不存在', 'data': None})

    data = request.get_json()
    new_password = data.get('password', '123456')

    if len(new_password) < 6:
        return jsonify({'code': 400, 'message': '密码长度不能少于6位', 'data': None})

    user.set_password(new_password)
    db.session.commit()

    log_operation(current_user.id, 'reset_password', f'重置用户密码: {user.username}')

    return jsonify({'code': 200, 'message': '密码重置成功', 'data': None})


# ==================== 模型管理 ====================

@settings_bp.route('/models', methods=['GET'])
@admin_required
def get_models():
    """获取模型列表"""
    models = ModelVersion.query.order_by(ModelVersion.created_at.desc()).all()

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': [m.to_dict() for m in models]
    })


@settings_bp.route('/models/active', methods=['GET'])
@login_required
def get_active_model():
    """获取当前激活模型"""
    model = ModelVersion.query.filter_by(is_active=1).first()

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': model.to_dict() if model else None
    })


@settings_bp.route('/models/<int:model_id>/activate', methods=['POST'])
@admin_required
def activate_model(model_id):
    """激活模型"""
    # 清除所有激活状态
    ModelVersion.query.update({'is_active': 0})

    model = ModelVersion.query.get(model_id)
    if not model:
        return jsonify({'code': 404, 'message': '模型不存在', 'data': None})

    model.is_active = 1
    db.session.commit()

    log_operation(current_user.id, 'activate_model', f'激活模型: {model.version}')

    return jsonify({
        'code': 200,
        'message': '激活成功',
        'data': model.to_dict()
    })


# ==================== 系统配置 ====================

@settings_bp.route('/configs', methods=['GET'])
@login_required
def get_configs():
    """获取系统配置"""
    configs = SystemConfig.query.all()

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': [c.to_dict() for c in configs]
    })


@settings_bp.route('/configs/<key>', methods=['GET'])
@login_required
def get_config(key):
    """获取单个配置"""
    config = SystemConfig.query.filter_by(config_key=key).first()
    if not config:
        return jsonify({'code': 404, 'message': '配置不存在', 'data': None})

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': config.to_dict()
    })


@settings_bp.route('/configs', methods=['PUT'])
@login_required
def update_configs():
    """批量更新配置"""
    data = request.get_json()
    configs = data.get('configs', [])

    for item in configs:
        key = item.get('key')
        value = item.get('value')

        config = SystemConfig.query.filter_by(config_key=key).first()
        if config:
            config.config_value = str(value)
            config.updated_at = datetime.now()
        else:
            # 自动创建不存在的配置
            config = SystemConfig(
                config_key=key,
                config_value=str(value),
                config_type='string',
                description=f'用户创建的配置: {key}',
                updated_at=datetime.now()
            )
            db.session.add(config)

    db.session.commit()

    log_operation(current_user.id, 'update_configs', '更新系统配置')

    return jsonify({'code': 200, 'message': '更新成功', 'data': None})


# ==================== 操作日志 ====================

@settings_bp.route('/logs', methods=['GET'])
@admin_required
def get_operation_logs():
    """获取操作日志"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    user_id = request.args.get('user_id', type=int)
    action = request.args.get('action')

    query = OperationLog.query

    if user_id:
        query = query.filter_by(user_id=user_id)
    if action:
        query = query.filter(OperationLog.action.contains(action))

    pagination = query.order_by(OperationLog.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'items': [log.to_dict() for log in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page
        }
    })


@settings_bp.route('/logs/<int:log_id>', methods=['DELETE'])
@admin_required
def delete_log(log_id):
    """删除单条操作日志"""
    log = OperationLog.query.get(log_id)
    if not log:
        return jsonify({'code': 404, 'message': '日志不存在', 'data': None})

    db.session.delete(log)
    db.session.commit()

    return jsonify({'code': 200, 'message': '删除成功', 'data': None})


@settings_bp.route('/logs/clear', methods=['DELETE'])
@admin_required
def clear_logs():
    """清空所有操作日志"""
    try:
        deleted = OperationLog.query.delete()
        db.session.commit()

        log_operation(current_user.id, 'clear_logs', f'清空操作日志: {deleted}条')

        return jsonify({'code': 200, 'message': f'已清空{deleted}条日志', 'data': None})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'清空失败: {str(e)}', 'data': None})


# ==================== 看板配置 ====================

@settings_bp.route('/dashboards', methods=['GET'])
@login_required
def get_dashboards():
    """获取看板列表"""
    scene_id = request.args.get('scene_id', type=int)

    query = DashboardConfig.query

    if scene_id:
        query = query.filter_by(scene_id=scene_id)

    # 包含公共看板和用户私有看板
    query = query.filter(
        db.or_(
            DashboardConfig.user_id.is_(None),
            DashboardConfig.user_id == current_user.id
        )
    )

    dashboards = query.order_by(DashboardConfig.created_at.desc()).all()

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': [d.to_dict() for d in dashboards]
    })


@settings_bp.route('/dashboards', methods=['POST'])
@login_required
def create_dashboard():
    """创建看板"""
    data = request.get_json()
    name = data.get('name', '').strip()

    if not name:
        return jsonify({'code': 400, 'message': '看板名称不能为空', 'data': None})

    dashboard = DashboardConfig(
        name=name,
        scene_id=data.get('scene_id'),
        user_id=current_user.id,
        layout=data.get('layout'),
        widgets=data.get('widgets'),
        is_default=data.get('is_default', 0)
    )

    db.session.add(dashboard)
    db.session.commit()

    return jsonify({
        'code': 200,
        'message': '创建成功',
        'data': dashboard.to_dict()
    })


@settings_bp.route('/dashboards/<int:dashboard_id>', methods=['PUT'])
@login_required
def update_dashboard(dashboard_id):
    """更新看板"""
    dashboard = DashboardConfig.query.get(dashboard_id)
    if not dashboard:
        return jsonify({'code': 404, 'message': '看板不存在', 'data': None})

    data = request.get_json()

    if 'name' in data:
        dashboard.name = data['name']
    if 'layout' in data:
        dashboard.layout = data['layout']
    if 'widgets' in data:
        dashboard.widgets = data['widgets']
    if 'is_default' in data:
        dashboard.is_default = data['is_default']

    db.session.commit()

    return jsonify({
        'code': 200,
        'message': '更新成功',
        'data': dashboard.to_dict()
    })


@settings_bp.route('/dashboards/<int:dashboard_id>', methods=['DELETE'])
@login_required
def delete_dashboard(dashboard_id):
    """删除看板"""
    dashboard = DashboardConfig.query.get(dashboard_id)
    if not dashboard:
        return jsonify({'code': 404, 'message': '看板不存在', 'data': None})

    db.session.delete(dashboard)
    db.session.commit()

    return jsonify({'code': 200, 'message': '删除成功', 'data': None})
