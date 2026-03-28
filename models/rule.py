# -*- coding: utf-8 -*-
"""告警规则模型"""

from datetime import datetime
from models.user import db


class AlertRule(db.Model):
    """告警规则表"""
    __tablename__ = 'alert_rules'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    scene_id = db.Column(db.Integer, db.ForeignKey('scenes.id'), nullable=True, index=True)
    rule_type = db.Column(db.Enum('count', 'exists', 'area', 'combination', 'trend'),
                          nullable=False, default='count')
    conditions = db.Column(db.JSON, nullable=True)
    level = db.Column(db.Enum('info', 'warning', 'error', 'critical'),
                      nullable=False, default='warning')
    notify_methods = db.Column(db.JSON, nullable=True)
    is_enabled = db.Column(db.SmallInteger, nullable=False, default=1)
    trigger_count = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now,
                           onupdate=datetime.now)

    # 关系
    alerts = db.relationship('Alert', backref='rule', lazy='dynamic')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'scene_id': self.scene_id,
            'scene_name': self.scene.name if self.scene else None,
            'rule_type': self.rule_type,
            'conditions': self.conditions,
            'level': self.level,
            'notify_methods': self.notify_methods,
            'is_enabled': self.is_enabled,
            'trigger_count': self.trigger_count,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }
