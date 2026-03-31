# Keyboard Trainer 键盘练习工具

一个基于 Python GUI 的键盘练习桌面应用工具，帮助用户通过基础测试、针对性训练和进阶测试三个模块来提升打字技能。

## 功能特性

- **基础打字测试**: 随机生成测试文本，测量打字速度和准确率
- **针对性训练**: 根据测试结果识别薄弱按键，生成针对性训练内容
- **进阶测试**: 支持导入自定义文章进行测试
- **虚拟键盘**: 实时显示按键高亮和手指位置指南
- **熟练度报告**: 详细的统计数据和改进建议
- **进步追踪**: 对比历史测试结果，展示进步情况

## 系统要求

- Python 3.8+
- PyQt5
- SQLite3（Python 内置）

## 快速启动

### macOS

**一键启动（推荐）：**
```bash
./start.sh
```

**手动运行：**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
keyboard-trainer
```

### Windows

**一键启动（推荐）：**
```powershell
.\start.bat
```

**手动运行（PowerShell）：**
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -e .
keyboard-trainer
```

**手动运行（CMD）：**
```cmd
python -m venv .venv
.venv\Scripts\activate.bat
pip install -e .
keyboard-trainer
```

### Linux

**一键启动（推荐）：**
```bash
./start.sh
```

**手动运行：**
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
keyboard-trainer
```

> **注意**: Linux 系统可能需要先安装 PyQt5 系统依赖：
> ```bash
> # Ubuntu/Debian
> sudo apt install python3-pyqt5
> 
> # Fedora
> sudo dnf install python3-qt5
> 
> # Arch
> sudo pacman -S python-pyqt5
> ```

## 使用说明

### 基础打字测试

1. 点击主菜单的"基础打字测试"按钮
2. 点击"开始测试"开始计时
3. 按照屏幕显示的文本输入
4. 完成后查看熟练度报告

### 针对性训练

1. 完成基础测试后，系统会识别薄弱按键
2. 点击"针对性训练"进入训练模式
3. 训练内容会包含更多薄弱按键
4. 持续练习直到按键准确率提升

### 进阶测试

1. 点击"进阶测试（自定义文章）"
2. 选择一个 TXT 格式的文本文件（至少 50000 字符）
3. 完成测试后查看与基础测试的对比报告

## 项目结构

```
keyboard_trainer/
├── __init__.py          # 包初始化
├── main.py              # 应用入口
├── models.py            # 数据模型
├── data_store.py        # 数据持久化
├── key_analyzer.py      # 按键分析
├── content_generator.py # 内容生成
├── file_handler.py      # 文件处理
├── report_generator.py  # 报告生成
├── test_controller.py   # 测试控制
├── training_controller.py # 训练控制
├── logger.py            # 日志系统
├── error_handler.py     # 错误处理
└── ui/
    ├── __init__.py
    ├── main_window.py   # 主窗口
    ├── test_view.py     # 测试视图
    ├── training_view.py # 训练视图
    ├── report_view.py   # 报告视图
    └── virtual_keyboard.py # 虚拟键盘
```

## 开发

### 运行测试

```bash
# 安装测试依赖
pip install -e ".[dev]"

# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/
```

### 代码风格

项目使用 Python 标准代码风格，建议使用 black 和 flake8 进行格式化和检查。

## 许可证

MIT License
