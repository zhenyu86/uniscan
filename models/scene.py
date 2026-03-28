# -*- coding: utf-8 -*-
"""场景模型"""

from datetime import datetime
from models.user import db


class Scene(db.Model):
    """场景表"""
    __tablename__ = 'scenes'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    icon = db.Column(db.String(100), nullable=True)
    theme_color = db.Column(db.String(20), nullable=True, default='#2D5BFF')
    class_mapping = db.Column(db.JSON, nullable=True)
    focus_classes = db.Column(db.JSON, nullable=True)
    config = db.Column(db.JSON, nullable=True)
    is_default = db.Column(db.SmallInteger, nullable=False, default=0)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now,
                           onupdate=datetime.now)

    # 关系
    alert_rules = db.relationship('AlertRule', backref='scene', lazy='dynamic')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'icon': self.icon,
            'theme_color': self.theme_color,
            'class_mapping': self.class_mapping,
            'focus_classes': self.focus_classes,
            'config': self.config,
            'is_default': self.is_default,
            'created_by': self.created_by,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class SceneTemplate(db.Model):
    """场景模板表"""
    __tablename__ = 'scene_templates'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=True)
    description = db.Column(db.Text, nullable=True)
    config = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'category': self.category,
            'description': self.description,
            'config': self.config,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
