# UniScan - 智能目标检测平台

![Python](https://img.shields.io/badge/Python-3.8+-green)
![Flask](https://img.shields.io/badge/Flask-2.3-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

基于 目标检测 的平台，支持图片/视频检测/rstp流、多用户协作、告警管理。

---

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置数据库

编辑 `config.py`，修改数据库连接信息：

```python
MYSQL_HOST = 'localhost'      # MySQL 主机
MYSQL_PORT = 3306             # MySQL 端口
MYSQL_USER = 'root'           # MySQL 用户
MYSQL_PASSWORD = '123456'     # MySQL 密码
MYSQL_DATABASE = 'uniscan'    # 数据库名称
```

### 3. 启动应用

```bash
python app.py
```

**首次启动会自动：**
- 创建数据库（如不存在）
- 创建所有数据表
- 初始化默认数据和用户

### 4. 访问系统

打开浏览器访问 http://localhost:5000

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |
| operator | operator123 | 操作员 |
| viewer | viewer123 | 查看者 |

---

## 项目结构

```
detection_platform/
├── app.py                 # 主程序（自动初始化数据库）
├── config.py              # 统一配置文件
├── requirements.txt       # 依赖列表
├── api/                   # API 接口
│   ├── auth.py            # 认证接口
│   ├── detect.py          # 检测接口
│   ├── alerts.py          # 告警接口
│   ├── analytics.py       # 统计接口
│   ├── scenes.py          # 场景接口
│   ├── rules.py           # 规则接口
│   └── settings.py        # 设置接口
├── models/                # 数据库模型
│   ├── user.py            # 用户模型
│   ├── task.py            # 任务模型
│   ├── device.py          # 设备模型
│   ├── alert.py           # 告警模型
│   ├── scene.py           # 场景模型
│   ├── rule.py            # 规则模型
│   └── config.py          # 配置模型
├── utils/                 # 工具模块
│   ├── auth.py            # 认证工具
│   ├── detector_engine.py # 检测引擎
│   ├── task_executor.py   # 任务执行器
│   └── ...                # 其他工具
├── templates/             # 页面模板
├── static/                # 静态资源
├── weights/               # 模型文件
├── uploads/               # 上传目录
└── outputs/               # 输出目录
```

---

## 配置说明

所有配置集中在 `config.py` 文件中：

### 数据库配置
```python
MYSQL_HOST = 'localhost'      # 主机地址
MYSQL_PORT = 3306             # 端口
MYSQL_USER = 'root'           # 用户名
MYSQL_PASSWORD = '123456'     # 密码
MYSQL_DATABASE = 'uniscan'    # 数据库名
```

### 检测参数配置
```python
MODEL_PATH = 'weights/best.onnx'  # 模型路径
DEFAULT_CONFIDENCE = 0.5          # 默认置信度
DEFAULT_IOU_THRESHOLD = 0.45      # 默认IOU阈值
DEFAULT_FRAME_STEP = 10           # 视频抽帧步长
```

### 文件存储配置
```python
UPLOAD_FOLDER = 'uploads/'        # 上传目录
OUTPUT_FOLDER = 'outputs/'        # 输出目录
MAX_CONTENT_LENGTH = 500MB        # 最大上传大小
```

### 任务队列配置
```python
MAX_WORKERS = 4                   # 最大并行任务数
TASK_QUEUE_SIZE = 100             # 队列容量
```

---

## 数据库表结构

| 表名 | 说明 |
|------|------|
| `users` | 用户表 |
| `operation_logs` | 操作日志表 |
| `detection_tasks` | 检测任务表 |
| `detection_results` | 检测结果表 |
| `upload_records` | 上传记录表 |
| `alerts` | 告警记录表 |
| `alert_rules` | 告警规则表 |
| `scenes` | 场景表 |
| `scene_templates` | 场景模板表 |
| `system_configs` | 系统配置表 |
| `model_versions` | 模型版本表 |
| `traffic_stats` | 流量统计表 |
| `dashboard_configs` | 看板配置表 |

---

## API 接口

### 认证 `/api/v1/auth`
- `POST /login` - 登录
- `POST /logout` - 登出
- `GET /info` - 获取用户信息

### 检测 `/api/v1/detect`
- `POST /upload/image` - 上传图片
- `POST /upload/video` - 上传视频
- `POST /task` - 创建检测任务
- `GET /tasks` - 获取任务列表
- `DELETE /tasks/:id` - 删除任务
- `DELETE /tasks/clear` - 清空所有任务

### 设置 `/api/v1/settings`
- `GET /configs` - 获取配置
- `PUT /configs` - 更新配置
- `GET /users` - 获取用户列表
- `POST /users` - 创建用户

---

## 常见问题

### Q: 数据库连接失败？
A: 检查 MySQL 服务是否启动，以及 `config.py` 中的连接信息是否正确。

### Q: 检测任务一直排队？
A: 检查 `weights/best.onnx` 模型文件是否存在。

### Q: 如何重置管理员密码？
A: 删除数据库重新启动应用，或直接修改数据库 users 表。

### Q: 如何更换检测模型？
A: 将新模型放入 `weights/` 目录，在系统设置中激活新模型。

---

## License

MIT License
