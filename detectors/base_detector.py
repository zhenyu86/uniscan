# -*- coding: utf-8 -*-
"""
检测器抽象基类 - 定义统一的检测接口

本模块定义了目标检测器的标准接口，所有检测模型都应该继承此基类。

数据格式说明:
--------------
输入图像:
    - 类型: numpy.ndarray
    - 形状: (H, W, C) 其中 H=高度, W=宽度, C=通道数(通常为3)
    - 格式: BGR (Blue-Green-Red)
    - 数据类型: uint8 (0-255)

输出检测结果:
    - 类型: List[Dict]
    - 每个检测框包含:
        - class_id: int - 类别ID
        - class_name: str - 类别名称
        - confidence: float - 置信度 (0.0-1.0)
        - bbox: dict - 边界框坐标
            - x: int - 左上角x坐标
            - y: int - 左上角y坐标
            - w: int - 宽度
            - h: int - 高度

模型输入张量:
    - 类型: numpy.ndarray
    - 形状: (N, C, H, W) 其中 N=批次大小, C=通道数, H=高度, W=宽度
    - 数据类型: float32
    - 归一化: [0, 1]

如何替换检测模型:
----------------
1. 创建新的检测器类，继承 BaseDetector
2. 实现所有抽象方法:
   - preprocess(): 图像预处理
   - postprocess(): 模型输出后处理
   - detect(): 执行检测
3. 在 factory.py 中注册新的检测器类型
4. 修改 config.py 中的 MODEL_TYPE 配置
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass
import numpy as np


@dataclass
class DetectionResult:
    """
    检测结果数据类
    
    Attributes:
        class_id: 类别ID (从0开始)
        class_name: 类别名称 (如 'person', 'car')
        confidence: 检测置信度 (0.0-1.0)
        bbox: 边界框坐标字典
            - x: 左上角x坐标
            - y: 左上角y坐标  
            - w: 边界框宽度
            - h: 边界框高度
    """
    class_id: int
    class_name: str
    confidence: float
    bbox: Dict[str, int]
    
    def to_dict(self) -> Dict:
        """转换为字典格式"""
        return {
            'class_id': self.class_id,
            'class_name': self.class_name,
            'confidence': round(self.confidence, 4),
            'bbox': self.bbox
        }


class BaseDetector(ABC):
    """
    检测器抽象基类
    
    所有检测器实现都应该继承此类，并实现以下抽象方法:
    - preprocess(): 图像预处理
    - postprocess(): 模型输出后处理
    - detect(): 执行检测
    - detect_and_draw(): 检测并绘制结果
    """
    
    def __init__(
        self,
        model_path: str,
        class_labels: Optional[List[str]] = None,
        confidence_threshold: float = 0.5,
        iou_threshold: float = 0.45,
        **kwargs
    ):
        """
        初始化检测器
        
        Args:
            model_path: 模型文件路径
            class_labels: 类别标签列表，为None时使用模型默认值
            confidence_threshold: 置信度阈值 (默认: 0.5)
            iou_threshold: IOU阈值，用于NMS非极大值抑制 (默认: 0.45)
            **kwargs: 其他模型特定参数
        """
        self.model_path = model_path
        self.class_labels = class_labels or []
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold
        
        # 模型输入尺寸 (应在子类中设置)
        self.input_width: int = 640
        self.input_height: int = 640
        
        # 原始图像尺寸 (检测时动态设置)
        self.original_width: int = 0
        self.original_height: int = 0
        
        # 颜色映射 (用于可视化)
        self._color_map: Optional[np.ndarray] = None
    
    @property
    def color_map(self) -> np.ndarray:
        """获取颜色映射"""
        if self._color_map is None:
            self._color_map = np.random.uniform(0, 255, size=(len(self.class_labels), 3))
        return self._color_map
    
    @abstractmethod
    def load_model(self) -> None:
        """
        加载模型
        
        子类必须实现此方法来加载具体的模型文件。
        对于ONNX模型，使用onnxruntime加载；
        对于PyTorch模型，使用torch.load()加载；
        对于TensorFlow模型，使用tf.saved_model加载。
        """
        pass
    
    @abstractmethod
    def preprocess(self, image: np.ndarray) -> Any:
        """
        图像预处理
        
        将原始图像转换为模型输入格式。
        
        Args:
            image: 输入图像
                - 类型: numpy.ndarray
                - 形状: (H, W, C) 
                - 格式: BGR
                - 数据类型: uint8 (0-255)
        
        Returns:
            预处理后的输入张量
                - 类型: numpy.ndarray
                - 形状: (1, C, H, W) - 批次大小为1
                - 数据类型: float32
                - 值范围: [0, 1]
        """
        pass
    
    @abstractmethod
    def postprocess(
        self,
        raw_output: Any,
        conf_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None
    ) -> List[DetectionResult]:
        """
        模型输出后处理
        
        将模型原始输出转换为检测结果列表。
        
        Args:
            raw_output: 模型原始输出
                - 对于YOLOv8: List[np.ndarray]，包含一个形状为 (1, 4+num_classes, 8400) 的数组
                - 其中 8400 = 80*80 + 40*40 + 20*20 (三个检测头)
                - 前4个值是 (cx, cy, w, h)，后面是类别概率
            conf_threshold: 置信度阈值 (可选，覆盖默认值)
            iou_threshold: IOU阈值 (可选，覆盖默认值)
        
        Returns:
            检测结果列表，每个元素包含:
                - class_id: int - 类别ID
                - class_name: str - 类别名称
                - confidence: float - 置信度
                - bbox: dict - 边界框 {x, y, w, h}
        """
        pass
    
    @abstractmethod
    def detect(
        self,
        image: np.ndarray,
        conf_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None
    ) -> List[DetectionResult]:
        """
        执行目标检测
        
        Args:
            image: 输入图像
                - 类型: numpy.ndarray
                - 形状: (H, W, C)
                - 格式: BGR
            conf_threshold: 置信度阈值 (可选)
            iou_threshold: IOU阈值 (可选)
        
        Returns:
            检测结果列表
        """
        pass
    
    @abstractmethod
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
            image: 输入图像 (BGR格式)
            conf_threshold: 置信度阈值 (可选)
            iou_threshold: IOU阈值 (可选)
            show_label: 是否显示标签
            line_thickness: 边界框线条粗细
        
        Returns:
            (绘制后的图像, 检测结果列表)
        """
        pass
    
    def draw_detections(
        self,
        image: np.ndarray,
        detections: List[DetectionResult],
        show_label: bool = True,
        line_thickness: int = 2
    ) -> np.ndarray:
        """
        在图像上绘制检测结果 (通用实现)
        
        Args:
            image: 图像 (会被修改)
            detections: 检测结果列表
            show_label: 是否显示标签
            line_thickness: 线条粗细
        
        Returns:
            绘制后的图像
        """
        import cv2
        
        for det in detections:
            bbox = det.bbox
            x, y, w, h = bbox['x'], bbox['y'], bbox['w'], bbox['h']
            class_id = det.class_id
            confidence = det.confidence
            
            # 获取颜色
            color = tuple(map(int, self.color_map[class_id % len(self.color_map)]))
            
            # 绘制边界框
            cv2.rectangle(image, (x, y), (x + w, y + h), color, line_thickness)
            
            if show_label:
                # 标签文本
                label = f"{det.class_name} {confidence:.2f}"
                
                # 计算文本尺寸
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.5
                (text_w, text_h), baseline = cv2.getTextSize(label, font, font_scale, 1)
                
                # 标签位置
                label_y = max(y - 10, text_h + 10)
                
                # 绘制标签背景
                cv2.rectangle(
                    image,
                    (x, label_y - text_h - 5),
                    (x + text_w, label_y + 5),
                    color,
                    cv2.FILLED
                )
                
                # 绘制标签文本
                cv2.putText(
                    image, label, (x, label_y),
                    font, font_scale, (255, 255, 255), 1, cv2.LINE_AA
                )
        
        return image
    
    def set_params(
        self,
        confidence_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None
    ) -> None:
        """设置检测参数"""
        if confidence_threshold is not None:
            self.confidence_threshold = confidence_threshold
        if iou_threshold is not None:
            self.iou_threshold = iou_threshold
    
    def get_class_names(self) -> List[str]:
        """获取类别名称列表"""
        return self.class_labels
    
    def get_model_info(self) -> Dict:
        """获取模型信息"""
        return {
            'model_path': self.model_path,
            'model_type': self.__class__.__name__,
            'input_size': f'{self.input_width}x{self.input_height}',
            'class_count': len(self.class_labels),
            'class_names': self.class_labels,
            'confidence_threshold': self.confidence_threshold,
            'iou_threshold': self.iou_threshold
        }
