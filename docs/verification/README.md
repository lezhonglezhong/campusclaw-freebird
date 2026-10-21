# 个人 AI 应用平台验收证据（2026-10-21）

对应 `../campusclaw-platform-verification.pdf`。当前交付为个人项目；已完成能力直接用于后续增量，不重复建设。运行代码基线为 `6a6f8f1`；验收文档和规格归档随后提交。

## 当前验收

- 全量 `PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider`：226 项通过（原有 168、新增 58），包括真实 Chromium 操作。
- `platform-controlled.json`：10 组受控 HTTP 模型场景全部通过。应用 API 与请求序列化真实执行，HTTP/MCP 为独立实际网络服务，模型返回确定性内容。
- `platform-live-initial.json`：首次真实网关执行，9/10 成功，学习规划 503，记录为请求发出但无网关返回；没有删除此失败证据。
- 将私有部署的 `GATEWAY_TIMEOUT_SECONDS` 从默认 10 调至 30 秒后，`platform-live-retry.json` 中学习规划复测成功；同时以更明确的资料复述问题复核知识绑定，返回“光合作用需要阳光[1]”。无证据分支也通过。
- `platform-live.json`：汇总每场景最新结果，最终 10/10，通过 `retest` 字段链接原始尝试。HTTP/MCP 均由真实模型产生 tool_calls 并完成工具调用，结果为 221。
- `platform-deployment.json`：现有部署健康、登录、新平台接口和材料读接口通过；匿名访问返回 401。应用、MySQL、Qdrant、demo-tools 均 healthy。没有清空数据卷或覆盖私有密钥。
- `workspace.png`：真实 Chromium 交互截图，合成数据和模型替身；不是线上学生资料截图。
- `platform-sample-*`：从真实 JSON 提取的报告代码块与回答内容，保持实际参数/内容。
- 两份主执行 JSON 均包含 33 个运行文件的 SHA-256；`verify_platform_report.py` 对照当前源码校验。

## 重现

```bash
python -m pip install -r requirements-dev.txt
python -m playwright install chromium
PYTHONDONTWRITEBYTECODE=1 python -m pytest -q -p no:cacheprovider
PYTHONDONTWRITEBYTECODE=1 python docs/verification/capture_platform.py > /tmp/platform-controlled.json
docker compose exec -T campusclaw python docs/verification/capture_platform.py --live > /tmp/platform-live.json
PYTHONDONTWRITEBYTECODE=1 python docs/verification/check_platform_deployment.py
PYTHONDONTWRITEBYTECODE=1 python docs/verification/verify_platform_report.py
```

`--live` 实际消耗少量网关额度，但只创建临时 SQLite 和合成材料，不读取生产知识库正文，也不写入生产 MySQL/Qdrant；工具使用内部独立服务。`--case study` 可只重跑该场景（另含无证据分支）。网关调用具备不确定性，失败应保留证据后查明原因，不把失败输出改写成成功。

PDF 构建：

```bash
mkdir -p /tmp/campusclaw-report-build
xelatex -interaction=nonstopmode -halt-on-error -output-directory=/tmp/campusclaw-report-build docs/campusclaw-platform-verification.tex
xelatex -interaction=nonstopmode -halt-on-error -output-directory=/tmp/campusclaw-report-build docs/campusclaw-platform-verification.tex
cp /tmp/campusclaw-report-build/campusclaw-platform-verification.pdf docs/
```

## 原始缺项检查的历史证据

`controlled-requests.json`、`live-gateway.json`、`deployment-checks.json`、`capture_requests.py`、`live_gateway_probe.py` 来自补齐功能前的首次核查，保留用于对照旧 `/api/ask` 与嵌入协议。其 168 项测试基线、旧路由列表和旧源码哈希不能当作本次新增能力的验证结果。当前能力以 `platform-*` 证据和更新报告为准。

## 边界

本次不是高并发压测、全量安全审计或所有第三方 MCP 的兼容性认证。技能是 JSON 声明式模型步骤；MCP 支持 2025-06-18 Streamable HTTP。真实模型知识绑定样本用隔离数据库及受控向量候选；没有将这种隔离验证冒充生产 MySQL/Qdrant 的全链路性能证明。完整轨迹可包含模型附加字段，但不包含用户令牌或模型/工具鉴权头。
