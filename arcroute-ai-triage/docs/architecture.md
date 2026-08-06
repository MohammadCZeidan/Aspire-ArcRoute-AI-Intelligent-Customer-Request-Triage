# Architecture

ArcRoute AI is an n8n workflow that turns unstructured ArcVault customer messages into reviewable structured records. The workflow starts with a webhook, normalizes input fields, calls Groq for classification and enrichment, validates the model response, applies deterministic routing and escalation rules, stores records in Google Sheets, and returns the completed record to the caller.

## Component Flow

Inbound systems such as email processors, web forms, and support portals send JSON to `Webhook - Receive Request`. `Normalize Input` ensures every request has a `request_id`, `source`, `received_at`, and `raw_message`. If `request_id` or `received_at` is missing, the workflow generates them. If `raw_message` is missing, the workflow still creates a fallback record and routes it to Human Review rather than failing silently.

`LLM - Classify and Enrich` sends the normalized message to Groq using a low temperature and a strict system prompt. The model returns semantic fields only: category, priority, confidence, issue summary, identifiers, urgency, impact, follow-up needs, and a human-readable summary. The model is explicitly told not to choose the queue or decide escalation.

`Parse and Validate JSON` parses the LLM response and checks required fields, enum values, and confidence bounds. If validation fails, `Retry Invalid LLM Output` makes one repair attempt. If the retry also fails, the workflow creates a fallback low-confidence record and the deterministic rules route it to Human Review.

## State and Outputs

Google Sheets is the primary persistent store. `Google Sheets - Store All Records` writes every final record to the `All Requests` sheet. `Google Sheets - Escalation Queue` writes only escalated records to the `Human Review Queue` sheet. Nested objects and arrays are serialized as JSON strings so the sheet remains readable without losing structure.

The workflow response also returns the final JSON record. The additional deliverable [output-records.json](../samples/output-records.json) contains the five expected final records for assessment review.

## Why One LLM Call

Classification, extraction, urgency assessment, missing information, and summary generation are combined into one LLM call to keep the assessment clear, cheap, and fast. The tradeoff is that one prompt carries several responsibilities. In production, separate calls or specialized extractors could improve observability and independent evaluation, but would increase latency and orchestration overhead.

## Routing Logic

Routing is deterministic. Bug reports go to Engineering Support, feature requests to Product Management, billing issues to Billing Operations, incidents to Incident Response, and technical questions involving SSO, authentication, Okta, identity, permissions, or security to Identity & Security. Other technical questions go to Engineering Support.

This separation makes the system explainable: the LLM interprets the text, while code applies business rules.

## Escalation Logic

Escalation is also deterministic. A request is routed to Human Review when confidence is below 70, outage or unavailability language appears, multiple or all users are affected, specific escalation phrases are present, billing discrepancy exceeds $500, or LLM validation fails after retry. When escalation happens, `recommended_queue` is preserved and `final_queue` becomes `Human Review`.

Billing discrepancy is calculated from extracted money amounts. The workflow looks for billed and expected labels first, then falls back to the first two extracted amounts when needed.

## Error Handling

The workflow handles missing request IDs, missing timestamps, missing sources, malformed LLM JSON, schema validation failures, LLM timeout or HTTP errors, and incomplete input. It avoids exposing API keys by using n8n environment variables and credential configuration. The final record contains escalation reasons that explain why a request was sent to Human Review.

## Reliability, Latency, Privacy, Security, and Cost

Reliability comes from schema validation, deterministic business rules, fallback routing, and persistent output. Latency is kept low with one Groq call and temperature near zero. Privacy risk is limited by sending only the customer message and metadata needed for triage, though production should add PII redaction before LLM calls. Security relies on n8n credential storage, environment variables, HTTPS webhooks, and optional shared-token validation. Cost is controlled through a single open-source model call per request.

## Production Scale

At production scale, the webhook should enqueue requests rather than processing synchronously. Add idempotency keys based on `request_id`, duplicate prevention, webhook signature verification, PII redaction, prompt and model versioning, monitoring and observability, dead-letter queues, rate limiting, exponential backoff, automated evaluation datasets, human-review feedback loops, model drift monitoring, cost and latency tracking, role-based access control, and encryption in transit and at rest.

## Phase 2

Phase 2 would add customer sentiment detection, SLA prediction, duplicate-ticket detection, retrieval from account data or product documentation, suggested agent responses, multilingual handling, human corrections captured as evaluation data, a dashboard for category distribution and escalation rate, and integrations with Jira, Zendesk, or Slack.
