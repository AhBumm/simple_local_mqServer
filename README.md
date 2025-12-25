# simple_local_mqServer — 调用手册（中文，详尽）

版本说明
- 最新版本（本文档针对 2025-12-25 的实现）：默认使用 Huey 的 SqliteHuey（SQLite 文件）作为队列后端；同时保留一个独立的 SQLite ResultStore（huey_results.sqlite）用于保存任务元数据/结果索引与查询。
- 本仓库只包含服务端（API + producer + ResultStore）。任务执行端（consumer/worker）应运行 Huey consumer 或实现自定义 consumer 来执行实际作业（例如调用 ComfyUI 并把结果写入 NAS）。

目录
- 简介
- 目录结构
- 术语表
- 快速开始（本地）
- 环境变量与配置
- 详细 API 文档（示例、curl、Python）
- 任务入队与流程说明（Producer）
- Consumer（Worker）运行与实现建议
- ResultStore（huey_results.sqlite）字段约定与示例
- NAS / Artifact 写入最佳实践（原子流程）
- 常见运维与故障排查
- Docker / docker-compose 简要说明
- 监控 / 日志 / 备份 建议
- FAQ
- 贡献与许可

-------------------------------------------------------------------------------
简介
-------------------------------------------------------------------------------
simple_local_mqServer 是一个轻量的本地任务队列服务：
- 接受外部（如 ComfyUI 或前端）提交的任务（描述为 prompt 字符串：ComfyUI 导出的完整工作流 JSON 的字符串形式）。
- 把任务写入本地队列（当前为简单的 JSONL 文件或 Huey SqliteHuey，可配置）；由 consumer 拉取执行。
- 保存任务元信息与执行结果指针到一个独立的 SQLite（ResultStore），便于查询、取消与列表操作（在本精简模式中，ResultStore 可选由 consumer 实现，当前实现使用 tasks/queue.jsonl）。
适用场景：单机、小规模、开发或内网环境。若需高并发或分布式部署，建议使用 RedisHuey + 更健壮的结果存储（Postgres/S3 等）。

-------------------------------------------------------------------------------
目录结构（重要文件）
-------------------------------------------------------------------------------
- app/
  - main.py        # FastAPI HTTP API 实现（/tasks 或 /enqueue）
- tasks/
  - producer.py    # enqueue_task: 把 prompt 校验并持久化到 tasks/queue.jsonl
- README.md        # 本文件
- requirements.txt # Python 依赖（如有）
- LICENSE          # MIT（或你选择的许可）

-------------------------------------------------------------------------------
术语表
-------------------------------------------------------------------------------
- Producer：负责接受 HTTP 请求并把任务入队（本项目的 FastAPI）。
- Consumer / Worker：读取队列文件并执行任务（本仓库提供简单队列持久化，consumer 需自己实现执行逻辑）。
- Prompt：ComfyUI 导出的完整工作流 JSON 的字符串形式（本服务要求的唯一输入字段）。
- ResultStore：任务结果存放/索引（本简化实现使用 tasks/queue.jsonl 作为持久化，生产场景建议使用独立的 DB）。

-------------------------------------------------------------------------------
快速开始（本地）
-------------------------------------------------------------------------------
1. 克隆仓库
```bash
git clone https://github.com/AhBumm/simple_local_mqServer.git
cd simple_local_mqServer
```

2. 建议使用虚拟环境并安装依赖
```bash
python3 -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt  # 如果没有 requirements，请至少安装 fastapi uvicorn
```

3. 配置（可选）
```bash
export API_HOST=127.0.0.1
export API_PORT=8000
```

