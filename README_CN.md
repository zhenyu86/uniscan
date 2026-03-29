# UniScan - 智能目标检测平台

![Python](https://img.shields.io/badge/Python-3.8+-green)
![Flask](https://img.shields.io/badge/Flask-2.3-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

UniScan 是一个基于深度学习的智能目标检测平台，支持图片/视频检测、多用户协作、告警管理等功能。

---

## 目录

- [快速开始](#快速开始)
- [环境配置](#环境配置)
- [数据库配置](#数据库配置)
- [项目结构](#项目结构)
- [配置文件说明](#配置文件说明)
- [如何替换检测模型](#如何替换检测模型)
- [API 接口](#api-接口)
- [常见问题](#常见问题)

---

## 快速开始

### 1. 环境要求

- Python 3.8+
- MySQL 5.7+ 或 MySQL 8.0+
- (可选) NVIDIA GPU + CUDA (用于加速推理)

### 2. 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 如需 GPU 加速，安装 onnxruntime-gpu 版本
pip install onnxruntime-gpu
```

### 3. 配置数据库

编辑 `config.py` 文件，修改数据库连接信息：

```python
MYSQL_HOST = 'localhost'      # MySQL 主机地址
MYSQL_PORT = 3306             # MySQL 端口
MYSQL_USER = 'root'           # MySQL 用户名
MYSQL_PASSWORD = '123456'     # MySQL 密码
MYSQL_DATABASE = 'uniscan'    # 数据库名称
```

或使用环境变量：

```bash
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=123456
export MYSQL_DATABASE=uniscan
```

### 4. 准备模型文件

将您的 ONNX 模型文件放置在 `weights/` 目录：

```
uniscan/
└── weights/
    └── best.onnx    # 默认模型文件名
```

### 5. 启动应用

```bash
python app.py
```

**首次启动会自动：**
- 创建数据库（如果不存在）
- 创建所有数据表
- 初始化默认数据和用户

### 6. 访问系统

打开浏览器访问 http://localhost:5000

| 用户名 | 密码 | 角色 |
|--------|------|------|
| admin | admin123 | 管理员 |
| user | user123 | 普通用户 |

---

## 环境配置

### 依赖包说明

| 包名 | 版本 | 用途 |
|------|------|------|
| Flask | 2.3.3 | Web 框架 |
| Flask-SQLAlchemy | 3.1.1 | ORM |
| Flask-Migrate | 4.0.5 | 数据库迁移 |
| Flask-Login | 0.6.3 | 用户认证 |
| PyMySQL | 1.1.0 | MySQL 驱动 |
| opencv-python | 4.8.1.78 | 图像处理 |
| numpy | 1.24.3 | 数值计算 |
| onnxruntime | 1.16.1 | ONNX 推理 |

### GPU 配置 (可选)

如需使用 GPU 加速：

1. 安装 CUDA Toolkit (推荐 11.x 或 12.x)
2. 安装 cuDNN
3. 安装 onnxruntime-gpu：

```bash
pip uninstall onnxruntime
pip install onnxruntime-gpu
```

系统会自动检测 GPU 并使用 CUDA 进行推理。

---

## 数据库配置

### 自动配置 (推荐)

首次启动时，系统会自动：
1. 创建数据库
2. 创建所有数据表
3. 初始化默认数据

### 手动配置

如果自动配置失败，可以手动创建：

```sql
-- 1. 创建数据库
CREATE DATABASE uniscan CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 2. 创建用户 (可选)
CREATE USER 'uniscan'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON uniscan.* TO 'uniscan'@'localhost';
FLUSH PRIVILEGES;
```

### 数据库表结构

| 表名 | 说明 |
|------|------|
| `users` | 用户账户 |
| `operation_logs` | 操作日志 |
| `detection_tasks` | 检测任务 |
| `detection_results` | 检测结果 |
| `upload_records` | 上传记录 |
| `alerts` | 告警记录 |
| `alert_rules` | 告警规则 |
| `scenes` | 检测场景 |
| `scene_templates` | 场景模板 |
| `system_configs` | 系统配置 |
| `model_versions` | 模型版本 |

---

## 项目结构

```
uniscan/
├── app.py                    # 主程序入口
├── config.py                 # 应用配置文件
├── detector_config.py        # 检测器配置文件
├── requirements.txt          # 依赖列表
│
├── detectors/                # 检测器模块 (可替换)
│   ├── __init__.py           # 模块初始化
│   ├── base_detector.py      # 检测器抽象基类
│   ├── onnx_detector.py      # ONNX 检测器实现
│   └── factory.py            # 检测器工厂
│
├── api/                      # API 接口
│   ├── auth.py               # 认证接口
│   ├── detect.py             # 检测接口
│   ├── alerts.py             # 告警接口
│   ├── analytics.py          # 分析接口
│   ├── scenes.py             # 场景接口
│   ├── rules.py              # 规则接口
│   └── settings.py           # 设置接口
│
├── models/                   # 数据库模型
│   ├── user.py               # 用户模型
│   ├── task.py               # 任务模型
│   ├── device.py             # 设备模型
│   ├── alert.py              # 告警模型
│   ├── scene.py              # 场景模型
│   ├── rule.py               # 规则模型
│   └── config.py             # 配置模型
│
├── utils/                    # 工具模块
│   ├── auth.py               # 认证工具
│   ├── detector_engine.py    # 检测引擎 (兼容层)
│   ├── task_executor.py      # 任务执行器
│   ├── analytics.py          # 分析引擎
│   ├── alert_manager.py      # 告警管理
│   └── rule_engine.py        # 规则引擎
│
├── templates/                # 页面模板
├── static/                   # 静态资源
├── weights/                  # 模型文件目录
├── uploads/                  # 上传文件目录
└── outputs/                  # 输出文件目录
```

---

## 配置文件说明

### 1. config.py - 应用配置

主要的应用配置文件，包含：

- 数据库连接配置
- 文件存储配置
- 用户认证配置
- 默认用户账户
- 场景模板

### 2. detector_config.py - 检测器配置

专门用于目标检测的配置文件，包含：

```python
# 检测器类型: 'onnx', 'pytorch', 'tensorflow'
MODEL_TYPE = 'onnx'

# 模型文件路径
MODEL_PATH = 'weights/best.onnx'

# 模型输入尺寸 (宽度, 高度)
INPUT_SIZE = (640, 640)

# 置信度阈值 (0.0-1.0)
CONFIDENCE_THRESHOLD = 0.5

# IOU 阈值 (用于NMS)
IOU_THRESHOLD = 0.45

# 推理设备: 'cuda' 或 'cpu'
DEVICE = 'cuda'

# 类别标签列表
CLASS_LABELS = ['person', 'car', 'dog', ...]

# 视频抽帧步长
DEFAULT_FRAME_STEP = 10
```

---

## 如何替换检测模型

### 方法一：使用 ONNX 模型 (推荐)

1. **准备模型文件**
   - 将您的模型转换为 ONNX 格式
   - 放置在 `weights/` 目录

2. **修改 detector_config.py**
   ```python
   # 修改模型路径
   MODEL_PATH = 'weights/your_model.onnx'
   
   # 修改类别标签
   CLASS_LABELS = ['class1', 'class2', 'class3', ...]
   
   # 修改输入尺寸 (如果需要)
   INPUT_SIZE = (640, 640)
   ```

3. **重启应用**

### 方法二：使用其他框架模型

如果要使用 PyTorch、TensorFlow 等其他框架：

1. **创建新的检测器类**

   ```python
   # detectors/pytorch_detector.py
   from detectors.base_detector import BaseDetector, DetectionResult
   
   class PyTorchDetector(BaseDetector):
       def __init__(self, model_path, **kwargs):
           super().__init__(model_path, **kwargs)
           self.load_model()
       
       def load_model(self):
           import torch
           self.model = torch.load(self.model_path)
           self.model.eval()
       
       def preprocess(self, image):
           # 实现图像预处理
           pass
       
       def postprocess(self, raw_output, **kwargs):
           # 实现输出后处理
           pass
       
       def detect(self, image, **kwargs):
           # 实现检测逻辑
           pass
       
       def detect_and_draw(self, image, **kwargs):
           # 实现检测并绘制
           pass
   ```

2. **注册检测器**

   ```python
   # detectors/__init__.py
   from detectors.pytorch_detector import PyTorchDetector
   DetectorFactory.register('pytorch')(PyTorchDetector)
   ```

3. **修改配置**
   ```python
   # detector_config.py
   MODEL_TYPE = 'pytorch'
   MODEL_PATH = 'weights/model.pth'
   ```

### 输入输出数据格式

#### 输入图像格式
- **类型**: numpy.ndarray
- **形状**: (H, W, 3)
- **格式**: BGR (Blue-Green-Red)
- **数据类型**: uint8 (0-255)

#### 检测结果格式
```python
[
    {
        'class_id': 0,           # 类别ID
        'class_name': 'person',  # 类别名称
        'confidence': 0.95,      # 置信度 (0.0-1.0)
        'bbox': {
            'x': 100,            # 左上角x坐标
            'y': 50,             # 左上角y坐标
            'w': 200,            # 宽度
            'h': 300             # 高度
        }
    },
    ...
]
```

#### 模型输入张量格式
- **类型**: numpy.ndarray
- **形状**: (1, 3, H, W)
- **数据类型**: float32
- **值范围**: [0, 1] (归一化后的RGB图像)

#### 模型输出格式 (YOLO)
- **类型**: numpy.ndarray
- **形状**: (1, 4+num_classes, 8400)
- **前4个值**: (center_x, center_y, width, height)
- **后续值**: 各类别概率

---

## API 接口

### 认证接口 `/api/v1/auth`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /login | 用户登录 |
| POST | /logout | 用户登出 |
| GET | /info | 获取用户信息 |

### 检测接口 `/api/v1/detect`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /upload/image | 上传图片 |
| POST | /upload/video | 上传视频 |
| POST | /task | 创建检测任务 |
| GET | /tasks | 获取任务列表 |
| GET | /tasks/:id | 获取任务详情 |
| DELETE | /tasks/:id | 删除任务 |
| POST | /quick | 快速检测 |

### 告警接口 `/api/v1/alerts`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | / | 获取告警列表 |
| POST | /:id/handle | 处理告警 |

### 分析接口 `/api/v1/analytics`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /dashboard | 获取仪表盘数据 |
| GET | /detection-trend | 获取检测趋势 |
| GET | /class-distribution | 获取类别分布 |
| GET | /alert-trend | 获取告警趋势 |

### 设置接口 `/api/v1/settings`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | /configs | 获取配置 |
| PUT | /configs | 更新配置 |
| GET | /users | 获取用户列表 |
| POST | /users | 创建用户 |

---

## 常见问题

### Q: 数据库连接失败？

A: 检查以下几点：
1. MySQL 服务是否启动
2. `config.py` 中的连接信息是否正确
3. 用户是否有创建数据库的权限

### Q: 检测任务一直排队？

A: 检查以下几点：
1. `weights/best.onnx` 模型文件是否存在
2. 模型格式是否正确 (ONNX)
3. 查看控制台是否有错误信息

### Q: 如何重置管理员密码？

A: 两种方法：
1. 删除数据库并重启应用
2. 运行 `python app.py reset`

### Q: 如何启用 GPU 加速？

A: 
1. 安装 CUDA Toolkit 和 cuDNN
2. 安装 `onnxruntime-gpu`: `pip install onnxruntime-gpu`
3. 系统会自动检测并使用 GPU

### Q: 如何修改检测参数？

A: 编辑 `detector_config.py`：
```python
CONFIDENCE_THRESHOLD = 0.5  # 置信度阈值
IOU_THRESHOLD = 0.45        # IOU阈值
DEFAULT_FRAME_STEP = 10     # 视频抽帧步长
```

### Q: 支持哪些模型格式？

A: 目前支持：
- **ONNX**: 推荐格式，支持 YOLOv5/v8 等
- 可扩展支持: PyTorch (.pth), TensorFlow (.pb), 等

---

## 许可证

MIT License
