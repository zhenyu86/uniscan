# -*- coding: utf-8 -*-
"""
检测器配置文件

本文件包含了目标检测相关的所有配置参数。
修改此文件可以快速切换检测模型和调整检测参数。

配置说明:
---------
1. MODEL_TYPE: 检测器类型 ('onnx', 'pytorch', 'tensorflow')
2. MODEL_PATH: 模型文件路径
3. CLASS_LABELS: 类别标签列表
4. CONFIDENCE_THRESHOLD: 默认置信度阈值
5. IOU_THRESHOLD: 默认IOU阈值 (用于NMS)
6. INPUT_SIZE: 模型输入尺寸
7. DEVICE: 推理设备 ('cuda', 'cpu')

如何替换检测模型:
----------------
1. 准备模型文件并放置在 weights/ 目录
2. 修改 MODEL_TYPE 和 MODEL_PATH
3. 更新 CLASS_LABELS 为新模型的类别
4. 如需修改模型输入尺寸，更新 INPUT_SIZE
5. 重启应用

示例配置:
---------
# 使用YOLOv8 ONNX模型
MODEL_TYPE = 'onnx'
MODEL_PATH = 'weights/yolov8n.onnx'
INPUT_SIZE = (640, 640)

# 使用自定义训练的模型
MODEL_TYPE = 'onnx'
MODEL_PATH = 'weights/custom_model.onnx'
CLASS_LABELS = ['cat', 'dog', 'bird']  # 自定义类别
"""

import os

# 获取项目根目录
basedir = os.path.abspath(os.path.dirname(__file__))


# ==================== 检测器类型配置 ====================
# 支持的类型: 'onnx', 'pytorch', 'tensorflow'
MODEL_TYPE = 'onnx'

# ==================== 模型路径配置 ====================
# 模型文件路径 (相对于项目根目录)
MODEL_PATH = os.path.join(basedir, 'weights', 'best.onnx')

# ==================== 模型输入尺寸 ====================
# 格式: (width, height)
# YOLO系列通常使用 640x640 或 1280x1280
INPUT_SIZE = (640, 640)

# ==================== 检测参数配置 ====================
# 默认置信度阈值 (范围: 0.0-1.0)
# 值越高，检测越严格，误检越少
CONFIDENCE_THRESHOLD = 0.5

# 默认IOU阈值 (用于NMS非极大值抑制)
# 值越高，重叠框越多；值越低，重叠框越少
IOU_THRESHOLD = 0.45

# ==================== 推理设备配置 ====================
# 优先使用的设备: 'cuda' 或 'cpu'
# 如果cuda不可用，会自动回退到cpu
DEVICE = 'cuda'

# ==================== COCO 80类标签 ====================
# 如果使用自定义模型，请修改此列表为您的类别
CLASS_LABELS = [
    'person', 'bicycle', 'car', 'motorcycle', 'airplane', 'bus', 'train', 'truck',
    'boat', 'traffic light', 'fire hydrant', 'stop sign', 'parking meter', 'bench',
    'bird', 'cat', 'dog', 'horse', 'sheep', 'cow', 'elephant', 'bear', 'zebra',
    'giraffe', 'backpack', 'umbrella', 'handbag', 'tie', 'suitcase', 'frisbee',
    'skis', 'snowboard', 'sports ball', 'kite', 'baseball bat', 'baseball glove',
    'skateboard', 'surfboard', 'tennis racket', 'bottle', 'wine glass', 'cup',
    'fork', 'knife', 'spoon', 'bowl', 'banana', 'apple', 'sandwich', 'orange',
    'broccoli', 'carrot', 'hot dog', 'pizza', 'donut', 'cake', 'chair', 'couch',
    'potted plant', 'bed', 'dining table', 'toilet', 'tv', 'laptop', 'mouse',
    'remote', 'keyboard', 'cell phone', 'microwave', 'oven', 'toaster', 'sink',
    'refrigerator', 'book', 'clock', 'vase', 'scissors', 'teddy bear', 'hair drier',
    'toothbrush'
]

# ==================== 视频处理配置 ====================
# 视频抽帧步长 (每N帧检测1帧)
# 值越大，处理速度越快，但可能漏检
# 值越小，检测越完整，但处理时间越长
DEFAULT_FRAME_STEP = 10

# ==================== 批量检测配置 ====================
# 批量检测时的最大并行数
BATCH_SIZE = 1


def get_detector_config() -> dict:
    """
    获取检测器配置字典
    
    Returns:
        dict: 检测器配置
    """
    return {
        'model_type': MODEL_TYPE,
        'model_path': MODEL_PATH,
        'input_size': INPUT_SIZE,
        'confidence': CONFIDENCE_THRESHOLD,
        'iou': IOU_THRESHOLD,
        'device': DEVICE,
        'class_labels': CLASS_LABELS,
        'frame_step': DEFAULT_FRAME_STEP,
        'batch_size': BATCH_SIZE
    }
