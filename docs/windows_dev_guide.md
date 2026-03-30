# Echo Mock System - Windows 开发指南 (无 WSL2)

本指南建议您根据自己的开发偏好及系统资源情况，在以下两种模式中二选一：

1.  **方案 A (推荐): 使用 VS Code Dev Containers** — 彻底屏蔽环境差异，一键搞定全部依赖（需 Docker 配合）。
2.  **方案 B (备选): Windows 原生手动搭建** — 无需 Docker/WSL2，直接在 Windows 系统上安装工具链与虚拟环境。

---

## 🚀 方案 A: 使用 Dev Containers (极大简化流程)

如果您已经在 Windows 上安装了 **Docker Desktop**，那么项目已经内置了全套的容器化开发配置。

### 为什么选择 Dev Containers?
*   **零配置**: 容器启动时会自动通过 `postCreateCommand` 安装所有 Python 依赖、初始化数据库并构建向量索引。
*   **完整性**: 容器内包含所有底层 C 库（FFmpeg 等），无需担心 Windows 路径或库缺失问题。
*   **GPU 直通**: 只要宿主机安装了 Nvidia 驱动，容器可直接调用 GPU。

### ⚠️ 关于 WSL2 的说明
在 Windows 上，Docker Desktop 通常使用 **WSL2** 作为其运行引擎。这意味着虽然您感官上是在 VS Code 中开发，但底层逻辑依然依赖于 WSL2。
*   如果您是出于“不想手动管理 WSL2 分发版”考虑，Dev Container 是最佳选择。
*   如果您是出于“系统不支持虚拟化/不能开启 WSL2”考虑，请跳过此方案，直接查看下方的 **方案 B**。

---

## 🛠 方案 B: Windows 原生手动搭建 (无 WSL2)

在开始之前，请确保您的 Windows 系统已安装以下基础工具：

1.  **Git for Windows**: [官方下载](https://git-scm.com/download/win)
    *   **重要配置**: 为了避免换行符冲突，请在安装后运行：
        ```powershell
        git config --global core.autocrlf true
        ```
2.  **Miniconda** (推荐) 或 Anaconda: [官方下载](https://docs.anaconda.com/free/miniconda/index.html)
    *   用于管理 Python 环境及底层 C 库（如 `ffmpeg`, `libsndfile`）。
3.  **Node.js (LTS 版本)**: [官方下载](https://nodejs.org/)
    *   建议版本 v18+。
4.  **pnpm**: 安装 Node.js 后运行：
    ```powershell
    npm install -g pnpm
    ```

---

## 2. 🌲 后端环境搭建 (Backend)

### 2.1 创建 Conda 虚拟环境

项目根目录下的 `backend/environment.yml` 已经配置好了 Windows 兼容的依赖项。

1.  打开 **Anaconda Prompt** 或 **PowerShell** (确保已初始化 conda)。
2.  进入项目后端目录：
    ```powershell
    cd backend
    ```
3.  创建环境（首次创建可能较慢，涉及 PyTorch 和 CUDA 库）：
    ```powershell
    conda env create -f environment.yml
    ```
4.  激活环境：
    ```powershell
    conda activate mock-interview
    ```

### 2.2 配置环境变量

1.  在项目根目录下，将 `.env.example` 复制并重命名为 `.env`。
2.  编辑 `.env` 文件，填写您的 API Key（如 OpenAI 或 Google Gemini）以及其他配置。
    *   Windows 路径建议使用正斜杠 `/` 或 双反斜杠 `\\`。

### 2.3 初始化数据库与向量索引

在激活了 `mock-interview` 环境的终端中运行：

```powershell
# 回到项目根目录
cd ..

# 初始化数据库表
python deploy_scripts/init_db.py

# 构建向量知识库索引 (需确保 data/raw 下有数据)
python deploy_scripts/build_vector_index.py
```

### 2.4 启动后端服务

```powershell
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 3. 🌐 前端环境搭建 (Frontend)

1.  打开新的 PowerShell 窗口，进入前端目录：
    ```powershell
    cd frontend
    ```
2.  安装依赖：
    ```powershell
    pnpm install
    ```
3.  启动开发服务器：
    ```powershell
    pnpm dev
    ```
    访问 [http://localhost:5173](http://localhost:5173) 即可查看界面。

---

## 4. ⚠️ Windows 常见问题与解决方案

### 4.1 FFmpeg 与音频库报错
如果遇到 `ffmpeg` 或 `libsndfile` 相关报错，请确保您是在 `conda` 环境中运行的。Conda 会自动将这些二进制工具添加到环境路径中。

### 4.2 Celery 在 Windows 上运行
Celery 4.x 以后不再官方支持 Windows。如果需要运行异步任务，启动 worker 时请添加 `-P eventlet` 参数：
```powershell
# 先安装 eventlet
pip install eventlet
# 启动 worker
celery -A app.core.celery_app worker --loglevel=info -P eventlet
```

### 4.3 GPU 支持 (CUDA)
如果您有 NVIDIA 显卡并希望启用硬件加速：
1.  确保宿主机安装了最新的 **NVIDIA 驱动**。
2.  `environment.yml` 默认尝试安装 `pytorch-cuda=12.1`。
3.  验证命令：`python -c "import torch; print(torch.cuda.is_available())"`。如果返回 `True`，则说明加速已开启。

### 4.4 路径说明
由于 Windows 的路径长度限制或特殊字符问题，建议将项目存放在较浅的目录中，例如 `D:\projects\EchoMockSystem`。

---

## 5. 🚀 快速启动脚本 (可选)

您可以创建一个 `run_dev.bat` 放置在根目录，方便一键启动：

```batch
@echo off
start cmd /k "conda activate mock-interview && cd backend && uvicorn app.main:app --reload"
start cmd /k "cd frontend && pnpm dev"
```
