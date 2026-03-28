# -*- coding: utf-8 -*-
"""
UniScan 统一配置文件
所有配置参数集中管理，方便修改
"""

import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    """基础配置"""

    # ==================== 应用配置 ====================
    SECRET_KEY = os.environ.get('SECRET_KEY', 'uniscan-secret-key-2024-change-in-production')
    DEBUG = os.environ.get('FLASK_DEBUG', 'true').lower() == 'true'

    # ==================== 数据库配置 ====================
    MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT', 3306))
    MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '123456')
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE', 'uniscan')

    # SQLAlchemy 配置
    SQLALCHEMY_DATABASE_URI = (
        f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@'
        f'{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'max_overflow': 20
    }

    # ==================== 文件存储配置 ====================
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    OUTPUT_FOLDER = os.path.join(basedir, 'outputs')
    MAX_CONTENT_LENGTH = 500 * 1024 * 1024  # 最大上传大小: 500MB

    # 允许的文件类型
    ALLOWED_IMAGE_EXTENSIONS = {'jpg', 'jpeg', 'png', 'bmp', 'tiff'}
    ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'flv'}

    # ==================== 检测模型配置 ====================
    MODEL_PATH = os.path.join(basedir, 'weights', 'best.onnx')

    # 默认检测参数
    DEFAULT_CONFIDENCE = 0.5       # 默认置信度阈值
    DEFAULT_IOU_THRESHOLD = 0.45   # 默认IOU阈值
    DEFAULT_FRAME_STEP = 10        # 视频抽帧步长

    # ==================== 任务队列配置 ====================
    MAX_WORKERS = 4                # 最大并行任务数
    TASK_QUEUE_SIZE = 100          # 任务队列容量

    # ==================== 用户认证配置 ====================
    SESSION_PROTECTION = 'basic'
    REMEMBER_COOKIE_DURATION = 86400  # 24小时

    # ==================== 默认用户账户 ====================
    DEFAULT_USERS = [
        {'username': 'admin', 'password': 'admin123', 'role': 'admin', 'name': '系统管理员'},
        {'username': 'operator', 'password': 'operator123', 'role': 'operator', 'name': '操作员'},
        {'username': 'viewer', 'password': 'viewer123', 'role': 'viewer', 'name': '查看者'}
    ]

    # ==================== COCO 80类标签 ====================
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

    # ==================== 场景模板 ====================
    SCENE_TEMPLATES = [
        {
            'name': '智慧交通',
            'category': '交通',
            'description': '适用于道路监控、车辆检测、交通流量分析等场景',
            'config': {
                'icon': 'bi-car-front',
                'theme_color': '#1890ff',
                'focus_classes': ['car', 'truck', 'bus', 'motorcycle', 'bicycle', 'person'],
                'class_mapping': {
                    'car': '小汽车', 'truck': '卡车', 'bus': '公交车',
                    'motorcycle': '摩托车', 'bicycle': '自行车', 'person': '行人'
                }
            }
        },
        {
            'name': '智慧安防',
            'category': '安防',
            'description': '适用于视频监控、人员检测、异常行为分析等场景',
            'config': {
                'icon': 'bi-shield-check',
                'theme_color': '#52c41a',
                'focus_classes': ['person', 'car', 'backpack', 'suitcase', 'knife'],
                'class_mapping': {
                    'person': '人员', 'car': '车辆', 'backpack': '背包',
                    'suitcase': '行李箱', 'knife': '刀具'
                }
            }
        },
        {
            'name': '工业质检',
            'category': '工业',
            'description': '适用于产品缺陷检测、质量控制等场景',
            'config': {'icon': 'bi-gear', 'theme_color': '#722ed1', 'focus_classes': [], 'class_mapping': {}}
        },
        {
            'name': '智慧零售',
            'category': '零售',
            'description': '适用于客流分析、商品识别、货架监控等场景',
            'config': {
                'icon': 'bi-shop',
                'theme_color': '#fa8c16',
                'focus_classes': ['person', 'bottle', 'cup', 'chair'],
                'class_mapping': {'person': '顾客', 'bottle': '瓶装商品', 'cup': '杯装商品', 'chair': '座椅'}
            }
        },
        {
            'name': '智慧农业',
            'category': '农业',
            'description': '适用于农作物监测、病虫害识别、牲畜管理等场景',
            'config': {
                'icon': 'bi-tree',
                'theme_color': '#13c2c2',
                'focus_classes': ['cow', 'sheep', 'horse', 'bird'],
                'class_mapping': {'cow': '牛', 'sheep': '羊', 'horse': '马', 'bird': '鸟'}
            }
        },
        {
            'name': '医疗影像',
            'category': '医疗',
            'description': '适用于医学图像分析、病灶检测等场景',
            'config': {'icon': 'bi-hospital', 'theme_color': '#eb2f96', 'focus_classes': [], 'class_mapping': {}}
        }
    ]

    # ==================== 系统默认配置项 ====================
    DEFAULT_CONFIGS = [
        {'key': 'system_name', 'value': 'UniScan智能检测平台', 'type': 'string', 'desc': '系统名称'},
        {'key': 'detection_confidence', 'value': '0.5', 'type': 'float', 'desc': '默认置信度阈值'},
        {'key': 'detection_iou', 'value': '0.45', 'type': 'float', 'desc': '默认IOU阈值'},
        {'key': 'frame_step', 'value': '10', 'type': 'int', 'desc': '视频抽帧步长'},
        {'key': 'auto_refresh_interval', 'value': '5', 'type': 'int', 'desc': '自动刷新间隔(秒)'},
        {'key': 'theme_color', 'value': '#2D5BFF', 'type': 'string', 'desc': '主题颜色'},
    ]


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
