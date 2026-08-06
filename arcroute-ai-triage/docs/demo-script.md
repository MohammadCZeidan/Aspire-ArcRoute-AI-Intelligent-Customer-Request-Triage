# Demo Script

## Five-to-Seven-Minute Walkthrough

1. Introduce ArcVault's intake problem: customer requests arrive through email, web forms, and support portals as unstructured text, and teams need reliable triage without putting business rules entirely inside an LLM.
2. Show the n8n canvas. Walk from `Webhook - Receive Request` through input normalization, Groq classification and enrichment, JSON validation, deterministic routing, escalation evaluation, Google Sheets storage, and webhook response.
3. Open the system prompt. Point out category definitions, priority rules, strict JSON output, confidence scoring, and the instruction that the model should not choose queues.
4. Submit the five sample requests to the webhook. Explain that `request_id` and `received_at` are generated automatically when missing.
5. Show the returned final JSON records. Highlight that each contains the original message, LLM-derived semantic fields, deterministic queue fields, escalation fields, model name, workflow version, and processing timestamp.
6. Focus on Request 5. The LLM identifies an incident, deterministic rules detect `dashboard stopped loading` and `multiple users affected`, and the final queue becomes `Human Review` while preserving `Incident Response` as the recommended queue.
7. Show Google Sheets. The `All Requests` sheet contains every record, while `Human Review Queue` contains only escalated records.
8. Demonstrate error handling by sending a malformed or ambiguous request. Explain schema validation, one retry for invalid LLM output, fallback low-confidence classification, and Human Review routing.
9. Close with production improvements: async queues, idempotency, webhook signatures, PII redaction, prompt versioning, monitoring, dead-letter queues, rate limiting, evaluation datasets, model drift checks, cost tracking, RBAC, and encryption.
