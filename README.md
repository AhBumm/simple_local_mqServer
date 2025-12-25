# simple_local_mqServer

仓库定位
- 简单轻量的队列服务（Producer + 文件队列）。负责接收任务并入队（当前以 tasks/queue.jsonl 为队列）。
- 不包含复杂的 Worker，Worker 可单独实现或参考仓库根的 `worker.example`。

主要文件
- app/main.py — FastAPI 服务，提供 POST /tasks 接口用于入队（返回 job_id）。
- tasks/producer.py — 将任务追加为 JSONL（tasks/queue.jsonl）。
- db/result_store.py — 简单的 SQLite 结果/元数据存储（供 Worker 使用）。
- worker.example — 最简消费示例（示例脚本）。

快速开始（本地）
1. 创建环境并安装（示例）
   python -m venv .venv
   source .venv/bin/activate
   pip install fastapi uvicorn

2. 启动服务（Producer）
   uvicorn app.main:app --reload --port 8000

3. 入队示例（返回 job_id）
   curl -X POST "http://127.0.0.1:8000/tasks" \
     -H "Content-Type: application/json" \
     -d '{"prompt":"{\"op\":\"echo\",\"value\":\"hello\"}'}'

4. 查看队列
   tail -n 5 tasks/queue.jsonl

使用示例 Worker
- 仓库根的 `worker.example` 是一个最小演示：轮询 tasks/queue.jsonl，消费一条任务并用 db/result_store.py 写入结果。
- 运行示例：
    python worker.example

注意事项
- 文件队列仅适合本地/开发/演示。生产请使用可靠队列（Redis、RabbitMQ 等）和独立 Worker 服务。
- 若需要查询任务状态或支持并发/lease、认证等，请在独立的 Worker/服务中实现这些功能。

贡献
- 若要贡献 Worker，请在新仓库实现并说明如何与本仓库整合（文件队列或替换为 MQ）。
