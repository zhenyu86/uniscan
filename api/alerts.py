# -*- coding: utf-8 -*-
"""
告警API
处理告警管理和处置
"""

from flask import Blueprint, request, jsonify
from datetime import datetime
from flask_login import current_user
from models.user import db
from models.alert import Alert
from models.rule import AlertRule
from utils.auth import login_required, log_operation
from utils.alert_manager import AlertManager

alerts_bp = Blueprint('alerts', __name__, url_prefix='/api/v1/alerts')


@alerts_bp.route('', methods=['GET'])
@login_required
def get_alerts():
    """获取告警列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    level = request.args.get('level')
    status = request.args.get('status')
    rule_id = request.args.get('rule_id', type=int)
    start_time = request.args.get('start_time')
    end_time = request.args.get('end_time')

    filters = {}
    if level:
        filters['level'] = level
    if status:
        filters['status'] = status
    if rule_id:
        filters['rule_id'] = rule_id
    if start_time:
        filters['start_time'] = datetime.strptime(start_time, '%Y-%m-%d %H:%M:%S')
    if end_time:
        filters['end_time'] = datetime.strptime(end_time, '%Y-%m-%d %H:%M:%S')

    manager = AlertManager()
    result = manager.get_alerts(filters, page, per_page)

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': result
    })


@alerts_bp.route('/stats', methods=['GET'])
@login_required
def get_alert_stats():
    """获取告警统计"""
    manager = AlertManager()
    stats = manager.get_alert_stats()

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': stats
    })


@alerts_bp.route('/recent', methods=['GET'])
@login_required
def get_recent_alerts():
    """获取最近告警"""
    limit = request.args.get('limit', 5, type=int)
    manager = AlertManager()
    alerts = manager.get_recent_alerts(limit)

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': alerts
    })


@alerts_bp.route('/<int:alert_id>', methods=['GET'])
@login_required
def get_alert(alert_id):
    """获取告警详情"""
    alert = Alert.query.get(alert_id)
    if not alert:
        return jsonify({'code': 404, 'message': '告警不存在', 'data': None})

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': alert.to_dict()
    })


@alerts_bp.route('/<int:alert_id>/handle', methods=['POST'])
@login_required
def handle_alert(alert_id):
    """处置告警"""
    data = request.get_json()
    status = data.get('status', 'resolved')
    note = data.get('note', '')

    manager = AlertManager()
    success = manager.handle_alert(alert_id, current_user.id, status, note)

    if success:
        log_operation(current_user.id, 'handle_alert', f'处置告警: {alert_id}')

        return jsonify({'code': 200, 'message': '处置成功', 'data': None})
    else:
        return jsonify({'code': 500, 'message': '处置失败', 'data': None})


@alerts_bp.route('/batch-handle', methods=['POST'])
@login_required
def batch_handle_alerts():
    """批量处置告警"""
    data = request.get_json()
    alert_ids = data.get('alert_ids', [])
    status = data.get('status', 'resolved')
    note = data.get('note', '')

    if not alert_ids:
        return jsonify({'code': 400, 'message': '请选择告警', 'data': None})

    manager = AlertManager()
    success_count = 0

    for alert_id in alert_ids:
        if manager.handle_alert(alert_id, current_user.id, status, note):
            success_count += 1

    log_operation(current_user.id, 'batch_handle_alerts', f'批量处置告警: {len(alert_ids)}条')

    return jsonify({
        'code': 200,
        'message': f'成功处置{success_count}条告警',
        'data': {'success_count': success_count}
    })
