# -*- coding: utf-8 -*-
"""
ONNX目标检测器实现

本模块实现了基于ONNX Runtime的目标检测器，支持YOLO系列模型。

模型要求:
---------
1. 输入格式:
   - 形状: (1, 3, H, W)
   - 数据类型: float32
   - 值范围: [0, 1] (归一化后的RGB图像)

2. 输出格式 (YOLO v5/v8):
   - 形状: (1, 4+num_classes, num_predictions)
   - 其中 num_predictions = 80*80 + 40*40 + 20*20 = 8400 (对于640x640输入)
   - 前4个值: (center_x, center_y, width, height)
   - 后续值: 各类别概率

配置说明:
---------
1. 修改 DEFAULT_CLASS_LABELS 来设置默认类别名称
2. 修改 DEFAULT_CONFIDENCE 和 DEFAULT_IOU 来设置默认阈值
3. 如需修改检测逻辑，请参考 postprocess() 方法

替换为其他ONNX模型:
-------------------
1. 准备ONNX模型文件
2. 确保模型输入输出格式符合上述要求
3. 如输出格式不同，需修改 postprocess() 方法
4. 更新 class_labels 列表
"""

import os
import cv2
import numpy as np
import onnxruntime as ort
import time
from typing import List, Dict, Optional, Tuple, Callable

from detectors.base_detector import BaseDetector, DetectionResult


