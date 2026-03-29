# -*- coding: utf-8 -*-
"""
统计分析引擎
提供数据分析和报表功能
"""

from datetime import datetime, timedelta
from sqlalchemy import func, and_, case
from models.user import db
from models.task import DetectionTask, DetectionResult
from models.alert import Alert
from models.device import Device
from models.config import TrafficStats
import json


class AnalyticsEngine:
    """统计分析引擎类"""

    @staticmethod
    def get_dashboard_stats():
        """
        获取仪表盘统计数据

        Returns:
            dict: 统计数据
        """
        # 任务统计
        total_tasks = DetectionTask.query.count()
        completed_tasks = DetectionTask.query.filter_by(status='completed').count()
        processing_tasks = DetectionTask.query.filter_by(status='processing').count()
        failed_tasks = DetectionTask.query.filter_by(status='failed').count()

        # 告警统计
        total_alerts = Alert.query.count()
        pending_alerts = Alert.query.filter_by(status='pending').count()
        critical_alerts = Alert.query.filter_by(level='critical').count()

        # 设备统计
        total_devices = Device.query.count()
        online_devices = Device.query.filter_by(status=1).count()

        # 今日统计
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_tasks = DetectionTask.query.filter(DetectionTask.created_at >= today).count()
        today_alerts = Alert.query.filter(Alert.created_at >= today).count()

        return {
            'tasks': {
                'total': total_tasks,
                'completed': completed_tasks,
                'processing': processing_tasks,
                'failed': failed_tasks,
                'today': today_tasks
            },
            'alerts': {
                'total': total_alerts,
                'pending': pending_alerts,
                'critical': critical_alerts,
                'today': today_alerts
            },
            'devices': {
                'total': total_devices,
                'online': online_devices,
                'offline': total_devices - online_devices
            }
        }

    @staticmethod
    def get_detection_trend(days=7):
        """
        获取检测趋势数据

        Args:
            days: 天数

        Returns:
            list: 趋势数据
        """
        start_date = datetime.now() - timedelta(days=days)

        # 按日期统计任务数
        results = db.session.query(
            func.date(DetectionTask.created_at).label('date'),
            func.count(DetectionTask.id).label('count')
        ).filter(
            DetectionTask.created_at >= start_date
        ).group_by(
            func.date(DetectionTask.created_at)
        ).order_by('date').all()

        return [
            {'date': r.date.strftime('%Y-%m-%d'), 'count': r.count}
            for r in results
        ]

    @staticmethod
    def get_class_distribution(task_id=None, days=7):
        """
        获取类别分布

        Args:
            task_id: 任务ID（可选）
            days: 天数

        Returns:
            list: 类别分布数据
        """
        query = db.session.query(
            DetectionResult.class_name,
            func.count(DetectionResult.id).label('count')
        )

        if task_id:
            query = query.filter(DetectionResult.task_id == task_id)
        else:
            start_date = datetime.now() - timedelta(days=days)
            query = query.join(DetectionTask).filter(
                DetectionTask.created_at >= start_date
            )

        results = query.group_by(DetectionResult.class_name).order_by(
            func.count(DetectionResult.id).desc()
        ).limit(10).all()

        return [
            {'name': r.class_name, 'value': r.count}
            for r in results
        ]

    @staticmethod
    def get_alert_trend(days=7, alert_categories=None):
        """
        获取告警趋势（按配置的告警类别统计检测结果）

        Args:
            days: 天数
            alert_categories: 告警类别列表（可选）

        Returns:
            list: 趋势数据
        """
        start_date = datetime.now() - timedelta(days=days)

        # 如果没有传入告警类别，从数据库获取
        if not alert_categories:
            from models.config import SystemConfig
            config = SystemConfig.query.filter_by(config_key='alert_categories').first()
            if config and config.config_value:
                try:
                    alert_categories = json.loads(config.config_value)
                except:
                    alert_categories = []
        
        # 如果没有配置告警类别，返回空列表
        if not alert_categories:
            return []
        
        # 获取启用的类别名称
        enabled_categories = [cat['name'] for cat in alert_categories if cat.get('enabled', True)]
        
        if not enabled_categories:
            return []

        # 从检测结果表中统计各类别的数量
        results = db.session.query(
            func.date(DetectionResult.created_at).label('date'),
            DetectionResult.class_name,
            func.count(DetectionResult.id).label('count')
        ).filter(
            and_(
                DetectionResult.created_at >= start_date,
                DetectionResult.class_name.in_(enabled_categories)
            )
        ).group_by(
            func.date(DetectionResult.created_at),
            DetectionResult.class_name
        ).order_by('date').all()

        # 如果没有数据，返回空列表
        if not results:
            return []

        # 按日期组织数据
        trend_data = {}
        for r in results:
            date_str = r.date.strftime('%Y-%m-%d')
            if date_str not in trend_data:
                trend_data[date_str] = {'date': date_str}
                # 初始化所有启用的类别为0
                for cat in enabled_categories:
                    trend_data[date_str][cat] = 0
            trend_data[date_str][r.class_name] = r.count

        return list(trend_data.values())

    @staticmethod
    def get_hourly_stats(device_id=None, date=None):
        """
        获取按小时统计

        Args:
            device_id: 设备ID
            date: 日期

        Returns:
            list: 小时统计数据
        """
        if date is None:
            date = datetime.now().date()

        query = TrafficStats.query.filter_by(stat_date=date)

        if device_id:
            query = query.filter_by(device_id=device_id)

        results = query.order_by(TrafficStats.stat_hour).all()

        hourly_data = [0] * 24
        for r in results:
            hourly_data[r.stat_hour] = r.total_detections

        return hourly_data

    @staticmethod
    def get_device_stats():
        """
        获取设备统计

        Returns:
            list: 设备统计数据
        """
        results = db.session.query(
            Device.name,
            Device.status,
            func.count(DetectionTask.id).label('task_count')
        ).outerjoin(
            DetectionTask, Device.id == DetectionTask.source_id
        ).group_by(Device.id, Device.name, Device.status).all()

        return [
            {
                'name': r.name,
                'status': r.status,
                'task_count': r.task_count
            }
            for r in results
        ]

    @staticmethod
    def get_comparison_stats(current_start, current_end, previous_start, previous_end):
        """
        获取对比分析数据（同比/环比）

        Args:
            current_start: 当前开始时间
            current_end: 当前结束时间
            previous_start: 对比开始时间
            previous_end: 对比结束时间

        Returns:
            dict: 对比数据
        """
        # 当前周期
        current_tasks = DetectionTask.query.filter(
            and_(DetectionTask.created_at >= current_start,
                 DetectionTask.created_at <= current_end)
        ).count()

        current_alerts = Alert.query.filter(
            and_(Alert.created_at >= current_start,
                 Alert.created_at <= current_end)
        ).count()

        # 对比周期
        previous_tasks = DetectionTask.query.filter(
            and_(DetectionTask.created_at >= previous_start,
                 DetectionTask.created_at <= previous_end)
        ).count()

        previous_alerts = Alert.query.filter(
            and_(Alert.created_at >= previous_start,
                 Alert.created_at <= previous_end)
        ).count()

        # 计算变化率
        task_change = ((current_tasks - previous_tasks) / previous_tasks * 100) if previous_tasks else 0
        alert_change = ((current_alerts - previous_alerts) / previous_alerts * 100) if previous_alerts else 0

        return {
            'current': {
                'tasks': current_tasks,
                'alerts': current_alerts
            },
            'previous': {
                'tasks': previous_tasks,
                'alerts': previous_alerts
            },
            'change': {
                'tasks': round(task_change, 2),
                'alerts': round(alert_change, 2)
            }
        }

    @staticmethod
    def aggregate_stats(date=None):
        """
        聚合统计数据

        Args:
            date: 日期（默认为今天）
        """
        if date is None:
            date = datetime.now().date()

        # 获取所有设备
        devices = Device.query.all()
        scenes = [None]  # 可以扩展为多个场景

        for device in devices:
            for scene_id in scenes:
                # 统计每小时数据
                for hour in range(24):
                    start_time = datetime.combine(date, datetime.min.time()) + timedelta(hours=hour)
                    end_time = start_time + timedelta(hours=1)

                    # 统计检测结果
                    count = db.session.query(func.count(DetectionResult.id)).join(
                        DetectionTask
                    ).filter(
                        and_(
                            DetectionTask.source_id == device.id,
                            DetectionTask.created_at >= start_time,
                            DetectionTask.created_at < end_time
                        )
                    ).scalar()

                    # 统计类别分布
                    class_stats = db.session.query(
                        DetectionResult.class_name,
                        func.count(DetectionResult.id)
                    ).join(DetectionTask).filter(
                        and_(
                            DetectionTask.source_id == device.id,
                            DetectionTask.created_at >= start_time,
                            DetectionTask.created_at < end_time
                        )
                    ).group_by(DetectionResult.class_name).all()

                    class_stats_dict = {name: cnt for name, cnt in class_stats}

                    # 保存或更新统计记录
                    stat = TrafficStats.query.filter_by(
                        device_id=device.id,
                        scene_id=scene_id,
                        stat_date=date,
                        stat_hour=hour
                    ).first()

                    if stat:
                        stat.total_detections = count
                        stat.class_stats = class_stats_dict
                    else:
                        stat = TrafficStats(
                            device_id=device.id,
                            scene_id=scene_id,
                            stat_date=date,
                            stat_hour=hour,
                            total_detections=count,
                            class_stats=class_stats_dict
                        )
                        db.session.add(stat)

        db.session.commit()
