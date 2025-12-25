# simple_local_mqServer

本仓库已精简为一个“轻量级队列服务（Queue Server）+ Producer（任务入队）”的示例实现。仓库仅负责接收任务并将其入队（当前的队列实现为文件队列），具体的 Worker（任务消费与执行）被移出主树，并以一个最小示例提供在仓库根目录的 `worker.example` 文件，便于单独拆分到另一个仓库或作为参考实现。

## 设计与定位
- 目标：提供一个易于理解、便于测试的本地队列服务器与生产者实现，便于本地开发、演示和集成测试。
- 不负责：仓库不再承担 Worker 的职责（消费/执行任务），Worker 应另建仓库或使用示例代码。

## 仓库结构（主要文件）
- app/main.py
  - 基于 FastAPI 的 HTTP API，提供 POST /tasks 接口用于接收任务并调用 producer 将任务写入本地队列。
- tasks/producer.py
  - 生产者实现：将任务追加为 JSON 行到 `tasks/queue.jsonl`（文件队列）。
- db/result_store.py
  - 一个非常轻量的 SQLite-backed 结果/元数据存储，用于示例 Worker 记录任务状态与结果。
- worker.example
  - 仓库根目录下的最小示例 Worker（单文件脚本），演示如何从 `tasks/queue.jsonl` 弹出任务并将执行结果写入 `db/result_store.py`。
- tasks/huey_app.py（在本分支为占位文件）
  - 原先的 Huey-based Worker 已从主树移除；在此分支上保留占位文件以明确提示：Worker 应在独立仓库或用示例替代。
- config.py（在本分支为占位文件）
  - 原先的配置文件已被移除。运行时请使用环境变量来配置服务与 Worker（参见下文）。

## 如何运行（开发/演示）
1. 环境准备
   - 建议使用 Python 3.8+ 的虚拟环境：
     python -m venv .venv
     source .venv/bin/activate
   - 安装最少依赖（示例）：
     pip install fastapi uvicorn
   - 可选（如果使用示例 Worker 并希望使用 sqlite 功能）：
     pip install pysqlite3  # 大多数平台自带 sqlite3，无需额外安装

2. 启动 API 服务（Producer）
   - 启动命令（开发模式）：
     uvicorn app.main:app --reload --port 8000
   - POST 创建任务示例：
     curl -X POST "http://127.0.0.1:8000/tasks" \
       -H "Content-Type: application/json" \
       -d '{"prompt":"{\"op\":\"echo\",\"value\":\"hello\"}'}'
   - 成功后会在 `tasks/queue.jsonl` 写入一行 JSON（每行一个任务）。

3. 使用示例 Worker（可选）
   - 示例脚本位于仓库根目录 `worker.example`：
     python worker.example
   - 示例 Worker 会轮询 `tasks/queue.jsonl`，弹出任务，使用 `db/result_store.py` 记录任务状态与结果（单消费者实现，仅用于演示）。

## 配置（环境变量）
- QUEUE_FILE: 指定队列文件路径，默认 `tasks/queue.jsonl`。
- POLL_INTERVAL: 示例 Worker 的轮询间隔（秒），默认 `1.0`。
- ResultStore（db/result_store.py）默认使用文件 `comfy_queue.db`，可通过修改 ResultStore 的构造参数或示例 Worker 的实现来覆盖。

## 推荐的生产方案（非强制）
如果打算在生产环境使用该队列服务，请考虑：
- 将队列从文件队列替换为可靠的消息队列（Redis、RabbitMQ、Kafka 等）；
- 将 Worker 单独放到新仓库，设计为支持横向扩展与重试策略；
- 使用集中配置管理（环境变量、配置文件或配置服务）并在 CI 中加入端到端集成测试；
- 为结果存储选择生产级别的数据库（Postgres、Redis、或按需扩展的存储）。

## 为什么移除 Huey / config.py
- 简化主仓库职责：保持仓库聚焦于接收任务并入队；Worker 逻辑会引入额外依赖和运维维度，适合单独拆分。
- 降低运维/依赖复杂度：主仓库无需维护后台执行逻辑，便于快速部署用于测试或嵌入其他系统。

## 贡献与扩展
- 如果你想贡献 Worker 实现：建议在新的仓库中实现，并在 README 中说明如何与本仓库集成（例如使用相同的 tasks/queue.jsonl 路径或配置为 Redis 连接）。
- 如需恢复或替换为其他队列实现，可在 PR 中提交变更并附带运行与测试说明。

## 免责声明
本项目的文件队列实现仅用于本地开发/演示，不建议直接用于生产环境。请在生产前替换为可靠、持久且并发安全的队列后端。
