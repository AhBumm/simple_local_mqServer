# simple_local_mqServer — 详细中文手册

本文档提供对 simple_local_mqServer 的详细介绍、安装与使用说明，重点说明最新的 API 行为：/enqueue 接口现在强制要求使用 `prompt` 字段作为请求负载，服务端内部会将其标准化为 `graph` 用于内部处理。

目录
- 功能简介
- 安装与运行
- /enqueue API 规范（必须使用 prompt）
- 请求示例
- 返回与错误码
- 内部行为：prompt 如何被标准化为 graph
- 队列持久化与消费提示
- 常见问题与调试

功能简介
------
simple_local_mqServer 是一个轻量级的本地消息队列服务，采用最简单的持久化（文件行追加）方式存储要处理的任务。该服务设计目标是极简、易于部署与调试，适用于原型开发和本地流程编排。

安装与运行
------
先确保 Python >= 3.8，推荐使用虚拟环境：

1. 克隆仓库

   git clone https://github.com/AhBumm/simple_local_mqServer.git
   cd simple_local_mqServer

2. 安装依赖（如果项目使用 requirements.txt）：

   pip install -r requirements.txt

   如果没有依赖文件，FastAPI 与 uvicorn 是运行服务的基本要求：

   pip install fastapi uvicorn

3. 运行服务（开发示例）

   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

API: /enqueue（强制 prompt-only）
------
- 路径: POST /enqueue
- 请求体: JSON，必须包含字段 "prompt"
- Content-Type: application/json

请求体示例 (必须要有 prompt 字段)
- 最简单的字符串 prompt：

  {
    "prompt": "请生成一个简单的图形描述：节点 A 连接到 B"
  }

- 或者 prompt 也可以是一个 JSON 对象（例如前端直接构造的图对象）：

  {
    "prompt": {
      "nodes": [{"id": "A"}, {"id": "B"}],
      "edges": [{"from": "A", "to": "B"}]
    }
  }

注意：/enqueue 现在不接受自由结构的请求（例如直接使用 "graph" 字段等）——必须使用 "prompt" 作为唯一入口。

curl 示例
------
1) 发送简单字符串 prompt

curl -X POST http://localhost:8000/enqueue \
  -H "Content-Type: application/json" \
  -d '{"prompt": "生成一张包含 3 个节点的示例图"}'

2) 发送 JSON object 作为 prompt

curl -X POST http://localhost:8000/enqueue \
  -H "Content-Type: application/json" \
  -d '{"prompt": {"nodes": [{"id": "1"}, {"id": "2"}], "edges": [{"from": "1", "to": "2"}]}}'

响应
------
成功时返回 200，并包含任务 id：

{
  "id": "<task_id>",
  "status": "queued"
}

错误情况示例：
- 400 Bad Request: 请求中缺失 prompt 或 prompt 为空
- 500 Internal Server Error: 服务内部错误（例如磁盘写入失败）

内部行为：prompt -> graph 标准化
------
为了对外保持简单（客户端只需提供 prompt），服务端在接收后会进行如下标准化流程：

1) 如果 prompt 是一个对象（JSON 对象/字典），将其直接视为 graph。
2) 如果 prompt 是字符串，尝试将其解析为 JSON：
   - 若解析结果为对象，则作为 graph 使用；
   - 否则，将字符串放入 {"text": <prompt>} 作为 graph 的文本表示；
3) 其他类型会被包装为 {"value": <原始值>}。

最终的队列项包含至少以下字段：
- id: 任务唯一 id
- created_at: 时间戳
- graph: 标准化后的图结构
- status: 当前队列状态（初始为 "queued"）

队列持久化
------
目前实现为将每个任务以一行 JSON 的形式追加到存放在 tasks/queue.jsonl 的文件中。这个文件可以被消费者按行读取并解析 JSON 来处理任务。该方式简单透明，适合本地或开发环境。

消费者提示
------
- 消费者可通过 tail -f tasks/queue.jsonl 或者编写脚本按行读取并解析新的 JSON 行来获得任务。
- 处理完任务后，建议将处理结果写入单独的文件或把状态更新到中央存储（本项目未内置任务状态更新 API）。

常见问题与调试
------
- 如果提示 400，检查请求体是否为有效 JSON，并且包含了非空的 "prompt"。
- 如果服务无法写入队列文件，请检查运行用户对仓库 tasks/ 目录的写权限。
- 如果需要更复杂的持久化或分布式队列，建议替换持久化层（例如使用 Redis、Postgres 或消息队列服务）。

贡献
------
欢迎提交 issue 或 pull request。对于生产级使用，请考虑增强持久化、保证幂等性和增加任务消费确认机制。

许可
------
请查看仓库根目录的 LICENSE 文件（如果存在）。
