# simple_local_mqServer

简体中文使用手册（详细）

## 简介

simple_local_mqServer 是一个用于本地环境的轻量级消息队列服务（示例/参考实现）。它旨在帮助开发者在本地进行消息发布/订阅、队列管理和功能验证，便于测试微服务、异步任务以及消息驱动流程。

> 注：本 README 为通用的中文操作与配置手册。具体命令、文件路径或可执行方式请根据仓库实际语言与实现（例如 Go、Node、Python 等）调整。

## 主要特性

- 本地消息队列管理（创建、删除、列出队列）
- 消息发布与消费接口（支持短轮询/长轮询或推送，视实现而定）
- 持久化或内存存储（取决于配置）
- 简单的认证或访问控制（若实现）
- 可扩展的配置文件或命令行参数

## 环境与前置要求

请在本地安装以下通用工具（依据项目语言调整）：

- Git
- 对应运行环境或编译器：例如 Go（go 1.20+）、Node.js（>=14）、Python（>=3.8）等，视项目实现而定
- 可选：Docker、docker-compose（如仓库提供 Docker 支持）

## 快速开始（通用步骤）

1. 克隆仓库：

   git clone https://github.com/AhBumm/simple_local_mqServer.git
   cd simple_local_mqServer

2. 构建或安装（根据仓库/语言）：

   - 如果是 Python 项目：
     - python3 -m venv venv
     - source venv/bin/activate
     - pip install -r requirements.txt
     - python3 main.py

   如果仓库包含 Dockerfile，可以直接：

   docker build -t simple_local_mqserver .
   docker run -p 8080:8080 --name mqserver simple_local_mqserver

3. 启动服务（示例）：

   ./mqserver --host 0.0.0.0 --port 8080 --config config.yaml

   - 注意：实际命令行参数请以项目实现和 README 中的 `--help` 输出为准，例如 `./mqserver --help`。

## 配置（示例 config.yaml）

以下为常见配置项示例：

```yaml
server:
  host: "0.0.0.0"
  port: 8080
storage:
  type: "memory" # 或者 "file" / "sqlite" / "leveldb"
  data_dir: "./data"
auth:
  enabled: false
  token: "changeme"
logging:
  level: "info"
```

将配置保存为 `config.yaml`，并通过命令行参数或环境变量指向该配置。

## 命令行参数示例

服务通常会提供一些常用参数：

- --host: 监听的地址（默认 0.0.0.0）
- --port: 监听端口（默认 8080）
- --config: 指定配置文件路径
- --data-dir: 指定本地数据目录
- --log-level: 日志等级（debug/info/warn/error）

使用 `--help` 或 `-h` 查看完整参数列表。

## HTTP API 快速参考（示例）

下列 API 为示例接口，具体请参考代码或项目中的 API 文档。

- 列出队列
  - 请求：GET /queues
  - 返回：JSON 队列列表

- 创建队列
  - 请求：POST /queues
  - Body (JSON)：{ "name": "my-queue" }

- 发布消息
  - 请求：POST /queues/{queueName}/publish
  - Body (JSON)：{ "message": "hello world", "meta": {...} }
  - 响应：{ "message_id": "..." }

- 消费消息（短轮询示例）
  - 请求：GET /queues/{queueName}/consume
  - 参数：?timeout=30
  - 响应：{ "message_id": "...", "message": "..." }

- 确认/删除消息
  - 请求：DELETE /queues/{queueName}/message/{messageId}

示例 curl：

发布消息：

curl -X POST "http://localhost:8080/queues/my-queue/publish" \
  -H "Content-Type: application/json" \
  -d '{"message":"hello","meta":{}}'

消费消息（短轮询）：

curl "http://localhost:8080/queues/my-queue/consume?timeout=10"

## 客户端示例（伪代码）

发布：

POST /queues/{queue}/publish
Body: { message: "..." }

消费：

GET /queues/{queue}/consume?timeout=30

处理后确认：

DELETE /queues/{queue}/message/{id}

注意：如果实现支持一次拉取多条或批量确认，请参阅具体接口定义。

## 持久化与数据丢失风险

- 当 storage.type 为 memory 时，服务重启将丢失所有队列与消息，仅适合测试环境。
- 若需持久化，请使用 file/sqlite/leveldb 或外部数据库，并确保 data_dir 有合适的读写权限与备份策略。

## 日志与调试

- 调整日志级别为 debug 以获取更多运行时信息。
- 查看 data 目录或日志文件以定位持久化/序列化问题。

## 常见问题与排查建议

- 端口被占用：检查并释放端口或修改配置端口
- 消息无法被消费：检查队列名、是否已正确发布、是否存在消费锁或可见性超时
- 权限问题：确认运行用户对 data_dir 的读写权限
