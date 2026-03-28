# -*- coding: utf-8 -*-
"""设备模型"""

from datetime import datetime
from models.user import db


class DeviceGroup(db.Model):
    """设备分组表"""
    __tablename__ = 'device_groups'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('device_groups.id'), nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    # 关系
    devices = db.relationship('Device', backref='group', lazy='dynamic')
    children = db.relationship('DeviceGroup', backref=db.backref('parent', remote_side=[id]))

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'parent_id': self.parent_id,
            'description': self.description,
            'device_count': self.devices.count(),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class Device(db.Model):
    """设备表"""
    __tablename__ = 'devices'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    device_type = db.Column(db.Enum('camera', 'drone', 'upload'),
                           nullable=False, default='camera')
    protocol = db.Column(db.String(20), nullable=True)
    address = db.Column(db.String(500), nullable=True)
    group_id = db.Column(db.Integer, db.ForeignKey('device_groups.id'), nullable=True, index=True)
    location = db.Column(db.String(200), nullable=True)
    latitude = db.Column(db.Numeric(10, 8), nullable=True)
    longitude = db.Column(db.Numeric(11, 8), nullable=True)
    status = db.Column(db.SmallInteger, nullable=False, default=0)
    config = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now,
                           onupdate=datetime.now)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'device_type': self.device_type,
            'protocol': self.protocol,
            'address': self.address,
            'group_id': self.group_id,
            'group_name': self.group.name if self.group else None,
            'location': self.location,
            'latitude': float(self.latitude) if self.latitude else None,
            'longitude': float(self.longitude) if self.longitude else None,
            'status': self.status,
            'config': self.config,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'updated_at': self.updated_at.strftime('%Y-%m-%d %H:%M:%S')
        }


class UploadRecord(db.Model):
    """上传记录表"""
    __tablename__ = 'upload_records'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    file_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_type = db.Column(db.Enum('image', 'video'), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    status = db.Column(db.Enum('pending', 'processing', 'completed', 'failed'),
                       nullable=False, default='pending')
    result_path = db.Column(db.String(500), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, index=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'file_name': self.file_name,
            'file_path': self.file_path,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'status': self.status,
            'result_path': self.result_path,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'completed_at': self.completed_at.strftime('%Y-%m-%d %H:%M:%S') if self.completed_at else None
        }
