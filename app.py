# -*- coding: utf-8 -*-
"""
UniScan 智能目标检测平台 - 主程序入口
"""

import os
import sys
from datetime import datetime
from flask import Flask, render_template, jsonify, send_from_directory, redirect
from flask_cors import CORS
from flask_login import LoginManager, current_user
from flask_migrate import Migrate

from config import config
from models.user import db, User
from api import (auth_bp, devices_bp, detect_bp, alerts_bp,
                 analytics_bp, scenes_bp, rules_bp, settings_bp)
from utils.task_executor import TaskExecutor

# 全局变量
migrate = Migrate()
login_manager = LoginManager()
task_executor = TaskExecutor()


def create_database(app):
    """自动创建数据库（如果不存在）"""
    import pymysql

    try:
        conn = pymysql.connect(
            host=app.config['MYSQL_HOST'],
            port=app.config['MYSQL_PORT'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            charset='utf8mb4'
        )
        with conn.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{app.config['MYSQL_DATABASE']}` "
                f"DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        conn.close()
        print(f"[OK] 数据库 {app.config['MYSQL_DATABASE']} 已就绪")
        return True
    except Exception as e:
        print(f"[ERROR] 数据库创建失败: {e}")
        return False


def init_tables(app):
    """初始化数据库表"""
    with app.app_context():
        try:
            db.create_all()
            
            # 修改 users 表的 role 字段从 Enum 改为 VARCHAR
            try:
                from sqlalchemy import text
                with db.engine.connect() as conn:
                    conn.execute(text("ALTER TABLE users MODIFY COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user'"))
                    conn.commit()
                print("[OK] 已更新 users 表 role 字段类型")
            except Exception as e:
                print(f"[INFO] role 字段更新跳过: {e}")
            
            print("[OK] 数据库表已创建")
            return True
        except Exception as e:
            print(f"[ERROR] 表创建失败: {e}")
            return False


def init_default_data(app):
    """初始化默认数据"""
    from models.scene import Scene, SceneTemplate
    from models.config import SystemConfig, ModelVersion

    with app.app_context():
        try:
            # 更新旧角色到新角色
            try:
                User.query.filter(User.role.in_(['manager', 'operator', 'viewer'])).update(
                    {'role': 'user'}, synchronize_session=False
                )
                db.session.commit()
                print("[OK] 已更新旧角色数据")
            except Exception as e:
                db.session.rollback()
                print(f"[INFO] 角色更新跳过: {e}")
            
            # 确保默认用户存在（无论数据库是否已有数据）
            for user_cfg in app.config['DEFAULT_USERS']:
                existing_user = User.query.filter_by(username=user_cfg['username']).first()
                if not existing_user:
                    user = User(
                        username=user_cfg['username'],
                        email=f"{user_cfg['username']}@uniscan.com",
                        real_name=user_cfg['name'],
                        role=user_cfg['role'],
                        status=1,
                        created_at=datetime.now(),
                        updated_at=datetime.now()
                    )
                    user.set_password(user_cfg['password'])
                    db.session.add(user)
                    print(f"[OK] 创建用户: {user_cfg['username']}")
                else:
                    # 更新角色（如果需要）
                    if existing_user.role not in ['admin', 'user']:
                        existing_user.role = 'user'
                    # 确保密码正确（重置密码）
                    existing_user.set_password(user_cfg['password'])
                    print(f"[OK] 更新用户: {user_cfg['username']}")
            db.session.commit()
            print("[OK] 用户数据已就绪")

            # 检查其他数据是否需要初始化
            from models.scene import SceneTemplate
            if SceneTemplate.query.first():
                print("[INFO] 场景模板已存在，跳过")
            else:
                # 创建场景模板
                for tmpl in app.config['SCENE_TEMPLATES']:
                    template = SceneTemplate(
                        name=tmpl['name'],
                        category=tmpl['category'],
                        description=tmpl['description'],
                        config=tmpl['config'],
                        created_at=datetime.now()
                    )
                    db.session.add(template)
                print("[OK] 场景模板已创建")

            # 创建默认场景
            from models.scene import Scene
            if not Scene.query.first():
                default_scene = Scene(
                    name='通用检测',
                    description='默认场景，适用于一般目标检测任务',
                    icon='bi-grid-3x3-gap',
                    theme_color='#2D5BFF',
                    class_mapping={},
                    focus_classes=[],
                    config={'auto_detect': True},
                    is_default=1,
                    created_by=1,
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                db.session.add(default_scene)
                print("[OK] 默认场景已创建")

            # 创建系统配置
            from models.config import SystemConfig
            for cfg in app.config['DEFAULT_CONFIGS']:
                if not SystemConfig.query.filter_by(config_key=cfg['key']).first():
                    config_item = SystemConfig(
                        config_key=cfg['key'],
                        config_value=cfg['value'],
                        config_type=cfg['type'],
                        description=cfg['desc'],
                        updated_at=datetime.now()
                    )
                    db.session.add(config_item)
            print("[OK] 系统配置已就绪")

            # 创建默认模型版本
            from models.config import ModelVersion
            if not ModelVersion.query.first():
                model = ModelVersion(
                    version='v1.0.0',
                    model_path='weights/best.onnx',
                    class_names=app.config['CLASS_LABELS'],
                    input_size='640x640',
                    is_active=1,
                    created_at=datetime.now()
                )
                db.session.add(model)
                print("[OK] 模型版本已创建")

            db.session.commit()
            print("[OK] 所有数据初始化完成")
            return True

        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] 数据初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False


def create_app(config_name='default'):
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # 确保目录存在
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['OUTPUT_FOLDER'], exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('weights', exist_ok=True)

    # 初始化扩展
    db.init_app(app)
    migrate.init_app(app, db)
    CORS(app)

    # 初始化任务执行器
    task_executor.init_app(app)

    # 初始化登录管理
    login_manager.init_app(app)
    login_manager.login_view = 'login'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    @login_manager.unauthorized_handler
    def unauthorized():
        return jsonify({'code': 401, 'message': '请先登录', 'data': None}), 401

    # 注册蓝图
    app.register_blueprint(auth_bp)
    app.register_blueprint(devices_bp)
    app.register_blueprint(detect_bp)
    app.register_blueprint(alerts_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(scenes_bp)
    app.register_blueprint(rules_bp)
    app.register_blueprint(settings_bp)

    # 注册页面路由
    register_page_routes(app)

    return app


def register_page_routes(app):
    """注册页面路由"""

    def check_login():
        """检查是否已登录"""
        return current_user.is_authenticated

    @app.route('/')
    def index():
        if not check_login():
            return redirect('/login')
        return render_template('index.html')

    @app.route('/login')
    def login():
        if current_user.is_authenticated:
            return redirect('/')
        return render_template('login.html')

    @app.route('/upload')
    def upload_page():
        if not check_login():
            return redirect('/login')
        return render_template('upload.html')

    @app.route('/tasks')
    def tasks_page():
        if not check_login():
            return redirect('/login')
        return render_template('tasks.html')

    @app.route('/settings')
    def settings_page():
        if not check_login():
            return redirect('/login')
        return render_template('settings.html')

    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    @app.route('/outputs/<path:filename>')
    def output_file(filename):
        return send_from_directory(app.config['OUTPUT_FOLDER'], filename)


def auto_init_database(app):
    """自动初始化数据库"""
    print("\n" + "=" * 50)
    print("UniScan 智能检测平台 - 启动中...")
    print("=" * 50)

    print("\n[1/3] 检查数据库...")
    if not create_database(app):
        print("数据库创建失败，请检查MySQL配置")
        sys.exit(1)

    print("\n[2/3] 初始化表结构...")
    if not init_tables(app):
        print("表结构创建失败")
        sys.exit(1)

    print("\n[3/3] 初始化数据...")
    init_default_data(app)

    print("\n" + "=" * 50)
    print("初始化完成！")
    print("默认账户: admin / admin123")
    print("=" * 50 + "\n")


# 创建应用实例
app = create_app()

# 自动初始化数据库
with app.app_context():
    auto_init_database(app)

if __name__ == '__main__':
    # 支持命令行参数
    if len(sys.argv) > 1 and sys.argv[1] == 'reset':
        # 重置管理员密码
        with app.app_context():
            admin = User.query.filter_by(username='admin').first()
            if admin:
                admin.set_password('admin123')
                db.session.commit()
                print("管理员密码已重置为: admin123")
            else:
                print("管理员账户不存在")
    else:
        app.run(host='0.0.0.0', port=5000, debug=True)
