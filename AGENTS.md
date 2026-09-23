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


## SDD 工作方式

- 本项目采用 Specification-Driven Development（SDD）。
- 新功能、行为变更或重要调整应先创建或更新相应的 OpenSpec change，再进行实现。
- 后续实现必须以 OpenSpec 中的 Requirements、Scenarios 和 tasks 为依据。
- 需求、设计、实现和测试必须保持一致；变更任一项时，应同步审查并更新相关规约与验证内容。

## 当前课程阶段（第 2 课）

- 当前仅进行 OpenSpec 的 Propose + Review，不进行 Apply。
- 未经用户明确要求，不得编写 CampusClaw 业务代码。
- 不得执行 `/opsx-apply`，也不得提前实现任何 CampusClaw 功能。

## 范围控制

- 不得擅自扩大需求范围；不明确之处应记录为待澄清项，或先向用户确认。
- 只处理当前 OpenSpec change 明确界定的范围和任务。
