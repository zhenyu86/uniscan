# -*- coding: utf-8 -*-
"""检测任务模型"""

from datetime import datetime
from models.user import db


class DetectionTask(db.Model):
    """检测任务表"""
    __tablename__ = 'detection_tasks'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_type = db.Column(db.Enum('image', 'video', 'stream', 'batch'),
                          nullable=False, index=True)
    source_type = db.Column(db.Enum('upload', 'device', 'url'), nullable=False)
    source_id = db.Column(db.Integer, nullable=True)
    scene_id = db.Column(db.Integer, db.ForeignKey('scenes.id'), nullable=True)
    params = db.Column(db.JSON, nullable=True)
    status = db.Column(db.Enum('queued', 'processing', 'completed', 'failed', 'cancelled'),
                       nullable=False, default='queued', index=True)
    progress = db.Column(db.Integer, nullable=False, default=0)
    result_summary = db.Column(db.JSON, nullable=True)
    result_path = db.Column(db.String(500), nullable=True)
    error_msg = db.Column(db.Text, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now, index=True)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    # 关系
    results = db.relationship('DetectionResult', backref='task', lazy='dynamic',
                              cascade='all, delete-orphan')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'task_type': self.task_type,
            'source_type': self.source_type,
            'source_id': self.source_id,
            'scene_id': self.scene_id,
            'params': self.params,
            'status': self.status,
            'progress': self.progress,
            'result_summary': self.result_summary,
            'result_path': self.result_path,
            'error_msg': self.error_msg,
            'created_by': self.created_by,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'started_at': self.started_at.strftime('%Y-%m-%d %H:%M:%S') if self.started_at else None,
            'completed_at': self.completed_at.strftime('%Y-%m-%d %H:%M:%S') if self.completed_at else None
        }


class DetectionResult(db.Model):
    """检测结果明细表"""
    __tablename__ = 'detection_results'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    task_id = db.Column(db.Integer, db.ForeignKey('detection_tasks.id'),
                        nullable=False, index=True)
    frame_index = db.Column(db.Integer, nullable=True, default=0)
    class_id = db.Column(db.Integer, nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    confidence = db.Column(db.Numeric(5, 4), nullable=False)
    bbox_x = db.Column(db.Integer, nullable=False)
    bbox_y = db.Column(db.Integer, nullable=False)
    bbox_w = db.Column(db.Integer, nullable=False)
    bbox_h = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'frame_index': self.frame_index,
            'class_id': self.class_id,
            'class_name': self.class_name,
            'confidence': float(self.confidence),
            'bbox': {
                'x': self.bbox_x,
                'y': self.bbox_y,
                'w': self.bbox_w,
                'h': self.bbox_h
            },
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }
