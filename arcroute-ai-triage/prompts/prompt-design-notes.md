# Prompt Design Notes

## Exact System Prompt

See [classification-system-prompt.md](classification-system-prompt.md). The n8n workflow stores the same prompt in the `LLM - Classify and Enrich` HTTP request body.

## Rationale

The output format is strict because every downstream routing and escalation step depends on predictable fields and enum values. Category and priority definitions are included to reduce drift across similar customer messages and to make the LLM's semantic judgment reviewable. Confidence scoring is requested so deterministic code can escalate ambiguous requests without asking the model to make the escalation decision itself. Routing and escalation stay deterministic because queues, outage handling, and billing thresholds are business rules that need auditability and stable behavior. A single combined classification and enrichment call keeps latency and cost low for a technical assessment; splitting classification, extraction, summarization, and risk scoring into separate calls could improve specialization and evaluation coverage, but would add orchestration complexity. With more time, I would add a labeled evaluation set, prompt regression tests, model comparison, human-review feedback capture, and automatic prompt/version rollback.
