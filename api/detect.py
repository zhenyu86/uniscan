# -*- coding: utf-8 -*-
"""
检测API
处理图片/视频检测、任务管理
"""

import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, send_file
from werkzeug.utils import secure_filename
from flask_login import current_user
from models.user import db
from models.device import UploadRecord, Device
from models.task import DetectionTask, DetectionResult
from models.scene import Scene
from utils.auth import login_required, log_operation
from utils.detector_engine import DetectorEngine
from utils.alert_manager import AlertManager
from utils.rule_engine import RuleEngine
from models.rule import AlertRule

detect_bp = Blueprint('detect', __name__, url_prefix='/api/v1/detect')


def allowed_file(filename, allowed_extensions):
    """检查文件类型"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


@detect_bp.route('/upload/image', methods=['POST'])
@login_required
def upload_image():
    """上传图片（仅上传，不自动检测）"""
    if 'file' not in request.files:
        return jsonify({'code': 400, 'message': '没有选择文件', 'data': None})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'code': 400, 'message': '没有选择文件', 'data': None})

    allowed = current_app.config['ALLOWED_IMAGE_EXTENSIONS']
    if not allowed_file(file.filename, allowed):
        return jsonify({'code': 400, 'message': '不支持的文件格式', 'data': None})

    # 生成安全的文件名
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

    # 确保目录存在
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    # 保存文件
    file.save(filepath)
    file_size = os.path.getsize(filepath)

    # 创建上传记录
    record = UploadRecord(
        user_id=current_user.id,
        file_name=file.filename,
        file_path=filepath,
        file_type='image',
        file_size=file_size,
        status='completed'
    )

    db.session.add(record)
    db.session.commit()

    log_operation(current_user.id, 'upload_image', f'上传图片: {file.filename}')

    return jsonify({
        'code': 200,
        'message': '上传成功',
        'data': record.to_dict()
    })


@detect_bp.route('/upload/video', methods=['POST'])
@login_required
def upload_video():
    """上传视频（仅上传，不自动检测）"""
    if 'file' not in request.files:
        return jsonify({'code': 400, 'message': '没有选择文件', 'data': None})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'code': 400, 'message': '没有选择文件', 'data': None})

    allowed = current_app.config['ALLOWED_VIDEO_EXTENSIONS']
    if not allowed_file(file.filename, allowed):
        return jsonify({'code': 400, 'message': '不支持的文件格式', 'data': None})

    # 生成安全的文件名
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)

    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    file.save(filepath)
    file_size = os.path.getsize(filepath)

    # 创建上传记录
    record = UploadRecord(
        user_id=current_user.id,
        file_name=file.filename,
        file_path=filepath,
        file_type='video',
        file_size=file_size,
        status='completed'
    )

    db.session.add(record)
    db.session.commit()

    log_operation(current_user.id, 'upload_video', f'上传视频: {file.filename}')

    return jsonify({
        'code': 200,
        'message': '上传成功',
        'data': record.to_dict()
    })


@detect_bp.route('/task', methods=['POST'])
@login_required
def create_task():
    """创建检测任务"""
    from models.config import SystemConfig
    
    data = request.get_json()

    source_type = data.get('source_type', 'upload')
    source_id = data.get('source_id')
    task_type = data.get('task_type', 'image')
    scene_id = data.get('scene_id')
    params = data.get('params', {})
    
    # 从系统配置获取默认参数
    if 'confidence' not in params:
        config = SystemConfig.query.filter_by(config_key='detection_confidence').first()
        if config:
            params['confidence'] = float(config.config_value)
        else:
            params['confidence'] = 0.5
            
    if 'iou_threshold' not in params:
        config = SystemConfig.query.filter_by(config_key='detection_iou').first()
        if config:
            params['iou_threshold'] = float(config.config_value)
        else:
            params['iou_threshold'] = 0.45
            
    if 'frame_step' not in params:
        config = SystemConfig.query.filter_by(config_key='frame_step').first()
        if config:
            params['frame_step'] = int(config.config_value)
        else:
            params['frame_step'] = 10

    # 创建任务
    task = DetectionTask(
        task_type=task_type,
        source_type=source_type,
        source_id=source_id,
        scene_id=scene_id,
        params=params,
        status='queued',
        created_by=current_user.id
    )

    db.session.add(task)
    db.session.commit()

    # 异步执行检测任务
    from app import task_executor
    task_executor.submit_task(task.id)

    log_operation(current_user.id, 'create_detection_task', f'创建检测任务: {task.id}')

    return jsonify({
        'code': 200,
        'message': '任务创建成功',
        'data': task.to_dict()
    })


@detect_bp.route('/tasks', methods=['GET'])
@login_required
def get_tasks():
    """获取任务列表"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    status = request.args.get('status')
    task_type = request.args.get('task_type')

    query = DetectionTask.query

    if status:
        query = query.filter_by(status=status)
    if task_type:
        query = query.filter_by(task_type=task_type)

    pagination = query.order_by(DetectionTask.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'items': [t.to_dict() for t in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page,
            'per_page': per_page
        }
    })


