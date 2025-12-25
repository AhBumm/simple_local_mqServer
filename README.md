# simple_local_mqServer

轻量级本地消息队列示例项目

## 概览

这个仓库提供了一个非常简单的本地消息队列实现、生产者、消费者示例，以及用于把旧格式（JSONL）迁移到 SQLite 的脚本。

- tasks/db.py: SQLite 后端的队列实现（enqueue/dequeue/ack 等）
- tasks/producer.py: 使用 SQLite 后端发送消息的生产者脚本
- tasks/migrate_jsonl_to_sqlite.py: 将 JSONL 格式的消息导入 SQLite 的迁移工具
- examples/worker_sqlite.py: 使用 SQLite 队列的消费者示例


## 使用 SQLite 后端（中文说明）

该项目现在支持以 SQLite 数据库作为队列后端，适合单机或轻量级场景，优点是易于持久化与迁移。

快速上手：

1. 安装（如果需要）：
   - 仅需 Python（内置 sqlite3），无需额外依赖。

2. 生产者：
   - 命令行发送：
     python -m tasks.producer <topic> '<JSON or text payload>' --db path/to/queue.sqlite3
   - 例如：
     python -m tasks.producer default '{"hello": "world"}'

3. 消费者：
   - 启动示例 worker：
     python examples/worker_sqlite.py --db path/to/queue.sqlite3 --topic default
   - 示例 worker 会调用 dequeue、处理并 ack；出错时会将消息 requeue（带短延迟）。

4. 可选：通过环境变量指定默认 DB
   - 设置环境变量 SIMPLE_MQ_DB=/path/to/queue.sqlite3，tasks.db 模块会使用该路径作为默认数据库。

5. 数据迁移（从旧的 JSONL 文件迁移到 SQLite）
   - 如果你有一份 JSONL 文件（每行是 JSON 消息），可以使用迁移脚本：

     python -m tasks.migrate_jsonl_to_sqlite path/to/messages.jsonl --sqlite path/to/queue.sqlite3

   - 支持的 JSONL 行格式示例：
     {"topic": "default", "payload": {"a": 1}}
     {"topic": "emails", "message": "hello"}
     "plain string message"

   - 若行不是合法 JSON，会作为纯文本 payload 导入。

6. SQLite 队列实现细节（简要）
   - 表结构包含：id, topic, payload, created_at, available_at, status, locked_until
   - dequeue 会将找到的消息标记为 processing 并设置 locked_until（可见性超时），以防止并发重复处理
   - ack 会删除已确认的消息；若处理失败可调用 requeue 将消息放回队列（并可设置延迟）


常见问题：
- 并发：SQLite 适合低到中等并发场景。对于高并发、多进程大量写入的场景，建议使用专门的消息队列（如 RabbitMQ、Redis、Kafka 等）。
- 可视化：直接用 sqlite 浏览工具查看队列表内容（例如 sqlite3 命令行或 DB 浏览器）。


## English (short)

This repository includes a SQLite-backed queue implementation, a producer adapted to the SQLite backend, a migration script from JSONL, and a worker example. Use for local or development scenarios where a lightweight persistent queue is desirable.


---

If you'd like different behavior (e.g. keep processed messages instead of deleting them, or add message metadata), tell me what you want and I can adjust the implementation.
