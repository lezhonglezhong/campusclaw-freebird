# CampusClaw

CampusClaw 是“互联网软件技术开发与实践”课程的三人小组学期项目，由 Freebird 小组维护；仓库名为 `campusclaw-freebird`。

## 开发方式

本项目采用 Specification-Driven Development（SDD）。当前阶段通过 OpenSpec 定义 CampusClaw 的需求、设计、验收标准和实施任务。

## Docker Compose 启动

项目推荐使用 Docker Compose 作为可复现启动方式。首次启动会拉取基础镜像、
安装依赖并构建应用。

```bash
cd campusclaw-freebird
cp .env.example .env
# 编辑 .env，为 TOKEN_SIGNING_SECRET 设置不可提交的随机值。
docker compose up --build -d --wait
docker compose exec campusclaw python -m flask --app campusclaw seed
```

浏览器访问 `http://localhost:8000/login`。

使用 `docker compose ps` 可确认服务状态为 `healthy`；健康检查地址为
`/health`。后续启动若本地镜像仍在，可使用 `docker compose up -d`。

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
- 材料列表、正文检索和下载均按登录用户所属班级隔离。
- 正文检索结果显示材料来源、班级、上传者和匹配片段；中文关键词可检索。
- 下载中文命名的材料会保留中文名称，并自动补齐 `.txt` 或 `.md` 后缀。
