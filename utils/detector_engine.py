# -*- coding: utf-8 -*-
"""
检测引擎模块 - 兼容性包装器

本模块是对新模块化检测器架构的兼容性包装器。
原有的代码可以继续使用此模块，无需修改。

新的检测器架构位于 detectors/ 目录：
- detectors/base_detector.py: 检测器抽象基类
- detectors/onnx_detector.py: ONNX检测器实现
- detectors/factory.py: 检测器工厂和引擎

如何替换检测模型:
----------------
1. 在 detector_config.py 中修改配置参数
2. 或者使用新的检测器接口：
   from detectors import DetectorFactory
   detector = DetectorFactory.create_detector(
       model_type='onnx',
       model_path='your_model.onnx'
   )

本模块保持向后兼容，但建议新代码使用 detectors 模块。
"""

import os
from typing import List, Dict, Optional, Tuple, Callable

# 从新的检测器模块导入
from detectors import (
    BaseDetector,
    DetectionResult,
    ONNXDetector,
    DetectorFactory,
    DetectorEngine
)

# 从配置文件导入默认参数
from detector_config import (
    MODEL_TYPE,
    MODEL_PATH,
    CLASS_LABELS,
    CONFIDENCE_THRESHOLD,
    IOU_THRESHOLD,
    DEVICE,
    DEFAULT_FRAME_STEP
)

# 向后兼容的常量别名
DEFAULT_CLASS_LABELS = CLASS_LABELS
DEFAULT_CONFIDENCE = CONFIDENCE_THRESHOLD
DEFAULT_IOU = IOU_THRESHOLD
PREFERRED_DEVICE = DEVICE.upper() if DEVICE else 'CPU'


# 向后兼容：直接导出ONNXDetector
# 原有代码可以直接使用 from utils.detector_engine import ONNXDetector
ONNXDetector = ONNXDetector


def create_detector(
    model_path: str,
    class_labels: Optional[List[str]] = None,
    confidence: float = DEFAULT_CONFIDENCE,
    iou: float = DEFAULT_IOU,
    model_type: str = 'onnx'
) -> DetectorEngine:
    """
    创建检测引擎实例 (向后兼容函数)
    
    Args:
        model_path: 模型路径
        class_labels: 类别标签
        confidence: 置信度阈值
        iou: IOU阈值
        model_type: 检测器类型 (新增参数)
    
    Returns:
        DetectorEngine实例
    """
    engine = DetectorEngine(
        model_type=model_type,
        model_path=model_path,
        class_labels=class_labels,
        confidence=confidence,
        iou=iou
    )
    return engine


def quick_detect(
    image_path: str,
    model_path: str = None,
    class_labels: Optional[List[str]] = None,
    confidence: float = DEFAULT_CONFIDENCE,
    iou: float = DEFAULT_IOU,
    output_path: Optional[str] = None
) -> Dict:
    """
    快速检测单张图片 (向后兼容函数)
    
    Args:
        image_path: 图片路径
        model_path: 模型路径
        class_labels: 类别标签
        confidence: 置信度阈值
        iou: IOU阈值
        output_path: 输出路径（可选）
    
    Returns:
        检测结果
    """
    import cv2
    
    if model_path is None:
        model_path = MODEL_PATH
    
    detector = create_detector(model_path, class_labels, confidence, iou)
    result = detector.detect_image(image_path, {'confidence': confidence, 'iou_threshold': iou})
    
    if result['success'] and output_path:
        detector.save_result_image(result['result_image'], output_path)
    
    return result


# 导出所有公共接口
__all__ = [
    # 新的模块化接口
    'BaseDetector',
    'DetectionResult',
    'ONNXDetector',
    'DetectorFactory',
    'DetectorEngine',
    
    # 向后兼容函数
    'create_detector',
    'quick_detect',
    
    # 向后兼容常量
    'DEFAULT_CLASS_LABELS',
    'DEFAULT_CONFIDENCE',
    'DEFAULT_IOU',
    'PREFERRED_DEVICE',
]
