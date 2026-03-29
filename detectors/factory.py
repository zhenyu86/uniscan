# -*- coding: utf-8 -*-
"""
检测器工厂 - 创建和管理检测器实例

本模块提供了检测器的工厂模式实现，支持:
1. 动态创建不同类型的检测器
2. 检测器注册机制
3. 全局单例管理

如何添加新的检测器类型:
---------------------
1. 创建检测器类，继承 BaseDetector
2. 使用 @DetectorFactory.register('type_name') 装饰器注册
3. 在配置中设置 MODEL_TYPE = 'type_name'

使用示例:
---------
# 使用ONNX检测器
detector = DetectorFactory.create_detector(
    model_type='onnx',
    model_path='weights/best.onnx'
)

# 使用单例模式
detector = DetectorEngine.get_instance(
    model_type='onnx',
    model_path='weights/best.onnx'
)
"""

from typing import Dict, Optional, List, Any
import numpy as np

from detectors.base_detector import BaseDetector, DetectionResult


class DetectorFactory:
    """
    检测器工厂类
    
    支持注册和创建不同类型的检测器。
    """
    
    # 检测器类型注册表
    _registry: Dict[str, type] = {}
    
    @classmethod
    def register(cls, model_type: str):
        """
        检测器注册装饰器
        
        使用示例:
            @DetectorFactory.register('onnx')
            class ONNXDetector(BaseDetector):
                pass
        
        Args:
            model_type: 检测器类型名称
        """
        def decorator(detector_class):
            cls._registry[model_type] = detector_class
            return detector_class
        return decorator
    
    @classmethod
    def create_detector(
        cls,
        model_type: str = 'onnx',
        model_path: Optional[str] = None,
        class_labels: Optional[List[str]] = None,
        confidence: float = 0.5,
        iou: float = 0.45,
        **kwargs
    ) -> BaseDetector:
        """
        创建检测器实例
        
        Args:
            model_type: 检测器类型 ('onnx', 'pytorch', 'tensorflow')
            model_path: 模型文件路径
            class_labels: 类别标签列表
            confidence: 置信度阈值
            iou: IOU阈值
            **kwargs: 其他检测器特定参数
        
        Returns:
            检测器实例
        
        Raises:
            ValueError: 不支持的检测器类型
            FileNotFoundError: 模型文件不存在
        """
        if model_type not in cls._registry:
            available_types = list(cls._registry.keys())
            raise ValueError(
                f"不支持的检测器类型: {model_type}。"
                f"可用类型: {available_types}"
            )
        
        detector_class = cls._registry[model_type]
        
        # 创建检测器实例
        return detector_class(
            model_path=model_path,
            class_labels=class_labels,
            confidence_threshold=confidence,
            iou_threshold=iou,
            **kwargs
        )
    
    @classmethod
    def get_registered_types(cls) -> List[str]:
        """获取已注册的检测器类型"""
        return list(cls._registry.keys())


