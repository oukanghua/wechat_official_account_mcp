# Python 安装指南 (Windows)

## 方法 1: 使用 winget（推荐，最简单）

### 步骤 1: 检查 winget 是否可用

```powershell
winget --version
```

如果已安装，继续步骤 2。如果未安装，使用方法 2 或 3。

### 步骤 2: 安装 Python

```powershell
# 搜索 Python
winget search Python.Python

# 安装 Python 3.12（推荐）
winget install Python.Python.3.12

# 或安装最新版本
winget install Python.Python.3
```

### 步骤 3: 验证安装

安装完成后，**重启 PowerShell** 或打开新的终端：

```powershell
python --version
pip --version
```

## 方法 2: 使用 Microsoft Store

### 步骤 1: 打开 Microsoft Store

在开始菜单搜索 "Microsoft Store" 并打开

### 步骤 2: 搜索 Python

在 Store 中搜索 "Python 3.12" 或 "Python 3.11"

### 步骤 3: 安装

点击 "获取" 或 "安装" 按钮

### 步骤 4: 验证

安装完成后，打开新的 PowerShell：

```powershell
python --version
```

## 方法 3: 从官网下载（推荐用于开发）

### 步骤 1: 下载 Python

访问：https://www.python.org/downloads/

下载 Python 3.12 或 3.11（推荐 3.12）

### 步骤 2: 安装

1. 运行下载的安装程序
2. **重要**：勾选 "Add Python to PATH"
3. 选择 "Install Now" 或 "Customize installation"
4. 如果选择自定义安装，确保勾选 "pip" 和 "Add Python to environment variables"

### 步骤 3: 验证

打开新的 PowerShell：

```powershell
python --version
pip --version
```

## 安装后配置

### 1. 验证安装

```powershell
# 检查 Python 版本
python --version

# 检查 pip 版本
pip --version

# 检查 Python 路径
python -c "import sys; print(sys.executable)"
```

### 2. 升级 pip

```powershell
python -m pip install --upgrade pip
```

### 3. 安装项目依赖

```powershell
# 进入项目目录
cd C:\Users\maluw\Code\MCP\wechat_official_account_mcp

# 安装依赖
pip install -r requirements.txt
```

### 4. 验证 MCP 依赖

```powershell
python -c "import mcp; print('MCP installed')"
python -c "import flask; print('Flask installed')"
python -c "import requests; print('Requests installed')"
```

## 常见问题

### 问题 1: python 命令不可用

**原因**: Python 未添加到 PATH

**解决**:
1. 重新安装 Python，确保勾选 "Add Python to PATH"
2. 或手动添加到 PATH：
   - 找到 Python 安装路径（通常在 `C:\Users\用户名\AppData\Local\Programs\Python\Python312\`）
   - 添加到系统环境变量 PATH

### 问题 2: 多个 Python 版本

**检查所有 Python 版本**:

```powershell
Get-Command python* | Select-Object Name, Source
```

**使用特定版本**:

```powershell
# 使用 python3
python3 --version

# 或使用 py launcher
py --version
py -3.12 --version
```

### 问题 3: pip 命令不可用

**解决**:

```powershell
python -m pip --version
python -m pip install --upgrade pip
```

## 推荐配置

安装 Python 3.12（当前最新稳定版），因为项目要求 Python 3.12。

安装完成后，运行：

```powershell
# 1. 验证安装
python --version

# 2. 安装依赖
pip install -r requirements.txt

# 3. 测试 MCP 服务器
python main.py
```

## 下一步

安装 Python 后：
1. 安装项目依赖：`pip install -r requirements.txt`
2. 更新 MCP 配置使用正确的 Python 路径
3. 重启 Claude Desktop
4. 测试 MCP 工具


