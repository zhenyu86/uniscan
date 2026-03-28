# -*- coding: utf-8 -*-
"""
规则API
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from flask_login import current_user
from models.user import db
from models.rule import AlertRule
from models.scene import Scene
from utils.auth import login_required, log_operation
from utils.rule_engine import RuleEngine

rules_bp = Blueprint('rules', __name__, url_prefix='/api/v1/rules')


@rules_bp.route('', methods=['GET'])
@login_required
def get_rules():
    """获取规则列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    scene_id = request.args.get('scene_id', type=int)
    rule_type = request.args.get('rule_type')
    is_enabled = request.args.get('is_enabled', type=int)

    query = AlertRule.query

    if scene_id:
        query = query.filter_by(scene_id=scene_id)
    if rule_type:
        query = query.filter_by(rule_type=rule_type)
    if is_enabled is not None:
        query = query.filter_by(is_enabled=is_enabled)

    pagination = query.order_by(AlertRule.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'items': [r.to_dict() for r in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page
        }
    })


@rules_bp.route('/all', methods=['GET'])
@login_required
def get_all_rules():
    """获取所有规则（不分页）"""
    scene_id = request.args.get('scene_id', type=int)

    query = AlertRule.query

    if scene_id:
        query = query.filter_by(scene_id=scene_id)

    rules = query.order_by(AlertRule.created_at.desc()).all()

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': [r.to_dict() for r in rules]
    })


@rules_bp.route('/<int:rule_id>', methods=['GET'])
@login_required
def get_rule(rule_id):
    """获取规则详情"""
    rule = AlertRule.query.get(rule_id)
    if not rule:
        return jsonify({'code': 404, 'message': '规则不存在', 'data': None})

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': rule.to_dict()
    })


@rules_bp.route('', methods=['POST'])
@login_required
def create_rule():
    """创建规则"""
    data = request.get_json()
    name = data.get('name', '').strip()

    if not name:
        return jsonify({'code': 400, 'message': '规则名称不能为空', 'data': None})

    rule = AlertRule(
        name=name,
        scene_id=data.get('scene_id'),
        rule_type=data.get('rule_type', 'count'),
        conditions=data.get('conditions'),
        level=data.get('level', 'warning'),
        notify_methods=data.get('notify_methods'),
        is_enabled=data.get('is_enabled', 1)
    )

    db.session.add(rule)
    db.session.commit()

    log_operation(current_user.id, 'create_rule', f'创建规则: {name}')

    return jsonify({
        'code': 200,
        'message': '创建成功',
        'data': rule.to_dict()
    })


@rules_bp.route('/<int:rule_id>', methods=['PUT'])
@login_required
def update_rule(rule_id):
    """更新规则"""
    rule = AlertRule.query.get(rule_id)
    if not rule:
        return jsonify({'code': 404, 'message': '规则不存在', 'data': None})

    data = request.get_json()

    if 'name' in data:
        rule.name = data['name']
    if 'scene_id' in data:
        rule.scene_id = data['scene_id']
    if 'rule_type' in data:
        rule.rule_type = data['rule_type']
    if 'conditions' in data:
        rule.conditions = data['conditions']
    if 'level' in data:
        rule.level = data['level']
    if 'notify_methods' in data:
        rule.notify_methods = data['notify_methods']
    if 'is_enabled' in data:
        rule.is_enabled = data['is_enabled']

    db.session.commit()

    log_operation(current_user.id, 'update_rule', f'更新规则: {rule.name}')

    return jsonify({
        'code': 200,
        'message': '更新成功',
        'data': rule.to_dict()
    })


@rules_bp.route('/<int:rule_id>', methods=['DELETE'])
@login_required
def delete_rule(rule_id):
    """删除规则"""
    rule = AlertRule.query.get(rule_id)
    if not rule:
        return jsonify({'code': 404, 'message': '规则不存在', 'data': None})

    db.session.delete(rule)
    db.session.commit()

    log_operation(current_user.id, 'delete_rule', f'删除规则: {rule.name}')

    return jsonify({'code': 200, 'message': '删除成功', 'data': None})


@rules_bp.route('/<int:rule_id>/toggle', methods=['POST'])
@login_required
def toggle_rule(rule_id):
    """启用/禁用规则"""
    rule = AlertRule.query.get(rule_id)
    if not rule:
        return jsonify({'code': 404, 'message': '规则不存在', 'data': None})

    rule.is_enabled = 1 if rule.is_enabled == 0 else 0
    db.session.commit()

    status = '启用' if rule.is_enabled else '禁用'
    log_operation(current_user.id, 'toggle_rule', f'{status}规则: {rule.name}')

    return jsonify({
        'code': 200,
        'message': f'已{status}',
        'data': rule.to_dict()
    })


@rules_bp.route('/test', methods=['POST'])
@login_required
def test_rule():
    """测试规则"""
    data = request.get_json()

    rule_config = data.get('rule_config', {})
    test_detections = data.get('test_detections', [])

    engine = RuleEngine()
    result = engine.test_rule(rule_config, test_detections)

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': result
    })


@rules_bp.route('/types', methods=['GET'])
@login_required
def get_rule_types():
    """获取规则类型列表"""
    types = [
        {'value': 'count', 'label': '数量规则', 'description': '检测目标数量超过/低于阈值'},
        {'value': 'exists', 'label': '存在规则', 'description': '检测到指定目标'},
        {'value': 'area', 'label': '区域规则', 'description': '目标进入指定区域'},
        {'value': 'combination', 'label': '组合规则', 'description': '多个条件组合（AND/OR）'},
        {'value': 'trend', 'label': '趋势规则', 'description': '检测数量趋势变化'}
    ]

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': types
    })


@rules_bp.route('/levels', methods=['GET'])
@login_required
def get_alert_levels():
    """获取告警级别列表"""
    levels = [
        {'value': 'info', 'label': '提示', 'color': '#1890ff'},
        {'value': 'warning', 'label': '一般', 'color': '#faad14'},
        {'value': 'error', 'label': '重要', 'color': '#ff4d4f'},
        {'value': 'critical', 'label': '紧急', 'color': '#cf1322'}
    ]

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': levels
    })