class DetectorEngine:
    """
    检测引擎管理类 (单例模式)
    
    提供统一的检测接口，支持图片、视频、批量检测。
    使用单例模式确保全局只有一个检测器实例。
    """
    
    _instance: Optional['DetectorEngine'] = None
    _detector: Optional[BaseDetector] = None
    
    def __new__(cls, *args, **kwargs):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(
        self,
        model_type: str = 'onnx',
        model_path: Optional[str] = None,
        class_labels: Optional[List[str]] = None,
        confidence: float = 0.5,
        iou: float = 0.45,
        **kwargs
    ):
        """
        初始化检测引擎
        
        Args:
            model_type: 检测器类型
            model_path: 模型路径
            class_labels: 类别标签
            confidence: 置信度阈值
            iou: IOU阈值
        """
        if self._detector is None and model_path:
            self.load_model(model_type, model_path, class_labels, confidence, iou, **kwargs)
    
    @classmethod
    def get_instance(
        cls,
        model_type: str = 'onnx',
        model_path: Optional[str] = None,
        **kwargs
    ) -> 'DetectorEngine':
        """
        获取检测引擎实例
        
        Args:
            model_type: 检测器类型
            model_path: 模型路径
            **kwargs: 其他参数
        
        Returns:
            DetectorEngine实例
        """
        if cls._instance is None:
            cls._instance = cls(model_type=model_type, model_path=model_path, **kwargs)
        return cls._instance
    
    def load_model(
        self,
        model_type: str = 'onnx',
        model_path: str = None,
        class_labels: Optional[List[str]] = None,
        confidence: float = 0.5,
        iou: float = 0.45,
        **kwargs
    ) -> bool:
        """
        加载模型
        
        Args:
            model_type: 检测器类型
            model_path: 模型路径
            class_labels: 类别标签
            confidence: 置信度阈值
            iou: IOU阈值
        
        Returns:
            是否加载成功
        """
        try:
            self._detector = DetectorFactory.create_detector(
                model_type=model_type,
                model_path=model_path,
                class_labels=class_labels,
                confidence=confidence,
                iou=iou,
                **kwargs
            )
            print(f"模型加载成功: {model_path}")
            return True
        except Exception as e:
            print(f"模型加载失败: {e}")
            self._detector = None
            return False
    
    @property
    def detector(self) -> Optional[BaseDetector]:
        """获取检测器实例"""
        return self._detector
    
    def detect_image(
        self,
        image_path: str,
        params: Optional[Dict] = None
    ) -> Dict:
        """
        检测单张图片
        
        Args:
            image_path: 图片路径
            params: 检测参数 {'confidence': 0.5, 'iou_threshold': 0.5}
        
        Returns:
            检测结果字典
        """
        import cv2
        
        if self._detector is None:
            return {'success': False, 'error': '模型未加载'}
        
        if not os.path.exists(image_path):
            return {'success': False, 'error': f'文件不存在: {image_path}'}
        
        try:
            # 读取图片
            image = cv2.imread(image_path)
            if image is None:
                return {'success': False, 'error': '无法读取图片'}
            
            # 获取参数
            conf = params.get('confidence', 0.5) if params else 0.5
            iou = params.get('iou_threshold', 0.45) if params else 0.45
            
            # 执行检测
            result_image, detections = self._detector.detect_and_draw(
                image,
                conf_threshold=conf,
                iou_threshold=iou
            )
            
            # 转换检测结果为字典
            detections_dict = [d.to_dict() if hasattr(d, 'to_dict') else d for d in detections]
            
            return {
                'success': True,
                'detections': detections_dict,
                'image_shape': image.shape[:2],
                'result_image': result_image,
                'inference_time': 0
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def detect_image_array(
        self,
        image: np.ndarray,
        params: Optional[Dict] = None
    ) -> Dict:
        """
        检测图像数组（直接传入numpy数组）
        
        Args:
            image: BGR格式的图像数组
            params: 检测参数
        
        Returns:
            检测结果字典
        """
        if self._detector is None:
            return {'success': False, 'error': '模型未加载'}
        
        try:
            conf = params.get('confidence', 0.5) if params else 0.5
            iou = params.get('iou_threshold', 0.45) if params else 0.45
            
            result_image, detections = self._detector.detect_and_draw(
                image,
                conf_threshold=conf,
                iou_threshold=iou
            )
            
            # 转换检测结果为字典
            detections_dict = [d.to_dict() if hasattr(d, 'to_dict') else d for d in detections]
            
            return {
                'success': True,
                'detections': detections_dict,
                'image_shape': image.shape[:2],
                'result_image': result_image
            }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def detect_video(
        self,
        video_path: str,
        params: Optional[Dict] = None,
        callback: Optional[callable] = None,
        save_video: bool = True,
        output_path: Optional[str] = None,
        frame_step: int = 10
    ) -> Dict:
        """
        检测视频（支持抽帧）
        
        Args:
            video_path: 视频路径
            params: 检测参数
            callback: 进度回调函数 callback(progress: int)
            save_video: 是否保存检测后的视频
            output_path: 输出视频路径（可选）
            frame_step: 抽帧步长，每N帧取1帧检测（默认10）
        
        Returns:
            检测结果字典
        """
        import cv2
        import os
        import time
        
        if self._detector is None:
            return {'success': False, 'error': '模型未加载'}
        
        if not os.path.exists(video_path):
            return {'success': False, 'error': f'文件不存在: {video_path}'}
        
        try:
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                return {'success': False, 'error': '无法打开视频'}
            
            # 获取视频信息
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # 设置输出路径
            if output_path is None:
                base_name = os.path.basename(video_path)
                name_without_ext = os.path.splitext(base_name)[0]
                uploads_dir = os.path.dirname(video_path)
                outputs_dir = os.path.join(os.path.dirname(uploads_dir), 'outputs')
                os.makedirs(outputs_dir, exist_ok=True)
                output_path = os.path.join(outputs_dir, f"{name_without_ext}_detected.mp4")
            
            # 创建视频写入器
            out = None
            if save_video:
                codecs = ['avc1', 'H264', 'X264', 'mp4v']
                for codec in codecs:
                    try:
                        fourcc = cv2.VideoWriter_fourcc(*codec)
                        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
                        if out.isOpened():
                            print(f"使用编码器: {codec}")
                            break
                        else:
                            out = None
                    except:
                        continue
            
            # 获取参数
            conf = params.get('confidence', 0.5) if params else 0.5
            iou = params.get('iou_threshold', 0.45) if params else 0.45
            
            all_results = []
            detection_map = {}
            frame_index = 0
            start_time = time.time()
            
            print(f"开始处理视频: {video_path}")
            print(f"总帧数: {total_frames}, FPS: {fps}, 抽帧步长: {frame_step}")
            
            # 第一遍：逐帧读取并检测
            frames_to_save = []
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frames_to_save.append(frame.copy())
                
                # 按步长抽帧检测
                if frame_index % frame_step == 0:
                    detections = self._detector.detect(frame, conf_threshold=conf, iou_threshold=iou)
                    # 转换为字典
                    detections_dict = [d.to_dict() if hasattr(d, 'to_dict') else d for d in detections]
                    detection_map[frame_index] = detections_dict
                    all_results.append({
                        'frame_index': frame_index,
                        'detections': detections_dict
                    })
                
                frame_index += 1
                
                # 更新进度
                if callback and frame_index % 10 == 0:
                    progress = int((frame_index / total_frames) * 80)
                    callback(progress)
            
            cap.release()
            print(f"读取完成，共 {len(frames_to_save)} 帧，检测了 {len(detection_map)} 帧")
            
            # 第二遍：保存视频
            if save_video and out is not None:
                for idx, frame in enumerate(frames_to_save):
                    detect_idx = (idx // frame_step) * frame_step
                    detections_dict = detection_map.get(detect_idx, [])
                    
                    # 将字典转换回DetectionResult对象用于绘制
                    detections = [
                        DetectionResult(
                            class_id=d.get('class_id', 0),
                            class_name=d.get('class_name', ''),
                            confidence=d.get('confidence', 0),
                            bbox=d.get('bbox', {})
                        ) for d in detections_dict
                    ]
                    
                    result_frame = self._detector.draw_detections(frame.copy(), detections)
                    out.write(result_frame)
                    
                    if callback and idx % 30 == 0:
                        progress = 80 + int((idx / len(frames_to_save)) * 20)
                        callback(progress)
                
                out.release()
            
            elapsed_time = time.time() - start_time
            print(f"视频处理完成，耗时: {elapsed_time:.2f}秒")
            
            if callback:
                callback(100)
            
            return {
                'success': True,
                'total_frames': total_frames,
                'detected_frames': len(detection_map),
                'fps': fps,
                'resolution': f'{width}x{height}',
                'frame_step': frame_step,
                'elapsed_time': round(elapsed_time, 2),
                'all_results': all_results,
                'output_path': output_path if save_video else None
            }
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def get_model_info(self) -> Optional[Dict]:
        """获取模型信息"""
        if self._detector:
            return self._detector.get_model_info()
        return None


# 导入 os 模块 (在模块顶部会被覆盖)
import os
