# -*- coding: utf-8 -*-
"""
检测器模块 - 提供统一的目标检测接口

本模块提供了可替换的检测器架构：
- BaseDetector: 抽象基类，定义了检测器的标准接口
- ONNXDetector: 基于ONNX Runtime的检测器实现
- DetectorFactory: 检测器工厂，用于创建检测器实例
- DetectorEngine: 检测引擎，提供高层检测接口

使用示例:
    from detectors import DetectorFactory
    
    # 创建检测器
    detector = DetectorFactory.create_detector(
        model_type='onnx',
        model_path='weights/best.onnx'
    )
    
    # 执行检测
    result = detector.detect(image)
"""

from detectors.base_detector import BaseDetector, DetectionResult
from detectors.onnx_detector import ONNXDetector
from detectors.factory import DetectorFactory, DetectorEngine

# 注册ONNX检测器
DetectorFactory.register('onnx')(ONNXDetector)

__all__ = [
    'BaseDetector',
    'DetectionResult',
    'ONNXDetector',
    'DetectorFactory',
    'DetectorEngine'
]
