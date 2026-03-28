# -*- coding: utf-8 -*-
"""Task executor module
Move heavy task execution logic here to improve modularity."""

import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor


class TaskExecutor:
    """任务执行器"""

    def __init__(self, max_workers=4, app=None):
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.running_tasks = {}
        self.app = app
        self._stop_flags = {}  # 任务停止标志

    def init_app(self, app):
        """初始化 Flask 应用"""
        self.app = app

    def submit_task(self, task_id):
        """提交检测任务"""
        if not self.app:
            print("错误: TaskExecutor 未初始化 Flask 应用，请调用 init_app()")
            return None
        self._stop_flags[task_id] = False
        future = self.executor.submit(self._execute_task, task_id)
        self.running_tasks[task_id] = future
        return future

    def cancel_task(self, task_id):
        """取消单个任务"""
        if task_id in self._stop_flags:
            self._stop_flags[task_id] = True
            print(f"任务 {task_id} 已设置停止标志")

    def cancel_all_tasks(self):
        """取消所有正在运行的任务"""
        for task_id in list(self._stop_flags.keys()):
            self._stop_flags[task_id] = True
        print(f"已设置 {len(self._stop_flags)} 个任务的停止标志")

    def is_task_cancelled(self, task_id):
        """检查任务是否被取消"""
        return self._stop_flags.get(task_id, False)

    def _execute_task(self, task_id):
        """执行检测任务"""
        from models.task import DetectionTask, DetectionResult
        from models.device import UploadRecord, Device
        from utils.detector_engine import DetectorEngine
        from utils.rule_engine import RuleEngine
        from utils.alert_manager import AlertManager
        from models.rule import AlertRule
        from models.user import db

        if not self.app:
            print("错误: TaskExecutor 未初始化 Flask 应用")
            return

        with self.app.app_context():
            task = DetectionTask.query.get(task_id)
            if not task:
                print(f"任务 {task_id} 不存在")
                return

            try:
                task.status = 'processing'
                task.started_at = datetime.now()
                db.session.commit()
                print(f"任务 {task_id} 开始执行")

                model_path = self.app.config.get('MODEL_PATH', 'weights/best.onnx')
                engine = DetectorEngine(model_path)

                params = task.params or {}
                confidence = params.get('confidence', 0.5)
                iou_threshold = params.get('iou_threshold', 0.45)

                if task.source_type == 'upload':
                    record = UploadRecord.query.get(task.source_id)
                    if not record:
                        raise Exception(f'上传记录 {task.source_id} 不存在')
                    file_path = record.file_path
                elif task.source_type == 'device':
                    device = Device.query.get(task.source_id)
                    if not device:
                        raise Exception(f'设备 {task.source_id} 不存在')
                    file_path = device.address
                elif task.source_type == 'url':
                    file_path = params.get('url')
                else:
                    raise Exception(f'未知的来源类型: {task.source_type}')

                import os
                if not os.path.exists(file_path):
                    raise Exception(f'文件不存在: {file_path}')

                def progress_callback(progress):
                    # 检查是否被取消
                    if self.is_task_cancelled(task_id):
                        return False  # 返回 False 停止处理
                    task.progress = progress
                    try:
                        db.session.commit()
                    except Exception:
                        db.session.rollback()
                    return True

                frame_step = params.get('frame_step', 10)

                # 检查是否被取消
                if self.is_task_cancelled(task_id):
                    task.status = 'cancelled'
                    task.completed_at = datetime.now()
                    db.session.commit()
                    print(f"任务 {task_id} 已取消")
                    return

                if task.task_type == 'image':
                    result = engine.detect_image(file_path, {
                        'confidence': confidence,
                        'iou_threshold': iou_threshold
                    })
                elif task.task_type == 'video':
                    result = engine.detect_video(file_path, {
                        'confidence': confidence,
                        'iou_threshold': iou_threshold
                    }, callback=progress_callback, frame_step=frame_step)
                elif task.task_type == 'stream':
                    result = engine.detect_stream(file_path, {
                        'confidence': confidence,
                        'iou_threshold': iou_threshold
                    })
                else:
                    result = engine.detect_image(file_path, {
                        'confidence': confidence,
                        'iou_threshold': iou_threshold
                    })

                # 检查是否被取消
                if self.is_task_cancelled(task_id):
                    task.status = 'cancelled'
                    task.completed_at = datetime.now()
                    db.session.commit()
                    print(f"任务 {task_id} 已取消")
                    return

                if result['success']:
                    all_detections = []

                    if isinstance(result, dict) and 'all_results' in result:
                        for frame_result in result['all_results']:
                            # 检查是否被取消
                            if self.is_task_cancelled(task_id):
                                task.status = 'cancelled'
                                task.completed_at = datetime.now()
                                db.session.commit()
                                print(f"任务 {task_id} 已取消")
                                return
                            
                            frame_index = frame_result['frame_index']
                            for det in frame_result['detections']:
                                all_detections.append(det)
                                bbox = det['bbox']
                                dr = DetectionResult(
                                    task_id=task.id,
                                    frame_index=frame_index,
                                    class_id=det.get('class_id', 0),
                                    class_name=det['class_name'],
                                    confidence=det['confidence'],
                                    bbox_x=bbox['x'],
                                    bbox_y=bbox['y'],
                                    bbox_w=bbox['w'],
                                    bbox_h=bbox['h']
                                )
                                db.session.add(dr)
                    else:
                        all_detections = result.get('detections', [])
                        for det in all_detections:
                            bbox = det['bbox']
                            dr = DetectionResult(
                                task_id=task.id,
                                frame_index=0,
                                class_id=det.get('class_id', 0),
                                class_name=det['class_name'],
                                confidence=det['confidence'],
                                bbox_x=bbox['x'],
                                bbox_y=bbox['y'],
                                bbox_w=bbox['w'],
                                bbox_h=bbox['h']
                            )
                            db.session.add(dr)

                    task.status = 'completed'
                    task.progress = 100
                    task.result_summary = {
                        'total_detections': len(all_detections),
                        'total_frames': result.get('total_frames', 0),
                        'detected_frames': result.get('detected_frames', 0),
                        'frame_step': frame_step,
                        'detections': all_detections[:100]
                    }
                    task.result_path = result.get('output_path')
                    task.completed_at = datetime.now()

                    print(f"任务 {task_id} 执行完成，检测到 {len(all_detections)} 个目标")

                    # 根据系统设置中的告警类别创建告警
                    try:
                        from models.config import SystemConfig
                        from models.alert import Alert
                        
                        config = SystemConfig.query.filter_by(config_key='alert_categories').first()
                        if config and config.config_value:
                            alert_categories = json.loads(config.config_value)
                            enabled_categories = {cat['name']: cat for cat in alert_categories if cat.get('enabled', True)}
                            
                            # 统计各类别检测数量
                            class_counts = {}
                            for det in all_detections:
                                class_name = det.get('class_name', '')
                                if class_name in enabled_categories:
                                    class_counts[class_name] = class_counts.get(class_name, 0) + 1
                            
                            # 为检测到的每个告警类别创建告警
                            for class_name, count in class_counts.items():
                                cat_info = enabled_categories[class_name]
                                alert = Alert(
                                    task_id=task.id,
                                    level=cat_info.get('level', 'warning'),
                                    content=f"检测到 {count} 个 {class_name}",
                                    details={'class_name': class_name, 'count': count},
                                    status='pending'
                                )
                                db.session.add(alert)
                                print(f"创建告警: {class_name} x {count}")
                    except Exception as e:
                        print(f"创建告警失败: {e}")
                    
                    print(f"任务 {task_id} 告警检查完成")
                else:
                    task.status = 'failed'
                    task.error_msg = result.get('error', '检测失败')
                    print(f"任务 {task_id} 检测失败: {task.error_msg}")

                db.session.commit()

            except Exception as e:
                task.status = 'failed'
                task.error_msg = str(e)
                try:
                    db.session.commit()
                except Exception:
                    db.session.rollback()
                print(f"任务 {task_id} 执行失败: {e}")

            finally:
                if task_id in self.running_tasks:
                    del self.running_tasks[task_id]
                if task_id in self._stop_flags:
                    del self._stop_flags[task_id]
