# simple_local_mqServer

一个基于 Huey 的本地任务队列服务（仅服务端）。该项目针对本地、小规模或开发场景进行了简化配置：默认使用 FileHuey（文件存储）作为队列后端，不再依赖外部 Redis，方便单机运行与调试。

本仓库只包含「服务端」部分：HTTP API + 任务入队与作业元数据/结果存储。消费者（worker）留待后续实现或由你自行运行 Huey consumer 来处理队列任务。

目录结构（重要文件）
- `app/` — FastAPI 服务代码（`main.py`, `schemas.py`）
- `tasks/` — Huey 实例与 producer（`huey_app.py`, `producer.py`）
- `db/` — 简单的 SQLite 元数据 / 结果存储（`result_store.py`）
- `config.py` — 环境变量与配置
- `requirements.txt` — 运行依赖
- `LICENSE` — MIT

特性概览
- 默认 FileHuey（文件 backed）作为队列后端（无需运行 Redis）。
- 使用 SQLite 存储任务元数据与结果（适合单机本地调试）。
- 提供 REST API：入队、查询状态、获取结果、列表、取消、健康检查、简单 metrics。
- 简单的 Bearer Token 验证（可通过环境变量启用）。

快速开始（本地）
1. 克隆仓库
   ```bash
   git clone https://github.com/AhBumm/simple_local_mqServer.git
   cd simple_local_mqServer
   ```

2. 建议使用虚拟环境并安装依赖
   ```bash
   python -m venv venv
   source venv/bin/activate    # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3.（可选）修改环境变量（示例）
   ```bash
   export QUEUE_BACKEND=file
   export FILE_HUEY_PATH=./huey_storage
   export SQLITE_PATH=./comfy_queue.db
   # 若要启用简单的 API 令牌验证：
   export COMFY_QUEUE_TOKEN="your-secret-token"
   # 修改 API 监听地址/端口（可选）
   export API_HOST=127.0.0.1
   export API_PORT=8000
   ```

4. 启动 API 服务
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

核心环境变量说明（常用）
- QUEUE_BACKEND: `file`（默认）或 `redis`（如需切回 Redis）
- FILE_HUEY_PATH: FileHuey 存储目录（默认 `./huey_storage`）
- SQLITE_PATH: SQLite 文件路径，用于存放任务元数据/结果（默认 `./huey_results.sqlite`）
- COMFY_QUEUE_TOKEN: 若设置，API 请求需带 Authorization: Bearer <token>
- API_HOST / API_PORT: FastAPI 服务绑定地址与端口

API 端点（HTTP）
- POST /enqueue
  - 描述：入队一个 ComfyUI 任务（graph + 可选元数据）
  - 请求体示例：
    ```json
    {
      "graph": { "nodes": [...] },
      "name": "my-job",
      "priority": 0,
      "metadata": { "user": "alice" }
    }
    ```
  - 返回示例：
    ```json
    { "job_id": "uuid-xxx", "status": "queued" }
    ```
  - curl 示例：
    ```bash
    curl -s -X POST http://127.0.0.1:8000/enqueue \
      -H "Authorization: Bearer your-token" \
      -H "Content-Type: application/json" \
      -d '{"graph":{"nodes":[]},"name":"test"}'
    ```

- GET /status/{job_id}
  - 描述：获取任务当前状态与元数据
  - 返回示例：
    ```json
    {
      "job_id": "uuid-xxx",
      "status": "queued|processing|finished|failed|cancelled",
      "result": {...} | null,
      "created_at": "2025-12-25T...",
      "updated_at": "2025-12-25T..."
    }
    ```

- GET /result/{job_id}
  - 描述：仅返回任务的 result 字段（通常是执行结果或指向 artifact 的路径）

- GET /jobs?limit=100
  - 描述：列出最近的任务（元信息）

- POST /cancel/{job_id}
  - 描述：尝试取消尚未执行的任务（在 DB 中标记为 cancelled）
  - 注意：消费者在执行任务前应检查 DB 状态以避免执行被取消的任务（server 端的标记需消费者配合生效）

- GET /health
  - 描述：基本健康检查（检查 FILE_HUEY_PATH 可读写、SQLite 文件存在等）

- GET /metrics
  - 简单占位，可扩展为 Prometheus 指标导出

FileHuey（文件后端）说明
- FileHuey 把队列、计划调度和结果存储为文件，适合单机、开发或轻量级本地部署。
- 优点：不需要 Redis，部署简单。
- 限制：
  - 不适合跨主机共享（不要把存储目录放在 NFS/SMB 上）。
  - 并发/吞吐量与 Redis 相比有限；若需要多机/高并发、强一致性或阻塞 pop，请切换到 RedisHuey。
  - FileHuey 在文件操作时使用锁避免竞态，但性能受限于文件系统。

切换到 Redis（可选）
若需要更高吞吐或分布式消费者，可以切换回 RedisHuey：
1. 安装 redis Python 客户端（例如 `pip install redis==4.7.0`）。
2. 启动 Redis 服务并设置环境变量：
   ```bash
   export QUEUE_BACKEND=redis
   export REDIS_URL=redis://localhost:6379/0
   ```
3. 修改或替换 `tasks/huey_app.py` 中的 Huey 实例为 `RedisHuey(...)`（示例已在仓库注释说明）。

关于消费者（worker）
- 当前仓库未包含完整的消费者实现（按你的要求先不实现）。
- 若要处理队列任务，你可以运行 Huey 自带的 consumer：
  ```bash
  # 启动 huey consumer，指向 huey 对象（示例）
  huey_consumer.py tasks.huey_app.huey
  # 或（按安装与版本）
  python -m huey.bin.huey_consumer tasks.huey_app.huey
  ```
- 消费者应在执行任务前检查 `db/result_store.py` 中的状态（例如是否被取消），并在执行后将结果写回 DB（目前 `run_comfy_job` 为占位实现）。

测试建议与调试小技巧
- 立即执行模式（供单机测试）：在 Python REPL 中设置 `huey.immediate = True`，可以让任务调用同步执行，便于快速调试。
- 查看 SQLite：使用 `sqlite3 comfy_queue.db` 或任何 SQLite 浏览器查看 `jobs` 表（状态/payload/result/时间戳）。
- 确保 `FILE_HUEY_PATH`（默认 `./huey_storage`）存在且可读写。

实现备注与扩展方向（可选）
- 将大文件（如生成的图片）保存为文件并在 DB 中保存路径，避免把二进制放入 SQLite JSON 字段。
- 为不同资源（GPU/CPU）或用户分配实现 consumer 端的过滤逻辑：消费者在取到任务时先检查任务 metadata（例如需要 GPU），若不能执行则重新入队或放弃。
- 集成 Prometheus 指标、添加 Docker / docker-compose、或实现 web UI。

许可
- 本项目采用 MIT 许可证，见 `LICENSE` 文件。

如果你希望，我可以：
- 把 README 翻译成英文或双语版本；
- 添加更多示例（比如完整的 curl 流程、用 Python 请求示例）；
- 或直接在仓库中提交此 README（需你允许我推送）。