@detect_bp.route('/tasks/<int:task_id>', methods=['GET'])
@login_required
def get_task(task_id):
    """获取任务详情"""
    task = DetectionTask.query.get(task_id)
    if not task:
        return jsonify({'code': 404, 'message': '任务不存在', 'data': None})

    data = task.to_dict()

    # 获取检测结果
    results = DetectionResult.query.filter_by(task_id=task_id).limit(100).all()
    data['results'] = [r.to_dict() for r in results]

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': data
    })


@detect_bp.route('/tasks/<int:task_id>/cancel', methods=['POST'])
@login_required
def cancel_task(task_id):
    """取消任务"""
    from app import task_executor
    
    task = DetectionTask.query.get(task_id)
    if not task:
        return jsonify({'code': 404, 'message': '任务不存在', 'data': None})

    if task.status not in ('queued', 'processing'):
        return jsonify({'code': 400, 'message': '任务无法取消', 'data': None})

    # 通知任务执行器停止该任务
    task_executor.cancel_task(task_id)
    
    task.status = 'cancelled'
    task.completed_at = datetime.now()
    db.session.commit()

    log_operation(current_user.id, 'cancel_task', f'取消检测任务: {task_id}')

    return jsonify({'code': 200, 'message': '任务已取消', 'data': None})


@detect_bp.route('/tasks/cancel-all', methods=['POST'])
@login_required
def cancel_all_tasks():
    """取消所有正在运行的任务"""
    from app import task_executor
    
    # 获取当前用户所有正在处理的任务
    tasks = DetectionTask.query.filter(
        DetectionTask.created_by == current_user.id,
        DetectionTask.status.in_(['queued', 'processing'])
    ).all()
    
    if not tasks:
        return jsonify({'code': 200, 'message': '没有正在运行的任务', 'data': None})
    
    # 通知任务执行器停止所有任务
    task_executor.cancel_all_tasks()
    
    # 更新任务状态
    for task in tasks:
        task.status = 'cancelled'
        task.completed_at = datetime.now()
    
    db.session.commit()
    
    log_operation(current_user.id, 'cancel_all_tasks', f'取消所有检测任务: {len(tasks)}个')

    return jsonify({'code': 200, 'message': f'已取消 {len(tasks)} 个任务', 'data': None})


