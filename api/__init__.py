# -*- coding: utf-8 -*-
"""API包初始化"""

from api.auth import auth_bp
from api.devices import devices_bp
from api.detect import detect_bp
from api.alerts import alerts_bp
from api.analytics import analytics_bp
from api.scenes import scenes_bp
from api.rules import rules_bp
from api.settings import settings_bp

__all__ = [
    'auth_bp',
    'devices_bp',
    'detect_bp',
    'alerts_bp',
    'analytics_bp',
    'scenes_bp',
    'rules_bp',
    'settings_bp'
]