4. 启动服务（API）
```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

-------------------------------------------------------------------------------
重要说明：最简模式与请求约定
-------------------------------------------------------------------------------
- 本服务采用最简模式（应你的要求）：入队仅接受三个要素：
  - prompt（必须）：完整的 ComfyUI 工作流 JSON 的字符串形式（服务端会验证其为可解析的 JSON）；
  - priority（可选，整数，默认 1）；
  - metadata（可选，但仅保留 prompt_id 与 create_time 两个字段，其他字段会被拒绝）。
- 接口路径为 POST /tasks（或 /enqueue，视实现），请求体示例在下文。

-------------------------------------------------------------------------------
API 详解（HTTP）
-------------------------------------------------------------------------------
注意：本简化实现未启用鉴权；若在生产或内网部署建议加入简单的 Bearer Token 或内网防火墙规则。

1) POST /tasks
- 描述：把 ComfyUI 的 prompt（字符串）入队为待执行任务。
- 请求体（JSON）示例：
```json
{
  "prompt": "{ \"3\": {\"class_type\": \"KSampler\", \"inputs\": {\"seed\":5, \"steps\":20}}, \"6\": {\"class_type\": \"CLIPTextEncode\", \"inputs\":{\"text\":\"masterpiece\"}} }",
  "priority": 5,
  "metadata": { "prompt_id": "frontend-1234", "create_time": 1714012345678 }
}
```
- 返回：
```json
{ "status": "queued", "task": { "prompt": "...", "priority":5, "metadata": {"prompt_id":"...","create_time":...} } }
```
- 校验规则：
  - prompt 必须为字符串且内容能被 JSON 解析（json.loads 能成功）。
  - metadata 只能包含 prompt_id 与 create_time，其他键会导致 400。

2) GET /health
- 描述：基本健康检查（服务是否在线、队列文件是否可写）

-------------------------------------------------------------------------------
任务入队与内部流程（Producer）
-------------------------------------------------------------------------------
1. Producer（API）流程：
   - 接受请求并校验 prompt 为 JSON 字符串；
   - 若 metadata 未提供 prompt_id 或 create_time，则自动补齐；
   - 生成 task_id / created_at 并把任务以单行 JSON 追加到 tasks/queue.jsonl（append-only）。

2. 为什么采用 JSONL 文件持久化？
   - 极简、易于调试、无外部依赖（适合内网/小规模）
   - 若需要更强的并发与可查询性，可迁移到 Redis / Postgres 并集成 Huey。 

-------------------------------------------------------------------------------
Consumer（Worker）实现建议
-------------------------------------------------------------------------------
- Consumer 从 tasks/queue.jsonl 读取新行并解析为 JSON（每行为一个 task 对象），
  然后用 json.loads(task['prompt']) 得到 ComfyUI graph（对象）并交给 ComfyUI 的执行器或自定义 executor。
- 执行生成的 artifact 由 consumer 自行写到 NAS / 本地磁盘 / 对象存储，并在外部系统记录结果（本简化实现不强制 consumer 回写 ResultStore）。
- 当执行前应检查 task.metadata.prompt_id 用来追踪，若需要幂等请 consumer 做去重检查。

-------------------------------------------------------------------------------
ResultStore 与简化策略
-------------------------------------------------------------------------------
- 本简化实现将任务直接写入 tasks/queue.jsonl，未内置复杂的 ResultStore 写回逻辑。建议在 production 场景添加独立结果数据库（例如 huey_results.sqlite 或 Postgres），并由 consumer 在完成时写回结果 metadata（artifact_path、size、checksum、completed_at）。

-------------------------------------------------------------------------------
NAS / Artifact 写入最佳实践（原子流程）
-------------------------------------------------------------------------------
当 consumer 将生成的二进制写入 NAS 时请遵循以下步骤：
1. 先写临时文件（例如 /nas/.../out.png.tmp）
2. flush + fsync
3. os.replace(tmp, final)（在同一文件系统上原子重命名）
4. 更新 result 数据（写入 ResultStore，由 consumer 负责）

-------------------------------------------------------------------------------
常见运维与故障排查
-------------------------------------------------------------------------------
- 400 Bad Request：prompt 非字符串或不能解析为 JSON，或 metadata 包含非法键。
- 写入失败：检查 tasks/ 目录权限与磁盘空间。
- 队列滞留：consumer 没有运行或没有轮询队列文件。可以用 tail -f tasks/queue.jsonl 查看新项。

-------------------------------------------------------------------------------
Docker / docker-compose（简要）
-------------------------------------------------------------------------------
示例（简略）：
```yaml
version: '3.8'
services:
  api:
    image: python:3.11-slim
    volumes:
      - ./data:/data
      - ./:/app
    working_dir: /app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000
```

-------------------------------------------------------------------------------
监控 / 日志 / 备份 建议
-------------------------------------------------------------------------------
- 日志：把 API 的访问日志和 consumer 的执行日志集中收集。
- 备份：定期备份 tasks/queue.jsonl（以防数据丢失）和 consumer 写入的 artifact。

-------------------------------------------------------------------------------
FAQ
-------------------------------------------------------------------------------
Q: prompt 必须是字符串吗？
A: 是。本简化实现要求 prompt 为 JSON 字符串，便于前端导出后直接传送并保证后端一致性。如果你希望改为接收 JSON 对象，我可以修改 API。

Q: 为什么不内置 callback？
A: 简化设计目标是降低复杂度；消费者可以自行实现回调或通过外部系统处理通知。

-------------------------------------------------------------------------------
贡献、联系与许可
-------------------------------------------------------------------------------
- 欢迎提交 Issue / PR。请在 PR 中描述用例与测试步骤。
- 许可证：MIT（详见 LICENSE）

-------------------------------------------------------------------------------
下一步我可以为你做的事（任选）
- 把 README 直接写入仓库（已准备好）；
- 添加一个示例 consumer 脚本，展示如何从 tasks/queue.jsonl 读取并执行 prompt；
- 或把 API 改为接受 JSON 对象形式的 prompt（代替字符串）。

请确认是否需要我直接提交此 README 到 main 分支并替换现有 README.