@detect_bp.route('/tasks/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    """删除任务"""
    task = DetectionTask.query.get(task_id)
    if not task:
        return jsonify({'code': 404, 'message': '任务不存在', 'data': None})

    try:
        # 删除关联的检测结果
        DetectionResult.query.filter_by(task_id=task_id).delete(synchronize_session=False)
        
        # 删除任务
        db.session.delete(task)
        db.session.commit()

        log_operation(current_user.id, 'delete_task', f'删除检测任务: {task_id}')

        return jsonify({'code': 200, 'message': '任务已删除', 'data': None})
    except Exception as e:
        db.session.rollback()
        print(f"删除任务失败: {e}")
        return jsonify({'code': 500, 'message': f'删除失败: {str(e)}', 'data': None})


@detect_bp.route('/tasks/clear', methods=['DELETE'])
@login_required
def clear_tasks():
    """清空所有检测任务（包括所有状态）"""
    try:
        # 获取当前用户的所有任务
        user_tasks = DetectionTask.query.filter_by(created_by=current_user.id).all()
        task_ids = [t.id for t in user_tasks]
        
        if not task_ids:
            return jsonify({'code': 200, 'message': '没有任务需要清空', 'data': None})
        
        # 先将正在处理的任务状态改为 cancelled
        DetectionTask.query.filter(
            DetectionTask.created_by == current_user.id,
            DetectionTask.status.in_(['queued', 'processing'])
        ).update({'status': 'cancelled'}, synchronize_session=False)
        
        # 删除所有检测结果
        DetectionResult.query.filter(
            DetectionResult.task_id.in_(task_ids)
        ).delete(synchronize_session=False)
        
        # 删除所有任务
        DetectionTask.query.filter(
            DetectionTask.created_by == current_user.id
        ).delete(synchronize_session=False)
        
        db.session.commit()
        
        log_operation(current_user.id, 'clear_tasks', f'清空检测任务: {len(task_ids)}个')

        return jsonify({'code': 200, 'message': f'已清空{len(task_ids)}个任务', 'data': None})
    except Exception as e:
        db.session.rollback()
        print(f"清空任务失败: {e}")
        return jsonify({'code': 500, 'message': f'清空失败: {str(e)}', 'data': None})


@detect_bp.route('/tasks/<int:task_id>/results', methods=['GET'])
@login_required
def get_task_results(task_id):
    """获取任务检测结果"""
    task = DetectionTask.query.get(task_id)
    if not task:
        return jsonify({'code': 404, 'message': '任务不存在', 'data': None})

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 100, type=int)

    pagination = DetectionResult.query.filter_by(task_id=task_id).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'items': [r.to_dict() for r in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }
    })


@detect_bp.route('/tasks/<int:task_id>/export', methods=['GET'])
@login_required
def export_task_results(task_id):
    """导出任务结果"""
    task = DetectionTask.query.get(task_id)
    if not task:
        return jsonify({'code': 404, 'message': '任务不存在', 'data': None})

    results = DetectionResult.query.filter_by(task_id=task_id).all()
    export_format = request.args.get('format', 'json')

    if export_format == 'json':
        import json
        data = [r.to_dict() for r in results]
        return jsonify({'code': 200, 'message': 'success', 'data': data})

    elif export_format == 'csv':
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['ID', 'Task ID', 'Frame', 'Class ID', 'Class Name',
                        'Confidence', 'X', 'Y', 'W', 'H'])

        for r in results:
            writer.writerow([
                r.id, r.task_id, r.frame_index, r.class_id, r.class_name,
                r.confidence, r.bbox_x, r.bbox_y, r.bbox_w, r.bbox_h
            ])

        from flask import make_response
        response = make_response(output.getvalue())
        response.headers['Content-Type'] = 'text/csv'
        response.headers['Content-Disposition'] = f'attachment; filename=task_{task_id}_results.csv'
        return response

    return jsonify({'code': 400, 'message': '不支持的导出格式', 'data': None})


