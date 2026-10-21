# CampusClaw 开发规则

本文件适用于在本仓库工作的所有 AI Coding Agent。

## OpenSpec Apply Workflow

When implementing an OpenSpec task, follow this workflow strictly:

1. Implement only the current OpenSpec task. Do not implement later tasks in advance.
2. Run the exact verification command specified in `openspec/changes/*/tasks.md`.
3. If verification fails:
   - Fix the implementation.
   - Re-run verification.
   - Do not mark the task complete.
   - Do not commit.
4. Only after verification passes:
   - Mark only the current task as completed in `tasks.md`.
   - Run `git status`.
   - Review the changes to ensure they are limited to the current task.
5. Run the verification command once more after all task-related changes are complete.
6. If verification still passes:
   - Stage the task changes with `git add`.
   - Create one Git commit for the completed task.
7. Use a concise commit message describing the task, for example:
   - `feat: add persistence models`
   - `feat: implement login`
   - `test: add authorization coverage`
8. After committing:
   - Run `git status`.
   - Run `openspec list`.
   - Report the completed task, verification result, commit hash, and OpenSpec progress.
9. After reporting the completed task, verification result, commit hash, and OpenSpec progress, automatically continue to the next incomplete task unless the user asks to pause or a task is blocked.
10. When the user explicitly requests delivery to the remote repository, push the current branch only after all requested tasks, full verification, and task commits are complete. Never commit runtime secrets or unrelated working-tree files.


## SDD 工作方式

- 本项目采用 Specification-Driven Development（SDD）。
- 新功能、行为变更或重要调整应先创建或更新相应的 OpenSpec change，再进行实现。
- 后续实现必须以 OpenSpec 中的 Requirements、Scenarios 和 tasks 为依据。
- 需求、设计、实现和测试必须保持一致；变更任一项时，应同步审查并更新相关规约与验证内容。

## 项目阶段与交付口径

- 当前处于个人项目阶段，尚未进入后续合作；报告与项目简介按个人项目表述，不擅自添加小组身份、成员分工或贡献比例。
- 后续合作直接复用个人阶段已经实现并验证的能力，不将这些能力重新列为待开发任务；只针对尚未完成的增量需求新建 OpenSpec change。
- “练习生成应用”不等于题库审核发布、在线测验和自动评分；“应用执行记录”不等于旧问答接口的会话持久化或教师问题反馈。文档必须区分已有基础与未来增量。

## 当前项目状态

- 项目已完成 Docker Compose 可复现启动、JWT Bearer 认证与角色权限、班级隔离、材料管理、浏览器页面和班级范围正文检索等已有 change。认证 token 仅由登录 JSON 返回，浏览器存于 `sessionStorage`，受保护请求必须携带 `Authorization: Bearer <access-token>`；不得恢复 Cookie 登录兼容路径。
- Bearer 认证与可追溯知识库 change 均已完成并归档。知识库包含自动/自定义/标题切片、MySQL 正文索引、Qdrant 向量、关键词/向量/混合检索，以及带编号来源的问答；问答只发送检索出的有限切片，不发送全库正文。
- AI 应用工作台位于 `/apps`，提供写作润色、学习规划、练习生成；模板可保存、编辑、删除并按班级选择。旧 `/materials` 与 `/api/ask` 保持原有知识库问答契约。
- Skill 支持两个内置技能及最多 16 KiB 的 JSON 上传，按 1–3 个模型步骤执行；每步发送完整清单并传递前一步结果，不执行上传脚本。外部工具支持部署配置的 HTTP 和 MCP 2025-06-18 Streamable HTTP，教师按班级启用，用户按次选择，工具结果回填模型。
- 新应用执行记录在 `application_runs` 中保存模型请求/响应、技能步骤和工具结果，仅执行者在其当前班级可访问；不得记录网关凭据或连接密钥。示例工具服务 `demo-tools` 仅在 Compose 内部提供计算器。
- 完整浏览器验收使用 Playwright Chromium。开发环境先安装 `requirements-dev.txt` 并执行 `python -m playwright install chromium`，再运行完整 pytest；报告及证据见 `docs/campusclaw-platform-verification.pdf` 与 `docs/verification/`。
- 新 change 应在全部任务验证通过后，将 delta spec 同步到主规格、运行 `openspec validate --specs`，再归档。部署使用私有 `.env`，不得提交 API 密钥、数据库密码、容器数据或迁移备份。
- 对已有或新建 OpenSpec change，可在用户明确要求 Apply 后按本文件的验证、提交和自动连续执行规则实施。
- 任何新增功能、行为变更或重要修复仍须先创建或更新相应 OpenSpec change；不得跳过规约、验证或任务顺序。

## 范围控制

- 不得擅自扩大需求范围；不明确之处应记录为待澄清项，或先向用户确认。
- 只处理当前 OpenSpec change 明确界定的范围和任务。
