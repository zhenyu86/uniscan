# -*- coding: utf-8 -*-
"""
检测引擎模块
基于 onnx_detect.py 重构，提供统一的检测接口

【配置说明】
1. 修改 DEFAULT_CLASS_LABELS 来设置默认类别名称
2. 修改 DEFAULT_CONFIDENCE 和 DEFAULT_IOU 来设置默认阈值
3. 如需修改检测逻辑，请参考 _process_detections 方法
"""

import os
import cv2
import numpy as np
import onnxruntime as ort
import time
from typing import List, Dict, Optional, Tuple, Callable


# ==================== 配置区域 ====================
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


class ONNXDetector:
    """
    ONNX目标检测器
    基于ONNX Runtime的高性能目标检测引擎
    """

    def __init__(
        self,
        model_path: str,
        class_labels: Optional[List[str]] = None,
        confidence_threshold: float = DEFAULT_CONFIDENCE,
        iou_threshold: float = DEFAULT_IOU
    ):
        """
        初始化检测器

        Args:
            model_path: ONNX模型文件路径
            class_labels: 类别标签列表，为None时使用默认值
            confidence_threshold: 置信度阈值
            iou_threshold: IOU阈值（用于NMS）
        """
        self.model_path = model_path
        self.class_labels = class_labels or DEFAULT_CLASS_LABELS
        self.confidence_threshold = confidence_threshold
        self.iou_threshold = iou_threshold

        # 生成颜色映射
        self.color_map = np.random.uniform(0, 255, size=(len(self.class_labels), 3))

        # 当前处理的图片尺寸
        self.original_width = 0
        self.original_height = 0

        # 初始化ONNX Runtime会话
        self._init_session()

    def _init_session(self):
        """初始化ONNX推理会话（优先使用GPU）"""
        if not os.path.exists(self.model_path):
            raise FileNotFoundError(f"模型文件不存在: {self.model_path}")

        # 获取可用的推理设备
        available_providers = ort.get_available_providers()
        print(f"可用的ONNX Runtime设备: {available_providers}")

        # 优先使用GPU (CUDA)
        if 'CUDAExecutionProvider' in available_providers:
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
            # 显示实际使用的设备
            used_providers = self.session.get_providers()
            print(f"当前使用的设备: {used_providers}")
        except Exception as e:
            print(f"GPU初始化失败，回退到CPU: {e}")
            self.session = ort.InferenceSession(self.model_path, providers=['CPUExecutionProvider'])

        self.input_name = self.session.get_inputs()[0].name
        self.output_names = [output.name for output in self.session.get_outputs()]

        # 获取模型输入尺寸
        input_shape = self.session.get_inputs()[0].shape
        self.input_width = input_shape[2]
        self.input_height = input_shape[3]

        # 预热模型
        self._warmup()

    def _warmup(self):
        """预热模型，加速首次推理"""
        try:
            dummy_input = np.zeros(
                (1, 3, self.input_width, self.input_height),
                dtype=np.float32
            )
            self.session.run(None, {self.input_name: dummy_input})
            print(f"模型预热完成 - 输入尺寸: {self.input_width}x{self.input_height}")
        except Exception as e:
            print(f"模型预热失败: {e}")

    def preprocess(self, image: np.ndarray) -> np.ndarray:
        """
        图像预处理

        Args:
            image: BGR格式的原始图像

        Returns:
            预处理后的模型输入张量
        """
        # 记录原始尺寸
        self.original_height, self.original_width = image.shape[:2]

        # BGR转RGB
        rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # 调整尺寸
        resized = cv2.resize(rgb_image, (self.input_width, self.input_height))

        # 归一化 [0, 1]
        normalized = resized.astype(np.float32) / 255.0

        # HWC -> CHW
        transposed = np.transpose(normalized, (2, 0, 1))

        # 添加batch维度
        batch_input = np.expand_dims(transposed, axis=0)

        return batch_input

    def postprocess(
        self,
        raw_output: List[np.ndarray],
        conf_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None
    ) -> List[Dict]:
        """
        后处理模型输出，提取检测结果

        Args:
            raw_output: 模型原始输出
            conf_threshold: 置信度阈值（可选，覆盖默认值）
            iou_threshold: IOU阈值（可选，覆盖默认值）

        Returns:
            检测结果列表
        """
        conf_threshold = conf_threshold or self.confidence_threshold
        iou_threshold = iou_threshold or self.iou_threshold

        # 处理输出数据 (YOLO格式)
        output_data = np.squeeze(raw_output[0]).T

        # 计算坐标缩放比例
        scale_x = self.original_width / self.input_width
        scale_y = self.original_height / self.input_height

        # 提取类别概率
        class_probs = output_data[:, 4:]
        max_scores = np.amax(class_probs, axis=1)
        class_ids = np.argmax(class_probs, axis=1)

        # 置信度过滤
        valid_indices = np.where(max_scores >= conf_threshold)[0]

        if len(valid_indices) == 0:
            return []

        filtered_output = output_data[valid_indices]
        filtered_scores = max_scores[valid_indices]
        filtered_class_ids = class_ids[valid_indices]

        # 提取并缩放边界框坐标
        center_x = filtered_output[:, 0]
        center_y = filtered_output[:, 1]
        box_width = filtered_output[:, 2]
        box_height = filtered_output[:, 3]

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

                detections.append({
                    'class_id': class_id,
                    'class_name': self.class_labels[class_id] if class_id < len(self.class_labels) else f'class_{class_id}',
                    'confidence': round(float(filtered_scores[idx]), 4),
                    'bbox': {
                        'x': int(box[0]),
                        'y': int(box[1]),
                        'w': int(box[2]),
                        'h': int(box[3])
                    }
                })

        return detections

    def detect(
        self,
        image: np.ndarray,
        conf_threshold: Optional[float] = None,
        iou_threshold: Optional[float] = None
    ) -> List[Dict]:
        """
        对单张图像进行目标检测

        Args:
            image: BGR格式的图像
            conf_threshold: 置信度阈值（可选）
            iou_threshold: IOU阈值（可选）

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
    ) -> Tuple[np.ndarray, List[Dict]]:
        """
        检测并在图像上绘制结果

        Args:
            image: BGR格式的图像
            conf_threshold: 置信度阈值（可选）
            iou_threshold: IOU阈值（可选）
            show_label: 是否显示标签
            line_thickness: 边界框线条粗细

        Returns:
            (绘制后的图像, 检测结果列表)
        """
        detections = self.detect(image, conf_threshold, iou_threshold)
        result_image = self.draw_detections(image.copy(), detections, show_label, line_thickness)
        return result_image, detections

    def draw_detections(
        self,
        image: np.ndarray,
        detections: List[Dict],
        show_label: bool = True,
        line_thickness: int = 2
    ) -> np.ndarray:
        """
        在图像上绘制检测结果

        Args:
            image: 图像
            detections: 检测结果列表
            show_label: 是否显示标签
            line_thickness: 线条粗细

        Returns:
            绘制后的图像
        """
        for det in detections:
            bbox = det['bbox']
            x, y, w, h = bbox['x'], bbox['y'], bbox['w'], bbox['h']
            class_id = det.get('class_id', 0)
            confidence = det['confidence']

            # 获取颜色
            color = tuple(map(int, self.color_map[class_id % len(self.color_map)]))

            # 绘制边界框
            cv2.rectangle(image, (x, y), (x + w, y + h), color, line_thickness)

            if show_label:
                # 标签文本
                label = f"{det['class_name']} {confidence:.2f}"

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
    ):
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
            'input_size': f'{self.input_width}x{self.input_height}',
            'class_count': len(self.class_labels),
            'class_names': self.class_labels,
            'confidence_threshold': self.confidence_threshold,
            'iou_threshold': self.iou_threshold,
            'providers': self.session.get_providers()
        }


class DetectorEngine:
    """
    检测引擎管理类
    提供统一的检测接口，支持图片、视频、批量检测
    """

    _instance = None
    _detector = None

    def __new__(cls, model_path=None, **kwargs):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(
        self,
        model_path: Optional[str] = None,
        class_labels: Optional[List[str]] = None,
        confidence: float = DEFAULT_CONFIDENCE,
        iou: float = DEFAULT_IOU
    ):
        """
        初始化检测引擎

        Args:
            model_path: 模型路径
            class_labels: 类别标签
            confidence: 置信度阈值
            iou: IOU阈值
        """
        if self._detector is None and model_path:
            self.load_model(model_path, class_labels, confidence, iou)

    def load_model(
        self,
        model_path: str,
        class_labels: Optional[List[str]] = None,
        confidence: float = DEFAULT_CONFIDENCE,
        iou: float = DEFAULT_IOU
    ) -> bool:
        """
        加载模型

        Args:
            model_path: 模型路径
            class_labels: 类别标签
            confidence: 置信度阈值
            iou: IOU阈值

        Returns:
            是否加载成功
        """
        try:
            self._detector = ONNXDetector(
                model_path=model_path,
                class_labels=class_labels,
                confidence_threshold=confidence,
                iou_threshold=iou
            )
            print(f"模型加载成功: {model_path}")
            return True
        except Exception as e:
            print(f"模型加载失败: {e}")
            self._detector = None
            return False

    @property
    def detector(self) -> Optional[ONNXDetector]:
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
            conf = params.get('confidence', DEFAULT_CONFIDENCE) if params else DEFAULT_CONFIDENCE
            iou = params.get('iou_threshold', DEFAULT_IOU) if params else DEFAULT_IOU

            # 执行检测
            result_image, detections = self._detector.detect_and_draw(
                image,
                conf_threshold=conf,
                iou_threshold=iou
            )

            return {
                'success': True,
                'detections': detections,
                'image_shape': image.shape[:2],
                'result_image': result_image,
                'inference_time': 0  # 可以添加计时
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
            conf = params.get('confidence', DEFAULT_CONFIDENCE) if params else DEFAULT_CONFIDENCE
            iou = params.get('iou_threshold', DEFAULT_IOU) if params else DEFAULT_IOU

            result_image, detections = self._detector.detect_and_draw(
                image,
                conf_threshold=conf,
                iou_threshold=iou
            )

            return {
                'success': True,
                'detections': detections,
                'image_shape': image.shape[:2],
                'result_image': result_image
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def detect_video(
        self,
        video_path: str,
        params: Optional[Dict] = None,
        callback: Optional[Callable[[int], None]] = None,
        save_video: bool = True,
        output_path: Optional[str] = None,
        frame_step: int = 10,
        batch_size: int = 1
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

            # 设置输出路径（保存到outputs目录）
            if output_path is None:
                base_name = os.path.basename(video_path)
                name_without_ext = os.path.splitext(base_name)[0]
                # 获取outputs目录（与uploads同级）
                uploads_dir = os.path.dirname(video_path)
                outputs_dir = os.path.join(os.path.dirname(uploads_dir), 'outputs')
                os.makedirs(outputs_dir, exist_ok=True)
                output_path = os.path.join(outputs_dir, f"{name_without_ext}_detected.mp4")

            # 创建视频写入器（尝试H.264编码，浏览器兼容性更好）
            out = None
            if save_video:
                # 尝试不同的编码器
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
                
                if out is None:
                    print("警告: 无法创建视频写入器")

            # 获取参数
            conf = params.get('confidence', DEFAULT_CONFIDENCE) if params else DEFAULT_CONFIDENCE
            iou = params.get('iou_threshold', DEFAULT_IOU) if params else DEFAULT_IOU

            all_results = []
            detection_map = {}  # frame_index -> detections
            frame_index = 0
            start_time = time.time()

            print(f"开始处理视频: {video_path}")
            print(f"总帧数: {total_frames}, FPS: {fps}, 抽帧步长: {frame_step}")

            # 第一遍：逐帧读取并检测需要抽样的帧
            frames_to_save = []  # 保存所有帧用于输出
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frames_to_save.append(frame.copy())
                
                # 按步长抽帧检测
                if frame_index % frame_step == 0:
                    detections = self._detector.detect(frame, conf_threshold=conf, iou_threshold=iou)
                    detection_map[frame_index] = detections
                    all_results.append({
                        'frame_index': frame_index,
                        'detections': detections
                    })
                
                frame_index += 1
                
                # 更新进度（检测阶段占80%）
                if callback and frame_index % 10 == 0:
                    progress = int((frame_index / total_frames) * 80)
                    callback(progress)

            cap.release()
            print(f"读取完成，共 {len(frames_to_save)} 帧，检测了 {len(detection_map)} 帧")

            # 第二遍：应用检测结果到所有帧并保存视频
            if save_video and out is not None:
                for idx, frame in enumerate(frames_to_save):
                    # 找到最近的检测帧
                    detect_idx = (idx // frame_step) * frame_step
                    detections = detection_map.get(detect_idx, [])
                    
                    # 绘制检测结果
                    result_frame = self._detector.draw_detections(frame.copy(), detections)
                    out.write(result_frame)
                    
                    # 更新进度（保存阶段占20%）
                    if callback and idx % 30 == 0:
                        progress = 80 + int((idx / len(frames_to_save)) * 20)
                        callback(progress)
                
                out.release()

            # 转换视频为浏览器兼容格式 (H.264)
            if save_video and output_path and os.path.exists(output_path):
                output_path = self._convert_to_browser_compatible(output_path)

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

    def _convert_to_browser_compatible(self, video_path: str) -> str:
        """
        将视频转换为浏览器兼容的H.264格式
        
        Args:
            video_path: 原始视频路径
            
        Returns:
            转换后的视频路径
        """
        try:
            import subprocess
            
            # 检查 ffmpeg 是否可用
            try:
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
            except:
                print("ffmpeg 不可用，跳过视频转换")
                return video_path
            
            # 生成输出路径
            base_name = os.path.splitext(video_path)[0]
            converted_path = f"{base_name}_h264.mp4"
            
            # 使用 ffmpeg 转换
            cmd = [
                'ffmpeg', '-y',
                '-i', video_path,
                '-c:v', 'libx264',
                '-preset', 'fast',
                '-crf', '23',
                '-pix_fmt', 'yuv420p',
                '-movflags', '+faststart',
                converted_path
            ]
            
            print(f"正在转换视频为H.264格式...")
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0 and os.path.exists(converted_path):
                # 删除原始文件，重命名转换后的文件
                os.remove(video_path)
                os.rename(converted_path, video_path)
                print(f"视频转换完成: {video_path}")
                return video_path
            else:
                print(f"视频转换失败: {result.stderr}")
                return video_path
                
        except Exception as e:
            print(f"视频转换出错: {e}")
            return video_path

    def detect_batch(
        self,
        image_dir: str,
        params: Optional[Dict] = None,
        output_dir: Optional[str] = None,
        callback: Optional[Callable[[int, int], None]] = None
    ) -> Dict:
        """
        批量检测图片

        Args:
            image_dir: 图片目录
            params: 检测参数
            output_dir: 输出目录（可选）
            callback: 进度回调 callback(current, total)

        Returns:
            检测结果字典
        """
        if self._detector is None:
            return {'success': False, 'error': '模型未加载'}

        if not os.path.exists(image_dir):
            return {'success': False, 'error': f'目录不存在: {image_dir}'}

        try:
            # 获取图片文件列表
            image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
            image_files = [
                f for f in os.listdir(image_dir)
                if os.path.splitext(f)[1].lower() in image_extensions
            ]

            if not image_files:
                return {'success': False, 'error': '目录中没有图片文件'}

            # 设置输出目录
            if output_dir is None:
                output_dir = os.path.join(image_dir, 'results')
            os.makedirs(output_dir, exist_ok=True)

            # 获取参数
            conf = params.get('confidence', DEFAULT_CONFIDENCE) if params else DEFAULT_CONFIDENCE
            iou = params.get('iou_threshold', DEFAULT_IOU) if params else DEFAULT_IOU

            all_results = []
            start_time = time.time()

            for idx, filename in enumerate(image_files):
                image_path = os.path.join(image_dir, filename)

                # 读取并检测
                image = cv2.imread(image_path)
                if image is None:
                    continue

                result_image, detections = self._detector.detect_and_draw(
                    image,
                    conf_threshold=conf,
                    iou_threshold=iou
                )

                # 保存结果图片
                output_path = os.path.join(output_dir, filename)
                cv2.imwrite(output_path, result_image)

                all_results.append({
                    'filename': filename,
                    'detections': detections,
                    'output_path': output_path
                })

                # 更新进度
                if callback:
                    callback(idx + 1, len(image_files))

            elapsed_time = time.time() - start_time
            avg_time = elapsed_time / len(image_files) if image_files else 0

            return {
                'success': True,
                'total_images': len(image_files),
                'elapsed_time': round(elapsed_time, 2),
                'avg_time_per_image': round(avg_time, 3),
                'output_dir': output_dir,
                'results': all_results
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def detect_stream(
        self,
        stream_url: str,
        params: Optional[Dict] = None
    ):
        """
        检测视频流（生成器）

        Args:
            stream_url: 视频流URL (RTSP/RTMP/HTTP等)
            params: 检测参数

        Yields:
            检测结果字典
        """
        if self._detector is None:
            yield {'success': False, 'error': '模型未加载'}
            return

        try:
            cap = cv2.VideoCapture(stream_url)
            if not cap.isOpened():
                yield {'success': False, 'error': f'无法连接视频流: {stream_url}'}
                return

            conf = params.get('confidence', DEFAULT_CONFIDENCE) if params else DEFAULT_CONFIDENCE
            iou = params.get('iou_threshold', DEFAULT_IOU) if params else DEFAULT_IOU

            while True:
                ret, frame = cap.read()
                if not ret:
                    break

                # 检测
                detections = self._detector.detect(frame, conf_threshold=conf, iou_threshold=iou)
                result_frame = self._detector.draw_detections(frame.copy(), detections)

                # 编码为JPEG
                _, buffer = cv2.imencode('.jpg', result_frame)

                yield {
                    'success': True,
                    'frame': buffer.tobytes(),
                    'detections': detections
                }

            cap.release()

        except Exception as e:
            yield {'success': False, 'error': str(e)}

    def save_result_image(self, image: np.ndarray, output_path: str) -> bool:
        """
        保存结果图片

        Args:
            image: 图像数组
            output_path: 输出路径

        Returns:
            是否保存成功
        """
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            cv2.imwrite(output_path, image)
            return True
        except Exception as e:
            print(f"保存图片失败: {e}")
            return False

    def get_model_info(self) -> Optional[Dict]:
        """获取模型信息"""
        if self._detector:
            return self._detector.get_model_info()
        return None


# ==================== 便捷函数 ====================

def create_detector(
    model_path: str,
    class_labels: Optional[List[str]] = None,
    confidence: float = DEFAULT_CONFIDENCE,
    iou: float = DEFAULT_IOU
) -> DetectorEngine:
    """
    创建检测引擎实例

    Args:
        model_path: 模型路径
        class_labels: 类别标签
        confidence: 置信度阈值
        iou: IOU阈值

    Returns:
        DetectorEngine实例
    """
    return DetectorEngine(model_path, class_labels, confidence, iou)


def quick_detect(
    image_path: str,
    model_path: str = 'weights/best.onnx',
    class_labels: Optional[List[str]] = None,
    confidence: float = DEFAULT_CONFIDENCE,
    iou: float = DEFAULT_IOU,
    output_path: Optional[str] = None
) -> Dict:
    """
    快速检测单张图片

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
    detector = create_detector(model_path, class_labels, confidence, iou)
    result = detector.detect_image(image_path, {'confidence': confidence, 'iou_threshold': iou})

    if result['success'] and output_path:
        detector.save_result_image(result['result_image'], output_path)

    return result