# ==================== 默认配置 ====================
# 【修改位置1】默认类别标签 - COCO 80类
DEFAULT_CLASS_LABELS = [
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

# 【修改位置2】默认置信度阈值
DEFAULT_CONFIDENCE = 0.5

# 【修改位置3】默认IOU阈值（NMS）
DEFAULT_IOU = 0.5

# 【修改位置4】优先使用的推理设备 ('CUDA' 或 'CPU')
PREFERRED_DEVICE = 'CUDA'
# ================================================


class ONNXDetector(BaseDetector):
    """
    ONNX目标检测器
    
    基于ONNX Runtime的高性能目标检测引擎。
    支持YOLOv5、YOLOv8等系列模型。
    
    使用示例:
        detector = ONNXDetector(
            model_path='weights/best.onnx',
            class_labels=['person', 'car', ...]
        )
        
        # 检测单张图像
        image = cv2.imread('test.jpg')
        detections = detector.detect(image)
        
        # 检测并绘制结果
        result_image, detections = detector.detect_and_draw(image)
    """
    
    def __init__(
        self,
        model_path: str,
        class_labels: Optional[List[str]] = None,
        confidence_threshold: float = DEFAULT_CONFIDENCE,
        iou_threshold: float = DEFAULT_IOU
    ):
        """
        初始化ONNX检测器
        
        Args:
            model_path: ONNX模型文件路径
            class_labels: 类别标签列表，为None时使用DEFAULT_CLASS_LABELS
            confidence_threshold: 置信度阈值 (默认: 0.5)
            iou_threshold: IOU阈值，用于NMS (默认: 0.5)
        """
        super().__init__(
            model_path=model_path,
            class_labels=class_labels or DEFAULT_CLASS_LABELS,
            confidence_threshold=confidence_threshold,
            iou_threshold=iou_threshold
        )
        
        # ONNX Runtime会话
        self.session: Optional[ort.InferenceSession] = None
        self.input_name: Optional[str] = None
        self.output_names: Optional[List[str]] = None
        
        # 加载模型
        self.load_model()
    
    def load_model(self) -> None:
        """加载ONNX模型"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"模型文件不存在: {self.model_path}")
        
        # 获取可用的推理设备
        available_providers = ort.get_available_providers()
        print(f"可用的ONNX Runtime设备: {available_providers}")
        
        # 优先使用GPU (CUDA)
        if 'CUDAExecutionProvider' in available_providers and PREFERRED_DEVICE == 'CUDA':
            providers = [
                ('CUDAExecutionProvider', {
                    'device_id': 0,
                    'arena_extend_strategy': 'kNextPowerOfTwo',
                    'gpu_mem_limit': 2 * 1024 * 1024 * 1024,  # 2GB
                    'cudnn_conv_algo_search': 'EXHAUSTIVE',
                    'do_copy_in_default_stream': True,
                }),
                'CPUExecutionProvider'
            ]
            print("✅ 使用GPU (CUDA) 进行推理")
        else:
            providers = ['CPUExecutionProvider']
            print("⚠️ CUDA不可用，使用CPU进行推理")
            print("提示: 安装GPU版本: pip install onnxruntime-gpu")
        
        # 创建推理会话
        try:
            self.session = ort.InferenceSession(self.model_path, providers=providers)
            used_providers = self.session.get_providers()
            print(f"当前使用的设备: {used_providers}")
        except Exception as e:
            print(f"GPU初始化失败，回退到CPU: {e}")
            self.session = ort.InferenceSession(self.model_path, providers=['CPUExecutionProvider'])
        
        # 获取模型输入输出信息
        self.input_name = self.session.get_inputs()[0].name
        self.output_names = [output.name for output in self.session.get_outputs()]
        
        # 获取模型输入尺寸
        input_shape = self.session.get_inputs()[0].shape
        # 形状通常是 (1, 3, H, W) 或 (1, 3, -1, -1)
        if len(input_shape) == 4:
            self.input_height = input_shape[2] if isinstance(input_shape[2], int) else 640
            self.input_width = input_shape[3] if isinstance(input_shape[3], int) else 640
        
        print(f"模型输入尺寸: {self.input_width}x{self.input_height}")
        
        # 预热模型
        self._warmup()
    
    def _warmup(self) -> None:
        """预热模型，加速首次推理"""
        try:
            dummy_input = np.zeros(
                (1, 3, self.input_height, self.input_width),
                dtype=np.float32
            )
            self.session.run(None, {self.input_name: dummy_input})
            print(f"模型预热完成 - 输入尺寸: {self.input_width}x{self.input_height}")
        except Exception as e:
            print(f"模型预热失败: {e}")
    
    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        图像预处理
        
        将BGR图像转换为模型输入格式。
        
        处理流程:
        1. 记录原始图像尺寸
        2. BGR → RGB 转换
        3. 调整尺寸到模型输入大小
        4. 归一化到 [0, 1]
        5. HWC → CHW (通道优先)
        6. 添加批次维度
        
        Args:
            image: 输入图像
                - 类型: numpy.ndarray
                - 形状: (H, W, 3)
                - 格式: BGR
                - 数据类型: uint8
        
        Returns:
            模型输入张量
                - 类型: numpy.ndarray
                - 形状: (1, 3, H, W)
                - 数据类型: float32
                - 值范围: [0, 1]
        """
        # 记录原始尺寸 (用于后处理坐标还原)
        self.original_height, self.original_width = image.shape[:2]
        
        # BGR转RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 调整尺寸
        resized = cv2.resize(rgb_image, (self.input_width, self.input_height))
        
        # 归一化 [0, 1]
        normalized = resized.astype(np.float32) / 255.0
        
        # HWC -> CHW (通道优先)
        transposed = np.transpose(normalized, (2, 0, 1))
        
        # 添加batch维度: (C, H, W) -> (1, C, H, W)
        batch_input = np.expand_dims(transposed, axis=0)
        
        return batch_input
    
    def postprocess(
        self,
        raw_output: List[np.ndarray],
        conf_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None
    ) -> List[DetectionResult]:
        """
        模型输出后处理
        
        将YOLO模型输出转换为检测结果列表。
        
        YOLO输出格式:
        - 形状: (1, 4+num_classes, 8400)
        - 前4个值: (center_x, center_y, width, height) - 归一化坐标
        - 后续值: 各类别概率
        
        Args:
            raw_output: 模型原始输出
                - 类型: List[np.ndarray]
                - 形状: [(1, 4+num_classes, 8400)]
            conf_threshold: 置信度阈值 (可选，覆盖默认值)
            iou_threshold: IOU阈值 (可选，覆盖默认值)
        
        Returns:
            检测结果列表，每个元素包含:
                - class_id: int - 类别ID (0-indexed)
                - class_name: str - 类别名称
                - confidence: float - 置信度 (0.0-1.0)
                - bbox: dict - 边界框 {x, y, w, h} - 像素坐标
        """
        conf_threshold = conf_threshold or self.confidence_threshold
        iou_threshold = iou_threshold or self.iou_threshold
        
        # 处理输出数据 (YOLO格式)
        # raw_output[0] 形状: (1, 4+num_classes, 8400)
        output_data = np.squeeze(raw_output[0]).T  # 转置: (8400, 4+num_classes)
        
        # 计算坐标缩放比例 (从模型输入尺寸到原始图像尺寸)
        scale_x = self.original_width / self.input_width
        scale_y = self.original_height / self.input_height
        
        # 提取类别概率 (跳过前4个坐标值)
        class_probs = output_data[:, 4:]
        max_scores = np.amax(class_probs, axis=1)  # 每个预测框的最大类别概率
        class_ids = np.argmax(class_probs, axis=1)  # 最大概率对应的类别ID
        
        # 置信度过滤
        valid_indices = np.where(max_scores >= conf_threshold)[0]
        
        if len(valid_indices) == 0:
            return []
        
        filtered_output = output_data[valid_indices]
        filtered_scores = max_scores[valid_indices]
        filtered_class_ids = class_ids[valid_indices]
        
        # 提取边界框坐标 (center_x, center_y, width, height)
        center_x = filtered_output[:, 0]
        center_y = filtered_output[:, 1]
        box_width = filtered_output[:, 2]
        box_height = filtered_output[:, 3]
        
        # 转换为 (x, y, w, h) 格式并缩放到原始图像尺寸
        x = (center_x - box_width / 2) * scale_x
        y = (center_y - box_height / 2) * scale_y
        w = box_width * scale_x
        h = box_height * scale_y
        
        # 转换为整数坐标
        boxes = np.column_stack((x, y, w, h)).astype(int)
        
        # NMS非极大值抑制
        nms_indices = cv2.dnn.NMSBoxes(
            boxes.tolist(),
            filtered_scores.tolist(),
            conf_threshold,
            iou_threshold
        )
        
        # 构建检测结果
        detections = []
        if len(nms_indices) > 0:
            for idx in nms_indices:
                if isinstance(idx, (list, np.ndarray)):
                    idx = idx[0]
                
                box = boxes[idx]
                class_id = int(filtered_class_ids[idx])
                
                detections.append(DetectionResult(
                    class_id=class_id,
                    class_name=self.class_labels[class_id] if class_id < len(self.class_labels) else f'class_{class_id}',
                    confidence=float(filtered_scores[idx]),
                    bbox={
                        'x': int(box[0]),
                        'y': int(box[1]),
                        'w': int(box[2]),
                        'h': int(box[3])
                    }
                ))
        
        return detections
    
    def detect(
        self,
        image: np.ndarray,
        conf_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None
    ) -> List[DetectionResult]:
        """
        对单张图像进行目标检测
        
        Args:
            image: BGR格式的图像
                - 类型: numpy.ndarray
                - 形状: (H, W, 3)
            conf_threshold: 置信度阈值 (可选)
            iou_threshold: IOU阈值 (可选)
        
        Returns:
            检测结果列表
        """
        # 预处理
        input_tensor = self.preprocess(image)
        
        # 推理
        raw_output = self.session.run(None, {self.input_name: input_tensor})
        
        # 后处理
        detections = self.postprocess(raw_output, conf_threshold, iou_threshold)
        
        return detections
    
    def detect_and_draw(
        self,
        image: np.ndarray,
        conf_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None,
        show_label: bool = True,
        line_thickness: int = 2
    ) -> Tuple[np.ndarray, List[DetectionResult]]:
        """
        检测并在图像上绘制结果
        
        Args:
            image: BGR格式的图像
            conf_threshold: 置信度阈值 (可选)
            iou_threshold: IOU阈值 (可选)
            show_label: 是否显示标签
            line_thickness: 边界框线条粗细
        
        Returns:
            (绘制后的图像, 检测结果列表)
        """
        detections = self.detect(image, conf_threshold, iou_threshold)
        result_image = self.draw_detections(image.copy(), detections, show_label, line_thickness)
        return result_image, detections
