# CampusClaw

CampusClaw 是“互联网软件技术开发与实践”课程的三人小组学期项目，由 Freebird 小组维护；仓库名为 `campusclaw-freebird`。

## 开发方式

本项目采用 Specification-Driven Development（SDD）。当前阶段通过 OpenSpec 定义 CampusClaw 的需求、设计、验收标准和实施任务。

## Docker Compose 启动

项目推荐使用 Docker Compose 作为可复现启动方式。首次启动会拉取 Dockerfile
中指定的 Python 基础镜像、安装依赖并构建应用；不需要提交 Docker 镜像、容器
或本地数据库到 GitHub。

```bash
cd campusclaw-freebird
SESSION_SECRET='请替换为自己的随机字符串' docker compose up --build -d --wait
SESSION_SECRET='使用同一段随机字符串' docker compose exec campusclaw python -m flask --app campusclaw seed
```

浏览器访问 `http://localhost:8000/login`。部署在本服务器时，访问服务器地址的
`/login`，例如 `http://10.129.165.201:8000/login`。

使用 `docker compose ps` 可确认服务状态为 `healthy`；健康检查地址为
`/health`。后续启动若本地镜像仍在，可使用 `docker compose up -d`。

`SESSION_SECRET` 是登录会话的服务器端密钥，必须自行设置且不得提交到仓库。
`.env.example` 只提供变量示例；`.env`、SQLite 数据库、`instance/` 材料数据、
Docker 镜像和 `__pycache__/` 都不应提交。

> Dockerfile 当前使用 `docker.m.daocloud.io` 的 Python 镜像代理，以适配本服务器
> 无法由 Docker 守护进程直接访问 Docker Hub 的网络环境。其他部署者可按其网络
> 与组织要求替换为可信且可访问的镜像来源。

## 本地测试账号

执行 `flask --app campusclaw seed` 可重复创建本地示例数据。账号
`teacher-a`（密码 `teacher-a-password`）是 A 班教师；账号 `student-a`
（密码 `student-a-password`）是 A 班学生；账号 `teacher-b`（密码
`teacher-b-password`）是 B 班教师；账号 `student-b`（密码
`student-b-password`）是 B 班学生。示例还会创建 A、B 两个班级，每班各一条
由本班教师上传的材料记录。

## 验收要点

- 教师可上传 `.txt` 或 `.md` 材料，也可直接输入文字；学生只读。
- 材料列表、正文检索和下载均按登录用户所属班级隔离。
- 正文检索结果显示材料来源、班级、上传者和匹配片段；中文关键词可检索。
- 下载中文命名的材料会保留中文名称，并自动补齐 `.txt` 或 `.md` 后缀。
