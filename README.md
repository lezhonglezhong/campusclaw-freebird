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
问题，最多取 4 个相关切片交给 `course-chat`，返回带 `[1]` 等编号的答案
及对应来源。确实没有证据时返回“资料中未找到相关内容”，不调用对话模型。
对话模型漏写或写错来源编号时，服务端使用相同的有限证据重试一次；仍无法
产生合规引用则返回 503，不把无来源答案展示给用户。向量库或网关故障时也
返回 503，不生成无依据答案。所有这些接口都要求上面的
Bearer token。

对已有材料补建缺失切片：

```bash
docker compose exec campusclaw python -m flask --app campusclaw backfill-knowledge
```


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
