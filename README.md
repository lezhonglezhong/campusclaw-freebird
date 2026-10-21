# CampusClaw

CampusClaw 是“互联网软件技术开发与实践”课程的三人小组学期项目，由 Freebird 小组维护；仓库名为 `campusclaw-freebird`。

## 开发方式

本项目采用 Specification-Driven Development（SDD）。当前阶段通过 OpenSpec 定义 CampusClaw 的需求、设计、验收标准和实施任务。

## Docker Compose 启动

Compose 启动应用、MySQL 8 与 Qdrant。MySQL 和 Qdrant 使用持久卷，只在
Compose 内部网络开放；应用映射本机 8000 端口。首次启动先编辑私有配置：

```bash
cd campusclaw-freebird
cp .env.example .env
# 为 TOKEN_SIGNING_SECRET、MYSQL_ROOT_PASSWORD、MYSQL_PASSWORD 分别设置随机值；
# 将 EMBEDDING_API_KEY 换成课程网关提供的私有密钥。
docker compose up --build -d --wait
docker compose exec campusclaw python -m flask --app campusclaw seed
```

浏览器访问 `http://localhost:8000/login`。

使用 `docker compose ps` 可确认三个服务状态为 `healthy`；应用健康检查
地址为 `/health`。若尚未配置网关密钥，上传与关键词检索仍可使用，向量
检索、混合检索和问答会返回明确的 503。配置密钥后，可通过教师页面重建
索引，或使用下方回填命令。

### 从旧 SQLite 容器迁移

升级前先保留旧容器的 `/app/instance`。在仓库目录中，确认本地尚无
`instance` 目录，然后执行：

```bash
docker cp campusclaw-freebird-campusclaw-1:/app/instance ./instance
docker compose up --build -d --wait
docker compose exec campusclaw python -m flask --app campusclaw migrate-legacy-sqlite
docker compose exec campusclaw python -m flask --app campusclaw backfill-knowledge
```

迁移命令只接受空的 MySQL 目标；旧 SQLite 文件和原始材料保留在忽略 Git 的
`instance` 目录中。全新安装直接执行 `seed`，无需运行迁移。
若旧资料保存在 `instance/legacy-container` 等独立目录，可用
`migrate-legacy-sqlite --source /app/instance/legacy-container/campusclaw.sqlite3`；
迁移会将材料路径指向该目录中的文件，不覆盖其他已有资料。

## Token 登录与接口调用

`POST /login` 成功后返回短期 JWT access token。系统不设置或接受登录
Cookie；浏览器只把 token 保存在当前标签页的 `sessionStorage` 中。除登录、
健康检查和页面外壳外，所有受保护接口都必须显式携带 Bearer header：

```bash
curl -s http://localhost:8000/login \
  -H 'Content-Type: application/json' \
  -d '{"account":"teacher-a","password":"teacher-a-password"}'

curl -s http://localhost:8000/api/me \
  -H 'Authorization: Bearer <access_token>'
```

`TOKEN_SIGNING_SECRET` 是必填的服务端密钥，不得提交到 Git、返回给浏览器或
写入日志。`TOKEN_TTL_SECONDS` 默认为 `3600`，允许范围为 1 至 86400 秒。
退出登录会清除浏览器 `sessionStorage`；当前实现没有服务端 token 吊销列表，
已经复制的 token 会在到期前保持有效。

## 知识库切片、检索与问答

上传文字或 UTF-8 `.txt`/`.md` 后，系统保留原文并默认按最多 800 字、
重叠 80 字切片。教师可在页面选择自动、自定义或 Markdown 标题切片方式，
对本班材料重建索引。向量点仅保存切片 ID、材料 ID 和班级等标识字段；
正文与来源保存在 MySQL。
上传成功后页面会自动打开新材料，详情下方直接显示原文；已有的文字、`.txt`
和 `.md` 材料也可点击列表或检索来源预览，同时仍可下载。预览接口
`GET /api/materials/<材料编号>/content` 返回 `material_id` 与 `content`，
必须携带 Bearer token，且只能读取本人所在班级的材料。

课程网关的 `EMBEDDING_BASE_URL` 配到 `/v1`，程序自行调用
`/embeddings`；嵌入模型为 `course-embedding`。`EMBEDDING_DIM=2048` 只
用于建库和校验返回向量，不随嵌入请求发送。对话使用同一网关的
`/chat/completions` 与 `course-chat`；如需单独的地址或密钥，可设置
`CHAT_BASE_URL` 和 `CHAT_API_KEY`。所有密钥只放在服务器的 `.env`，不能
提交到 Git。单次网关请求本地限制为 20 MB。

