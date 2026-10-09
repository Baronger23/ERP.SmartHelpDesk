# Kiến trúc AI Agent Harness

Phiên bản 3.0 · Thiết kế mục tiêu, chưa có runtime AI triển khai. Giữ 10 module nghiệp vụ; M09 là Knowledge Domain, Harness là lớp điều phối ngang. Single orchestrator là baseline; chưa triển khai delegation hoặc một agent cho mỗi module.

| File | Nội dung cần review |
|---|---|
| [01 · Harness](01_agent_harness_architecture.md) | Component, boundary, baseline và execution limits |
| [02 · Orchestration](02_agent_orchestration_workflow.md) | Lifecycle, transaction, checkpoint/resume, retry và ambiguous outcome |
| [03 · State/memory](03_agent_state_and_memory.md) | AgentDefinition/Run/Step/Checkpoint/Approval, version và memory scope |
| [04 · RAG](04_rag_ingestion_and_retrieval.md) | Ingestion, hybrid retrieval, evidence conflict và freshness |
| [05 · Tool contracts](05_tool_registry_and_contracts.md) | Registry, schema, risk, timeout/retry và idempotency |
| [06 · Planning/execution](06_reasoning_planning_execution.md) | Plan dependencies, bounded loop, observations và replan |
| [07 · Security/HITL](07_security_and_human_approval.md) | Authority, approval binding, stale detection và security boundaries |
| [08 · Observability/evaluation](08_observability_and_evaluation.md) | Trace, test oracles, release gates và offline checker |
| [09 · E2E scenarios](09_end_to_end_agent_scenarios.md) | 8 user story AI, kịch bản success/failure và acceptance |

Nguồn domain: [hợp đồng workflow](../05_domain_workflow_contracts.md). Sơ đồ: [Harness có icon](../diagrams/05_agent_harness.svg); các Mermaid trong tài liệu có bản SVG qua [sổ sơ đồ](../diagrams/index.html).

Artifact máy đọc: [registry](contracts/tool_registry.json), [schemas](contracts/schemas), [fixtures](contracts/fixtures.json), [checker](contracts/validate_contracts.py). Chạy `python docs/design/ai_architecture/contracts/validate_contracts.py` sau cài [dependencies](contracts/requirements.txt).

Checker kiểm tra schema, ví dụ và mô hình protocol offline. Nó không gọi ERP/LLM, không kiểm tra quyền runtime thật hoặc tuyên bố production-ready. Nhãn PASS phải ghi phạm vi; kế hoạch integration/evaluation ở file 08 là việc phải làm khi hiện thực.
