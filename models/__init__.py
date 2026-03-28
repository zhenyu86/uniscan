# -*- coding: utf-8 -*-
"""模型包初始化"""

from models.user import db, User, OperationLog
from models.device import DeviceGroup, Device, UploadRecord
from models.scene import Scene, SceneTemplate
from models.rule import AlertRule
from models.alert import Alert
from models.task import DetectionTask, DetectionResult
from models.config import TrafficStats, DashboardConfig, SystemConfig, ModelVersion

__all__ = [
    'db',
    'User', 'OperationLog',
    'DeviceGroup', 'Device', 'UploadRecord',
    'Scene', 'SceneTemplate',
    'AlertRule', 'Alert',
    'DetectionTask', 'DetectionResult',
    'TrafficStats', 'DashboardConfig', 'SystemConfig', 'ModelVersion'
]