`GET /api/retrieval?q=<问题>&mode=keyword|vector|hybrid` 检索当前登录用户
所属班级的切片；缺省模式为 `hybrid`。向量相似度低于 0.35 的候选会被
过滤，混合模式按 RRF 排序。每条结果含材料标题、切片编号、字符位置和
来源入口。旧的 `/api/materials/retrieve` 接口暂时保留。
关键词和混合检索还会识别问题中明确出现的完整材料标题（至少 3 个字符）。
因此即使正文很短，提问“某材料的内容是什么”也能定位其已入库切片；
纯向量模式仍执行 0.35 相似度过滤。标题匹配不会跨班级，也不会把整库
正文送给问答模型。

`POST /api/ask` 接收 JSON `{"question":"你的问题"}`。服务器只检索当前
问题，先从有界的混合检索候选中去重并按问题相关性选择证据，再交给
`course-chat`。比较题会保留检索到的各个数值项，例如比较楼宇用电量时同时
保留 150、300 和 40 度的相关切片，不把明显无关的实验背景一起发给对话模型。
比较答案必须引用每个已保留的数值项；只引用胜出项会重试一次，仍遗漏则返回 503。
确实没有证据时返回“资料中未找到相关内容”，不调用对话模型。
若明确询问“某材料的内容／正文／原文是什么”，且检索到该材料完整、较短的
原文，即使对话模型误判为资料不足，系统也会直接引用原文并标明来源。例如
“物理定理材料的内容是什么”可以回答该材料实际保存的文字。这不等同于
“物理定理是什么”：材料名称只是来源信息，若正文没有定义，就不能据此
编造概念解释。
问答响应只返回答案文本实际使用的不重复来源，并按引用首次出现顺序将答案
编号和来源卡片一起重排。上方独立的知识库检索列表仍展示它自己的命中，
不会混入“答案来源”。对话模型漏写、写错来源编号，或答案写出的数字
无法在对应引用切片中找到时，服务端使用相同的有限证据重试一次；仍不合格则
返回 503，不把无依据答案展示给用户。向量库或网关故障时也
返回 503，不生成无依据答案。所有这些接口都要求上面的
Bearer token。

对已有材料补建缺失切片：

```bash
docker compose exec campusclaw python -m flask --app campusclaw backfill-knowledge
```

“重建材料索引”供教师调整已有材料的切片方式，或修复旧材料缺失的检索索引：
系统从保留的原文重新生成切片、更新关键词索引，并重新生成向量索引。
它不修改材料原文，但会调用向量接口，可能产生时间和调用成本。新上传
材料会自动建索引，通常不需要再点击重建；这次模型误判短原文的问题
也不是通过重建索引解决的。


## 本地测试账号

执行 `flask --app campusclaw seed` 可重复创建本地示例数据。账号
`teacher-a`（密码 `teacher-a-password`）是 A 班教师；账号 `student-a`
（密码 `student-a-password`）是 A 班学生；账号 `teacher-b`（密码
`teacher-b-password`）是 B 班教师；账号 `student-b`（密码
`student-b-password`）是 B 班学生。示例还会创建 A、B 两个班级，每班各一条
由本班教师上传的材料记录。

## 验收要点

- 登录返回 JWT，受保护请求使用 `Authorization: Bearer <access_token>`，旧
  Cookie 不能获得授权。
- 教师可上传 `.txt` 或 `.md` 材料，也可直接输入文字；学生只读。
- 文字、`.txt`、`.md` 材料可在详情页直接预览原文，上传后自动打开，下载仍可用。
- 材料列表、切片检索、问答和下载均按登录用户当前数据库班级隔离。
- 关键词、向量和混合检索返回可追溯来源；完整标题提问可定位同班级短材料，
  无证据不调用对话模型。
- 下载中文命名的材料会保留中文名称，并自动补齐 `.txt` 或 `.md` 后缀。

## AI 应用平台

登录后进入 `/apps` 使用写作润色、学习规划、练习生成，选择可管理的提示词模板、内置或上传的 JSON Skill，按需绑定知识库及外部 HTTP/MCP 工具。教师管理本班模板、技能与连接；学生使用；执行记录仅本人可读。Compose 另带内部演示计算器工具服务。

完整说明、技能格式、外部连接配置与真实浏览器测试见 [应用平台使用指南](docs/platform-guide.md)。
