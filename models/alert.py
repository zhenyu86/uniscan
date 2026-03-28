# -*- coding: utf-8 -*-
"""告警模型"""

from datetime import datetime
from models.user import db


class Alert(db.Model):
    """告警记录表"""
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    rule_id = db.Column(db.Integer, db.ForeignKey('alert_rules.id'), nullable=True, index=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=True)
    task_id = db.Column(db.Integer, db.ForeignKey('detection_tasks.id'), nullable=True)
    level = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=True)
    details = db.Column(db.JSON, nullable=True)
    status = db.Column(db.Enum('pending', 'processing', 'resolved'),
                       nullable=False, default='pending', index=True)
    handler_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    handler_note = db.Column(db.Text, nullable=True)
    handled_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, index=True)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'rule_id': self.rule_id,
            'rule_name': self.rule.name if self.rule else None,
            'device_id': self.device_id,
            'task_id': self.task_id,
            'level': self.level,
            'content': self.content,
            'details': self.details,
            'status': self.status,
            'handler_id': self.handler_id,
            'handler_note': self.handler_note,
            'handled_at': self.handled_at.strftime('%Y-%m-%d %H:%M:%S') if self.handled_at else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
