# -*- coding: utf-8 -*-
"""
场景API
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from flask_login import current_user
from models.user import db
from models.scene import Scene, SceneTemplate
from utils.auth import login_required, log_operation

scenes_bp = Blueprint('scenes', __name__, url_prefix='/api/v1/scenes')


@scenes_bp.route('', methods=['GET'])
@login_required
def get_scenes():
    """获取场景列表"""
    scenes = Scene.query.order_by(Scene.is_default.desc(), Scene.created_at.desc()).all()

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': [s.to_dict() for s in scenes]
    })


@scenes_bp.route('/<int:scene_id>', methods=['GET'])
@login_required
def get_scene(scene_id):
    """获取场景详情"""
    scene = Scene.query.get(scene_id)
    if not scene:
        return jsonify({'code': 404, 'message': '场景不存在', 'data': None})

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': scene.to_dict()
    })


@scenes_bp.route('', methods=['POST'])
@login_required
def create_scene():
    """创建场景"""
    data = request.get_json()
    name = data.get('name', '').strip()

    if not name:
        return jsonify({'code': 400, 'message': '场景名称不能为空', 'data': None})

    scene = Scene(
        name=name,
        description=data.get('description'),
        icon=data.get('icon', 'bi-grid-3x3-gap'),
        theme_color=data.get('theme_color', '#2D5BFF'),
        class_mapping=data.get('class_mapping'),
        focus_classes=data.get('focus_classes'),
        config=data.get('config'),
        is_default=data.get('is_default', 0),
        created_by=current_user.id
    )

    db.session.add(scene)
    db.session.commit()

    log_operation(current_user.id, 'create_scene', f'创建场景: {name}')

    return jsonify({
        'code': 200,
        'message': '创建成功',
        'data': scene.to_dict()
    })


@scenes_bp.route('/<int:scene_id>', methods=['PUT'])
@login_required
def update_scene(scene_id):
    """更新场景"""
    scene = Scene.query.get(scene_id)
    if not scene:
        return jsonify({'code': 404, 'message': '场景不存在', 'data': None})

    data = request.get_json()

    if 'name' in data:
        scene.name = data['name']
    if 'description' in data:
        scene.description = data['description']
    if 'icon' in data:
        scene.icon = data['icon']
    if 'theme_color' in data:
        scene.theme_color = data['theme_color']
    if 'class_mapping' in data:
        scene.class_mapping = data['class_mapping']
    if 'focus_classes' in data:
        scene.focus_classes = data['focus_classes']
    if 'config' in data:
        scene.config = data['config']
    if 'is_default' in data:
        scene.is_default = data['is_default']

    db.session.commit()

    log_operation(current_user.id, 'update_scene', f'更新场景: {scene.name}')

    return jsonify({
        'code': 200,
        'message': '更新成功',
        'data': scene.to_dict()
    })


@scenes_bp.route('/<int:scene_id>', methods=['DELETE'])
@login_required
def delete_scene(scene_id):
    """删除场景"""
    scene = Scene.query.get(scene_id)
    if not scene:
        return jsonify({'code': 404, 'message': '场景不存在', 'data': None})

    if scene.is_default:
        return jsonify({'code': 400, 'message': '不能删除默认场景', 'data': None})

    db.session.delete(scene)
    db.session.commit()

    log_operation(current_user.id, 'delete_scene', f'删除场景: {scene.name}')

    return jsonify({'code': 200, 'message': '删除成功', 'data': None})


@scenes_bp.route('/<int:scene_id>/clone', methods=['POST'])
@login_required
def clone_scene(scene_id):
    """克隆场景"""
    scene = Scene.query.get(scene_id)
    if not scene:
        return jsonify({'code': 404, 'message': '场景不存在', 'data': None})

    data = request.get_json() or {}

    new_scene = Scene(
        name=data.get('name', f'{scene.name}_副本'),
        description=scene.description,
        icon=scene.icon,
        theme_color=scene.theme_color,
        class_mapping=scene.class_mapping,
        focus_classes=scene.focus_classes,
        config=scene.config,
        is_default=0,
        created_by=current_user.id
    )

    db.session.add(new_scene)
    db.session.commit()

    log_operation(current_user.id, 'clone_scene', f'克隆场景: {scene.name}')

    return jsonify({
        'code': 200,
        'message': '克隆成功',
        'data': new_scene.to_dict()
    })


@scenes_bp.route('/<int:scene_id>/set-default', methods=['POST'])
@login_required
def set_default_scene(scene_id):
    """设置默认场景"""
    # 清除所有默认
    Scene.query.update({'is_default': 0})

    scene = Scene.query.get(scene_id)
    if not scene:
        return jsonify({'code': 404, 'message': '场景不存在', 'data': None})

    scene.is_default = 1
    db.session.commit()

    log_operation(current_user.id, 'set_default_scene', f'设置默认场景: {scene.name}')

    return jsonify({'code': 200, 'message': '设置成功', 'data': scene.to_dict()})


@scenes_bp.route('/templates', methods=['GET'])
@login_required
def get_templates():
    """获取场景模板列表"""
    category = request.args.get('category')

    query = SceneTemplate.query

    if category:
        query = query.filter_by(category=category)

    templates = query.order_by(SceneTemplate.created_at.desc()).all()

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': [t.to_dict() for t in templates]
    })


@scenes_bp.route('/templates/<int:template_id>', methods=['GET'])
@login_required
def get_template(template_id):
    """获取场景模板详情"""
    template = SceneTemplate.query.get(template_id)
    if not template:
        return jsonify({'code': 404, 'message': '模板不存在', 'data': None})

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': template.to_dict()
    })


@scenes_bp.route('/create-from-template/<int:template_id>', methods=['POST'])
@login_required
def create_from_template(template_id):
    """从模板创建场景"""
    template = SceneTemplate.query.get(template_id)
    if not template:
        return jsonify({'code': 404, 'message': '模板不存在', 'data': None})

    data = request.get_json() or {}
    config = template.config or {}

    scene = Scene(
        name=data.get('name', template.name),
        description=data.get('description', template.description),
        icon=config.get('icon', 'bi-grid-3x3-gap'),
        theme_color=config.get('theme_color', '#2D5BFF'),
        class_mapping=config.get('class_mapping'),
        focus_classes=config.get('focus_classes'),
        config=config.get('config'),
        is_default=0,
        created_by=current_user.id
    )

    db.session.add(scene)
    db.session.commit()

    log_operation(current_user.id, 'create_from_template', f'从模板创建场景: {scene.name}')

    return jsonify({
        'code': 200,
        'message': '创建成功',
        'data': scene.to_dict()
    })
