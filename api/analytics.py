# -*- coding: utf-8 -*-
"""
统计分析API
"""

import json
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from utils.auth import login_required
from utils.analytics import AnalyticsEngine

analytics_bp = Blueprint('analytics', __name__, url_prefix='/api/v1/analytics')


@analytics_bp.route('/dashboard', methods=['GET'])
@login_required
def get_dashboard_stats():
    """获取仪表盘统计数据"""
    stats = AnalyticsEngine.get_dashboard_stats()

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': stats
    })


@analytics_bp.route('/detection-trend', methods=['GET'])
@login_required
def get_detection_trend():
    """获取检测趋势"""
    days = request.args.get('days', 7, type=int)
    trend = AnalyticsEngine.get_detection_trend(days)

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': trend
    })


@analytics_bp.route('/class-distribution', methods=['GET'])
@login_required
def get_class_distribution():
    """获取类别分布"""
    task_id = request.args.get('task_id', type=int)
    days = request.args.get('days', 7, type=int)
    distribution = AnalyticsEngine.get_class_distribution(task_id, days)

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': distribution
    })


@analytics_bp.route('/alert-trend', methods=['GET'])
@login_required
def get_alert_trend():
    """获取告警趋势"""
    days = request.args.get('days', 7, type=int)
    categories_str = request.args.get('categories')
    
    alert_categories = None
    if categories_str:
        try:
            alert_categories = json.loads(categories_str)
        except:
            alert_categories = None
    
    trend = AnalyticsEngine.get_alert_trend(days, alert_categories)

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': trend
    })


@analytics_bp.route('/hourly-stats', methods=['GET'])
@login_required
def get_hourly_stats():
    """获取按小时统计"""
    device_id = request.args.get('device_id', type=int)
    date_str = request.args.get('date')

    date = None
    if date_str:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()

    stats = AnalyticsEngine.get_hourly_stats(device_id, date)

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': stats
    })


@analytics_bp.route('/device-stats', methods=['GET'])
@login_required
def get_device_stats():
    """获取设备统计"""
    stats = AnalyticsEngine.get_device_stats()

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': stats
    })


@analytics_bp.route('/comparison', methods=['GET'])
@login_required
def get_comparison():
    """获取对比分析"""
    period = request.args.get('period', 'week')  # week/month

    now = datetime.now()

    if period == 'week':
        current_end = now
        current_start = now - timedelta(days=7)
        previous_end = current_start
        previous_start = previous_end - timedelta(days=7)
    else:  # month
        current_end = now
        current_start = now - timedelta(days=30)
        previous_end = current_start
        previous_start = previous_end - timedelta(days=30)

    comparison = AnalyticsEngine.get_comparison_stats(
        current_start, current_end, previous_start, previous_end
    )

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': comparison
    })


@analytics_bp.route('/aggregate', methods=['POST'])
@login_required
def trigger_aggregate():
    """触发数据聚合"""
    date_str = request.json.get('date')
    date = None
    if date_str:
        date = datetime.strptime(date_str, '%Y-%m-%d').date()

    AnalyticsEngine.aggregate_stats(date)

    return jsonify({
        'code': 200,
        'message': '聚合完成',
        'data': None
    })