@detect_bp.route('/quick', methods=['POST'])
@login_required
def quick_detect():
    """快速检测（单张图片）"""
    if 'file' not in request.files:
        return jsonify({'code': 400, 'message': '没有选择文件', 'data': None})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'code': 400, 'message': '没有选择文件', 'data': None})

    allowed = current_app.config['ALLOWED_IMAGE_EXTENSIONS']
    if not allowed_file(file.filename, allowed):
        return jsonify({'code': 400, 'message': '不支持的文件格式', 'data': None})

    # 保存临时文件
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    file.save(filepath)

    # 获取检测参数
    confidence = float(request.form.get('confidence', 0.5))
    iou_threshold = float(request.form.get('iou_threshold', 0.45))

    # 执行检测
    engine = DetectorEngine(current_app.config['MODEL_PATH'])
    result = engine.detect_image(filepath, {
        'confidence': confidence,
        'iou_threshold': iou_threshold
    })

    if result['success']:
        # 保存结果图片
        import cv2
        result_filename = f"result_{filename}"
        result_path = os.path.join(current_app.config['OUTPUT_FOLDER'], result_filename)
        os.makedirs(os.path.dirname(result_path), exist_ok=True)
        cv2.imwrite(result_path, result['result_image'])

        # 创建任务记录
        task = DetectionTask(
            task_type='image',
            source_type='upload',
            scene_id=request.form.get('scene_id'),
            params={'confidence': confidence, 'iou_threshold': iou_threshold},
            status='completed',
            progress=100,
            result_summary={'count': len(result['detections'])},
            result_path=result_path,
            created_by=current_user.id,
            started_at=datetime.now(),
            completed_at=datetime.now()
        )
        db.session.add(task)
        db.session.flush()

        # 保存检测结果
        for det in result['detections']:
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

        db.session.commit()

        # 检查告警规则
        scene_id = request.form.get('scene_id')
        if scene_id:
            rules = AlertRule.query.filter_by(scene_id=scene_id, is_enabled=1).all()
            rule_engine = RuleEngine()
            alert_manager = AlertManager()

            triggered = rule_engine.evaluate_rules(rules, result['detections'])
            for item in triggered:
                alert_manager.create_alert(
                    item['rule'], task.id, None,
                    item['result']['message'], item['result']['details']
                )

        return jsonify({
            'code': 200,
            'message': '检测完成',
            'data': {
                'task_id': task.id,
                'detections': result['detections'],
                'result_url': f'/api/v1/detect/result/{result_filename}'
            }
        })
    else:
        return jsonify({'code': 500, 'message': result.get('error', '检测失败'), 'data': None})


@detect_bp.route('/result/<filename>')
def get_result_image(filename):
    """获取结果文件（图片或视频）"""
    result_path = os.path.join(current_app.config['OUTPUT_FOLDER'], filename)
    if os.path.exists(result_path):
        # 根据文件扩展名设置正确的 mimetype
        ext = filename.rsplit('.', 1)[-1].lower()
        if ext in ['mp4', 'avi', 'mov', 'mkv']:
            return send_file(result_path, mimetype='video/mp4')
        return send_file(result_path)
    return jsonify({'code': 404, 'message': '文件不存在', 'data': None}), 404


@detect_bp.route('/uploads', methods=['GET'])
@login_required
def get_uploads():
    """获取上传记录"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    file_type = request.args.get('file_type')

    query = UploadRecord.query.filter_by(user_id=current_user.id)

    if file_type:
        query = query.filter_by(file_type=file_type)

    pagination = query.order_by(UploadRecord.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'items': [u.to_dict() for u in pagination.items],
            'total': pagination.total,
            'pages': pagination.pages,
            'current_page': page
        }
    })


@detect_bp.route('/uploads/clear', methods=['DELETE'])
@login_required
def clear_uploads():
    """清空上传记录"""
    try:
        # 只删除当前用户的上传记录
        deleted = UploadRecord.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
        
        log_operation(current_user.id, 'clear_uploads', f'清空上传记录: {deleted}条')
        
        return jsonify({'code': 200, 'message': f'已清空{deleted}条记录', 'data': None})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': f'清空失败: {str(e)}', 'data': None})
