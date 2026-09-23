# CampusClaw 开发规则

本文件适用于在本仓库工作的所有 AI Coding Agent。

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
