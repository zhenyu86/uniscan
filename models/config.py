# -*- coding: utf-8 -*-
"""系统配置模型"""

from datetime import datetime
from models.user import db


class TrafficStats(db.Model):
    """流量统计表"""
    __tablename__ = 'traffic_stats'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=True, index=True)
    scene_id = db.Column(db.Integer, db.ForeignKey('scenes.id'), nullable=True)
    stat_date = db.Column(db.Date, nullable=False, index=True)
    stat_hour = db.Column(db.SmallInteger, nullable=False)
    total_detections = db.Column(db.Integer, nullable=False, default=0)
    class_stats = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'device_id': self.device_id,
            'scene_id': self.scene_id,
            'stat_date': self.stat_date.strftime('%Y-%m-%d'),
            'stat_hour': self.stat_hour,
            'total_detections': self.total_detections,
            'class_stats': self.class_stats,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class DashboardConfig(db.Model):
    """看板配置表"""
    __tablename__ = 'dashboard_configs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    scene_id = db.Column(db.Integer, db.ForeignKey('scenes.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    layout = db.Column(db.JSON, nullable=True)
    widgets = db.Column(db.JSON, nullable=True)
    is_default = db.Column(db.SmallInteger, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now,
                           onupdate=datetime.now)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'scene_id': self.scene_id,
            'user_id': self.user_id,
            'layout': self.layout,
            'widgets': self.widgets,
            'is_default': self.is_default,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class SystemConfig(db.Model):
    """系统配置表"""
    __tablename__ = 'system_configs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    config_key = db.Column(db.String(100), unique=True, nullable=False)
    config_value = db.Column(db.Text, nullable=True)
    config_type = db.Column(db.String(20), nullable=False, default='string')
    description = db.Column(db.String(255), nullable=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now,
                           onupdate=datetime.now)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'config_key': self.config_key,
            'config_value': self.config_value,
            'config_type': self.config_type,
            'description': self.description,
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }

    def get_value(self):
        """获取配置值（自动类型转换）"""
        if self.config_type == 'int':
            return int(self.config_value)
        elif self.config_type == 'float':
            return float(self.config_value)
        elif self.config_type == 'bool':
            return self.config_value.lower() in ('true', '1', 'yes')
        elif self.config_type == 'json':
            import json
            return json.loads(self.config_value)
        return self.config_value


class ModelVersion(db.Model):
    """模型版本表"""
    __tablename__ = 'model_versions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    version = db.Column(db.String(50), nullable=False)
    model_path = db.Column(db.String(255), nullable=False)
    class_names = db.Column(db.JSON, nullable=True)
    input_size = db.Column(db.String(20), nullable=True)
    is_active = db.Column(db.SmallInteger, nullable=False, default=0)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'version': self.version,
            'model_path': self.model_path,
            'class_names': self.class_names,
            'input_size': self.input_size,
            'is_active': self.is_active,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
