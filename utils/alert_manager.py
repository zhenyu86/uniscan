# -*- coding: utf-8 -*-
"""
告警管理器
处理告警生成、通知和处置
"""

from datetime import datetime
from models.user import db
from models.alert import Alert
from models.rule import AlertRule


class AlertManager:
    """告警管理器类"""

    _instance = None

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def create_alert(self, rule, task_id, device_id, message, details):
        """
        创建告警记录

        Args:
            rule: 触发的规则
            task_id: 检测任务ID
            device_id: 设备ID
            message: 告警内容
            details: 告警详情

        Returns:
            Alert: 告警对象
        """
        try:
            alert = Alert(
                rule_id=rule.id,
                device_id=device_id,
                task_id=task_id,
                level=rule.level,
                content=message,
                details=details,
                status='pending'
            )

            db.session.add(alert)

            # 更新规则触发次数
            rule.trigger_count = (rule.trigger_count or 0) + 1

            db.session.commit()

            # 发送通知
            self._send_notifications(alert, rule)

            return alert

        except Exception as e:
            db.session.rollback()
            print(f"创建告警失败: {e}")
            return None

    def get_alerts(self, filters=None, page=1, per_page=20):
        """
        获取告警列表

        Args:
            filters: 筛选条件
            page: 页码
            per_page: 每页数量

        Returns:
            dict: 分页结果
        """
        query = Alert.query

        if filters:
            if filters.get('level'):
                query = query.filter(Alert.level == filters['level'])
            if filters.get('status'):
                query = query.filter(Alert.status == filters['status'])
            if filters.get('rule_id'):
                query = query.filter(Alert.rule_id == filters['rule_id'])
            if filters.get('start_time'):
                query = query.filter(Alert.created_at >= filters['start_time'])
            if filters.get('end_time'):
                query = query.filter(Alert.created_at <= filters['end_time'])

        query = query.order_by(Alert.created_at.desc())

        pagination = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            'items': [alert.to_dict() for alert in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page
        }

    def get_alert_stats(self):
        """
        获取告警统计

        Returns:
            dict: 统计结果
        """
        from sqlalchemy import func

        total = Alert.query.count()
        pending = Alert.query.filter_by(status='pending').count()
        processing = Alert.query.filter_by(status='processing').count()
        resolved = Alert.query.filter_by(status='resolved').count()

        # 按级别统计
        level_stats = db.session.query(
            Alert.level,
            func.count(Alert.id)
        ).group_by(Alert.level).all()

        level_counts = {level: count for level, count in level_stats}

        # 今日告警数
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        today_count = Alert.query.filter(Alert.created_at >= today).count()

        return {
            'total': total,
            'pending': pending,
            'processing': processing,
            'resolved': resolved,
            'level_counts': level_counts,
            'today_count': today_count
        }

    def handle_alert(self, alert_id, handler_id, status, note=None):
        """
        处置告警

        Args:
            alert_id: 告警ID
            handler_id: 处置人ID
            status: 新状态
            note: 处置意见

        Returns:
            bool: 是否成功
        """
        try:
            alert = Alert.query.get(alert_id)
            if not alert:
                return False

            alert.status = status
            alert.handler_id = handler_id
            alert.handler_note = note
            alert.handled_at = datetime.now()

            db.session.commit()
            return True

        except Exception as e:
            db.session.rollback()
            print(f"处置告警失败: {e}")
            return False

    def get_recent_alerts(self, limit=5):
        """
        获取最近的告警

        Args:
            limit: 数量限制

        Returns:
            list: 告警列表
        """
        alerts = Alert.query.order_by(Alert.created_at.desc()).limit(limit).all()
        return [alert.to_dict() for alert in alerts]

    def _send_notifications(self, alert, rule):
        """
        发送通知

        Args:
            alert: 告警对象
            rule: 规则对象
        """
        if not rule.notify_methods:
            return

        notify_methods = rule.notify_methods

        # 页面通知（通过WebSocket或轮询实现）
        if notify_methods.get('page'):
            self._send_page_notification(alert)

        # 声音通知
        if notify_methods.get('sound'):
            self._send_sound_notification(alert)

        # 邮件通知
        if notify_methods.get('email'):
            self._send_email_notification(alert, notify_methods.get('email_recipients', []))

    def _send_page_notification(self, alert):
        """发送页面通知"""
        # 实际应用中可以使用WebSocket推送
        print(f"[页面通知] 告警: {alert.content}")

    def _send_sound_notification(self, alert):
        """发送声音通知"""
        print(f"[声音通知] 告警级别: {alert.level}")

    def _send_email_notification(self, alert, recipients):
        """
        发送邮件通知

        Args:
            alert: 告警对象
            recipients: 收件人列表
        """
        # 实际应用中需要配置SMTP服务器
        print(f"[邮件通知] 发送到: {recipients}")
