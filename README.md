# UniScan - Intelligent Object Detection Platform

![Python](https://img.shields.io/badge/Python-3.8+-green)
![Flask](https://img.shields.io/badge/Flask-2.3-blue)
![License](https://img.shields.io/badge/License-MIT-yellow)

An intelligent object detection platform based on object detect, supporting image/video detection, multi-user collaboration, and alert management.
---

## Quick Start
### 1. Install Dependencies
```bash
pip install -r requirements.txt
```
### 2. Configure Database
Edit `config.py` to modify database connection:

```python
MYSQL_HOST = 'localhost'      # MySQL host
MYSQL_PORT = 3306             # MySQL port
MYSQL_USER = 'root'           # MySQL user
MYSQL_PASSWORD = '123456'     # MySQL password
MYSQL_DATABASE = 'uniscan'    # Database name
```
### 3. Start Application
```bash
python app.py
```
**First startup will automatically:**
- Create database (if not exists)
- Create all data tables
- Initialize default data and users
### 4. Access System
Open browser and visit http://localhost:5000

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Administrator |
| operator | operator123 | Operator |
| viewer | viewer123 | Viewer |
---

## Project Structure
```
detection_platform/
├── app.py                 # Main entry (auto database init)
├── config.py              # Unified configuration
├── requirements.txt       # Dependencies
├── api/                   # API endpoints
│   ├── auth.py            # Authentication
│   ├── detect.py          # Detection
│   ├── alerts.py          # Alerts
│   ├── analytics.py       # Analytics
│   ├── scenes.py          # Scenes
│   ├── rules.py           # Rules
│   └── settings.py        # Settings
├── models/                # Database models
│   ├── user.py            # User model
│   ├── task.py            # Task model
│   ├── device.py          # Device model
│   ├── alert.py           # Alert model
│   ├── scene.py           # Scene model
│   ├── rule.py            # Rule model
│   └── config.py          # Config model
├── utils/                 # Utilities
│   ├── auth.py            # Auth utilities
│   ├── detector_engine.py # Detection engine
│   ├── task_executor.py   # Task executor
│   └── ...                # Other utilities
├── templates/             # Page templates
├── static/                # Static assets
├── weights/               # Model files
├── uploads/               # Upload directory
└── outputs/               # Output directory
```
---
## Configuration

All configurations are centralized in `config.py`:

### Database Configuration
```python
MYSQL_HOST = 'localhost'      # Host address
MYSQL_PORT = 3306             # Port
MYSQL_USER = 'root'           # Username
MYSQL_PASSWORD = '123456'     # Password
MYSQL_DATABASE = 'uniscan'    # Database name
```

### Detection Parameters
```python
MODEL_PATH = 'weights/best.onnx'  # Model path
DEFAULT_CONFIDENCE = 0.5          # Default confidence
DEFAULT_IOU_THRESHOLD = 0.45      # Default IOU threshold
DEFAULT_FRAME_STEP = 10           # Video frame step
```
### File Storage
```python
UPLOAD_FOLDER = 'uploads/'        # Upload directory
OUTPUT_FOLDER = 'outputs/'        # Output directory
MAX_CONTENT_LENGTH = 500MB        # Max upload size
```
### Task Queue
```python
MAX_WORKERS = 4                   # Max parallel tasks
TASK_QUEUE_SIZE = 100             # Queue capacity
```
---
## Database Tables
| Table | Description |
|-------|-------------|
| `users` | User accounts |
| `operation_logs` | Operation logs |
| `detection_tasks` | Detection tasks |
| `detection_results` | Detection results |
| `upload_records` | Upload records |
| `alerts` | Alert records |
| `alert_rules` | Alert rules |
| `scenes` | Detection scenes |
| `scene_templates` | Scene templates |
| `system_configs` | System configurations |
| `model_versions` | Model versions |
| `traffic_stats` | Traffic statistics |
| `dashboard_configs` | Dashboard configurations |
---
## API Endpoints

### Authentication `/api/v1/auth`
- `POST /login` - User login
- `POST /logout` - User logout
- `GET /info` - Get user info

### Detection `/api/v1/detect`
- `POST /upload/image` - Upload image
- `POST /upload/video` - Upload video
- `POST /task` - Create detection task
- `GET /tasks` - Get task list
- `DELETE /tasks/:id` - Delete task
- `DELETE /tasks/clear` - Clear all tasks

### Settings `/api/v1/settings`
- `GET /configs` - Get configurations
- `PUT /configs` - Update configurations
- `GET /users` - Get user list
- `POST /users` - Create user

---

## FAQ

### Q: Database connection failed?
A: Check if MySQL service is running and connection info in `config.py` is correct.

### Q: Detection task keeps queuing?
A: Check if `weights/best.onnx` model file exists.

### Q: How to reset admin password?
A: Delete database and restart application, or directly modify users table in database.

### Q: How to change detection model?
A: Place new model in `weights/` directory and activate it in system settings.
---
## License
MIT License
