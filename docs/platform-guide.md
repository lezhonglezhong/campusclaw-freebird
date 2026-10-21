# AI 应用工作台

登录后从“班级材料”点击“AI 应用工作台”，或访问 `/apps`。提供写作润色、学习规划、练习生成三个应用，原有知识库检索和带引用问答保留在 `/materials`。

## 使用

1. 教师在工作台创建模板，可使用 `{{input}}` 和 `{{audience}}`，保存后自动选中。可编辑、删除；本班学生可选用。
2. 选择内置“起草与审校”“学习教练”，或上传 JSON 技能。示例下载在页面中，也在 `campusclaw/static/example-skill.json`。技能最多 16 KiB、1–3 个步骤，每一步调用模型，下一步接收上一步结果。整个技能清单逐步发送给模型；不执行脚本或 shell。
3. 可选绑定本班知识库；此时无证据不调用对话模型，有证据只发送有限切片并校验最终引用。未绑定时可以使用模型常识，不生成知识库来源卡片。
4. 教师启用外部连接后，学生勾选允许本次调用的工具。外部服务应为部署者信任且适用于自动调用的服务。页面显示执行结果和仅本人可见的精确请求、模型返回、技能步骤及工具结果。
5. 最近 30 条记录可重新打开。请求参数最多 4000 字符，模板 8000，目标读者 200；最多 3 个技能步骤、每步 3 轮模型请求、每次运行最多 4 次工具调用。

## 外部工具与 MCP

`docker compose up --build -d --wait` 会启动独立的 `demo-tools` 内部服务，不开放宿主机端口。默认提供 HTTP 和 MCP 计算器连接，但必须由教师对本班启用。计算器只进行数字加减乘除，不读取课程或用户数据。

可通过私有 `.env` 的 `PLATFORM_CONNECTORS_JSON` 替换连接目录。设为 `[]` 禁用全部连接；留空时 Compose 使用演示服务。示例：

```json
[
  {"id":"remote-mcp","label":"课程工具","type":"mcp","url":"https://tools.example.com/mcp","token_env":"COURSE_TOOLS_TOKEN"},
  {"id":"remote-http","label":"外部查询","type":"http","url":"https://tools.example.com/query","input_schema":{"type":"object","properties":{"query":{"type":"string"}},"required":["query"],"additionalProperties":false}}
]
```

`token_env` 是服务进程环境变量名，不是令牌本身；配置该变量时通过私有 Compose override 的 `environment` 或私有 env_file 注入应用容器。不要提交密钥。URL 固定在服务端配置，不允许浏览器或模型提供任意地址，不跟随 HTTP 重定向。HTTP 适配器 POST JSON 参数并接受 JSON 对象返回。

MCP 支持 **2025-06-18 Streamable HTTP**：initialize → notifications/initialized → tools/list → tools/call，支持 JSON/POST SSE、会话与版本头、分页（最多 5 页/32 工具），不实现 stdio、OAuth 配置或服务器发起的 sampling。模型获得命名空间隔离后的函数定义，通过 tool_calls 请求调用，结果以 role=tool 和对应 tool_call_id 回填。只接受选定工具及通过 JSON Schema 校验的参数；不接受 schema 的外部引用。网络超时 10 秒，工具返回最多 64 KiB；错误不伪装成成功。

协议依据：[MCP transports](https://modelcontextprotocol.io/specification/2025-06-18/basic/transports)、[lifecycle](https://modelcontextprotocol.io/specification/2025-06-18/basic/lifecycle)、[tools](https://modelcontextprotocol.io/specification/2025-06-18/server/tools)。

## 验证及部署

```bash
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider
```

真实 Chromium 测试使用临时数据库、独立 HTTP/MCP 服务及确定性的模型替身，不使用线上课程正文。浏览器安装依据 [Playwright Python](https://playwright.dev/python/docs/intro)。更新部署前运行全量测试；新增数据库表由应用启动时创建，不改变已有材料表，不删除数据卷。回滚应用镜像可保留新增表。不要使用 `down -v`。

执行记录保存用户输入和模型返回，应仅使用本人获授权的材料。记录不包含传输鉴权头或连接地址；上游模型附加字段可能存在于返回 JSON 中，浏览器默认折叠详细记录。
