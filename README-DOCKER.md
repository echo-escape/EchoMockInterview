# 🐳 EchoMock 全栈项目 Docker 本地开发指南

本指南旨在帮助开发者利用 Docker 快速搭建 **EchoMock** 的完整开发环境。通过本方案，你可以实现：
- **一键启动**：前端、后端、数据库及 AI 模型服务。
- **硬件加速**：直接在容器内调用宿主机的 NVIDIA GPU (CUDA)。
- **热更新 (Hot-Reload)**：修改本地代码后，容器会自动重新加载，无需重启。

---

### 1. 环境准备 (Prerequisites)

在开始之前，请根据你的操作系统选择最适合的方案：

#### 方案 A：Windows (推荐使用 WSL2 + Docker)
- **NVIDIA 驱动**：安装最新的 [NVIDIA 驱动](https://www.nvidia.com/Download/index.aspx)。
- **Docker Desktop**：
  - 勾选 `Settings -> General -> Use the WSL 2 based engine`。
  - 勾选 `Settings -> Resources -> WSL Integration -> [你的 Ubuntu 分发版]`。

#### 方案 B：Windows (原生直连 - 不使用 WSL2/Docker)
如果你不想使用 WSL2，可以直接在 Windows 宿主机运行：
- **Python 3.11**：通过 [Python 官网](https://www.python.org/) 安装。
- **Node.js 20+**：安装 Node.js 并使用 `npm install -g pnpm`。
- **显卡库**：安装对应版本的 CUDA Toolkit (推荐 12.1)。
- **运行方式**：参考本手册后续的 [7. 备选：原生 Windows 开发](#7-备选原生-windows-开发)。

#### 方案 C：Linux (原生 Docker)
- **Docker Engine** & **Docker Compose**。
- **NVIDIA Container Toolkit**：[安装指南](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)。

---

## 2. 快速上手 (Quick Start)

项目根目录已配置好 `docker-compose.yml`，只需一行命令即可启动：

```bash
# 第一次启动或依赖更新时建议加上 --build
docker-compose up --build
```

启动成功后：
- **前端地址**：[http://localhost:5173](http://localhost:5173)
- **后端服务**：[http://localhost:8000](http://localhost:8000)
- **API 文档**：[http://localhost:8000/docs](http://localhost:8000/docs)
- **健康检查**：[http://localhost:8000/health](http://localhost:8000/health)

---

## 3. 初始化数据与向量索引 (Init Data & Vector Index)

**⚠️ 重要说明：**
如果是首次启动，或者你修改了 `/data/raw` 下的面试题库（Markdown 文件），你必须手动运行向量化脚本，否则 AI 将无法检索到面试题。

在容器保持运行的状态下，打开另一个终端执行：

```bash
# 1. (可选) 手动初始化数据库表
docker-compose exec backend python deploy_scripts/init_db.py

# 2. 构建向量库索引（必须执行，用于 AI 检索题库）
docker-compose exec backend python deploy_scripts/build_vector_index.py
```

---

## 4. 本地开发工作流 (Local Development Workflow)

### 代码热更新
- **后端**：我们通过挂载 `./backend` 卷并使用 `uvicorn --reload` 实现。你修改 `backend/app/` 下的 Python 代码，容器会自动重载。
- **前端**：我们通过挂载 `./frontend` 卷并利用 Vite 的 HMR 实现。修改 Vue 组件后浏览器会即时更新。

### 环境变量管理
- 容器会自动加载根目录下的 `.env` 文件。
- 如果你修改了 `.env` 中的关键配置，请使用 `docker-compose up -d` 重新应用。

### 查看日志
```bash
# 查看所有服务的实时日志
docker-compose logs -f

# 仅查看后端日志
docker-compose logs -f backend
```

### 进入容器内部调试
```bash
# 进入后端执行命令 (如运行数据库迁移)
docker-compose exec backend /bin/bash
```

---

## 4. GPU 验证 (GPU Verification)

由于本项目使用了 **FunASR** 和 **PyTorch**，GPU 加速至关重要。你可以通过以下命令验证容器是否成功识别 GPU：

```bash
docker-compose exec backend nvidia-smi
```

如果能看到显卡型号和显存占用，说明配置成功。

---

## 5. 常见问题排查 (Troubleshooting)

- **Q: 启动后报错 "NVIDIA: get subclass id from device node failed"**
  - **A**: 通常是由于 Docker Desktop 没能正确识别到 GPU 驱动。请尝试在 Windows 下重新安装驱动，并重启 Docker Desktop。
- **Q: 前端无法连接后端 API**
  - **A**: 默认 `VITE_API_URL` 设置为 `http://localhost:8000`。如果你在 WSL2 内部通过 IP 访问，请检查浏览器是否能解析该地址。
- **Q: 更新 `requirements.txt` 后容器内没生效**
  - **A**: 运行 `docker-compose up --build` 强制重新构建镜像。
- **Q: 磁盘空间不足**
  - **A**: AI 镜像较大（约 5GB+），请确保 Docker 的磁盘配额充足。

---

## 6. 服务编排说明 (Component Details)

- **Backend**: 基于 `python:3.11-slim`，安装了 CUDA 12.1 兼容的 PyTorch。
- **Frontend**: 基于 `node:20-slim`，使用 `pnpm` 进行依赖管理。
- **Volumes**: 
  - `data/`: 持久化存储 SQLite 数据库和向量索引，重启不丢失。
  - `node_modules/`: 容器内独立管理，避免与物理机冲突。

---

## 7. 备选：原生 Windows 开发 (不使用 WSL2/Docker)

如果你无法使用 WSL2 或 Docker，请按以下步骤在 Windows 上直接运行项目：

### 后端配置
1.  **创建虚拟环境**:
    ```powershell
    cd backend
    python -m venv venv
    .\venv\Scripts\activate
    ```
2.  **安装 PyTorch (CUDA 12.1)**:
    ```powershell
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu121
    ```
3.  **安装其他依赖**:
    ```powershell
    pip install -r requirements.txt
    ```
4.  **启动后端**:
    ```powershell
    python -m uvicorn app.main:app --reload
    ```

### 前端配置
1.  **安装依赖**:
    ```powershell
    cd frontend
    pnpm install
    ```
2.  **启动前端**:
    ```powershell
    pnpm dev
    ```

> [!WARNING]
> **注意**：原生 Windows 环境下，你需要手动安装 `ffmpeg` 并将其添加到系统的 PATH 环境变量中，否则音频处理功能将失效。
