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

## 当前项目状态

- 项目已完成 Docker Compose 可复现启动、JWT Bearer 认证与角色权限、班级隔离、材料管理、浏览器页面和班级范围正文检索等已有 change。认证 token 仅由登录 JSON 返回，浏览器存于 `sessionStorage`，受保护请求必须携带 `Authorization: Bearer <access-token>`；不得恢复 Cookie 登录兼容路径。
- 已完成的历史 change 应在 delta spec 同步到主规格并验证后归档；当前活动的 `add-traceable-vector-retrieval` 依赖 Bearer 认证 change 完成。
- 对已有或新建 OpenSpec change，可在用户明确要求 Apply 后按本文件的验证、提交和自动连续执行规则实施。
- 任何新增功能、行为变更或重要修复仍须先创建或更新相应 OpenSpec change；不得跳过规约、验证或任务顺序。

## 范围控制

- 不得擅自扩大需求范围；不明确之处应记录为待澄清项，或先向用户确认。
- 只处理当前 OpenSpec change 明确界定的范围和任务。
