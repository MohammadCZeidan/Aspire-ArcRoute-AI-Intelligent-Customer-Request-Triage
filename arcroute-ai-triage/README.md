# ArcRoute AI - Intelligent Customer Request Triage

ArcRoute AI is a technical assessment project for a fictional B2B software company called ArcVault. It uses n8n, Groq, deterministic routing logic, and Google Sheets to convert unstructured customer requests into complete, reviewable JSON records.

## Features

- Webhook intake for email, web form, and support portal requests.
- Automatic `request_id` and `received_at` generation when absent.
- Groq LLM classification and enrichment with strict JSON output.
- Schema validation and one automatic retry for malformed LLM output.
- Deterministic queue routing and escalation logic outside the LLM.
- Billing discrepancy calculation when billed and expected amounts are available.
- Google Sheets persistence for all requests and human-review records.
- Sample inputs, expected outputs, prompt docs, architecture docs, and demo script.

## Technology Stack

- n8n for workflow orchestration.
- Groq API with `llama-3.3-70b-versatile` or another available open-source Groq model.
- n8n Code, IF, HTTP Request, Google Sheets, and Respond to Webhook nodes.
- Google Sheets as the persistent review surface.
- Environment variables for API keys and configuration.

## Architecture Summary

Inbound requests hit an n8n webhook, are normalized, classified and enriched by Groq, validated, routed by deterministic code, evaluated for escalation, written to Google Sheets, and returned as final JSON. The LLM handles semantic understanding. Code handles queue selection, escalation, billing thresholds, and fallback behavior.

See [docs/architecture.md](docs/architecture.md) and [docs/architecture-diagram.md](docs/architecture-diagram.md).

## Setup

1. Create a free Groq account and API key.
2. Create a Google Sheet with two tabs: `All Requests` and `Human Review Queue`.
3. Add these columns to both tabs:

   `Request ID`, `Source`, `Raw message`, `Category`, `Priority`, `Confidence`, `Core issue`, `Identifiers`, `Urgency`, `Recommended queue`, `Final queue`, `Escalation flag`, `Escalation reasons`, `Summary`, `Processed timestamp`

4. Copy `.env.example` into your n8n environment configuration.
5. Configure Google Sheets OAuth credentials in n8n.
6. Import [workflow/arcroute-n8n-workflow.json](workflow/arcroute-n8n-workflow.json).
7. Open the imported workflow and manually set:

   - Groq API credential or `GROQ_API_KEY` environment variable.
   - Google Sheets credential.
   - Google Sheets document ID.
   - Production webhook path or auth token, if desired.

## Environment Variables

```bash
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.3-70b-versatile
WORKFLOW_VERSION=1.0.0
N8N_WEBHOOK_AUTH_TOKEN=replace_with_shared_secret
GOOGLE_SHEETS_DOCUMENT_ID=replace_with_google_sheet_id
```

## Importing the n8n Workflow

In n8n, choose `Import from File` and select `workflow/arcroute-n8n-workflow.json`. The workflow uses valid n8n node types, but credential IDs and the Google Sheets document ID are intentionally placeholders. Configure them manually in your n8n instance.

## Submitting Test Requests

Use the records in [samples/input-requests.json](samples/input-requests.json). Example:

```bash
curl -X POST "https://YOUR_N8N_HOST/webhook/arcroute-ai-triage" \
  -H "Content-Type: application/json" \
  -d '{
    "request_id": "REQ-001",
    "source": "Email",
    "received_at": "2026-08-06T10:00:00Z",
    "raw_message": "Hi, I tried logging in this morning and keep getting a 403 error. My account is arcvault.io/user/jsmith. This started after your update last Tuesday."
  }'
```

## Expected Output

The webhook returns a complete final record with category, priority, confidence, extracted identifiers, urgency, customer impact, follow-up requirements, `recommended_queue`, `final_queue`, escalation details, summary, model name, workflow version, and `processed_at`.

The five expected output records are in [samples/output-records.json](samples/output-records.json).

## Limitations

- The workflow JSON is ready to import, but Google Sheets credentials and document ID must be configured per n8n instance.
- The sample output records are expected results, not hard-coded workflow responses.
- The assessment does not include a live n8n server, a live Google Sheet, or screenshots generated from a local execution.
- PII redaction, webhook signatures, and async queues are described as production improvements rather than fully implemented in this assessment workflow.

## Future Improvements

- Queue-based async processing.
- Webhook signature verification and idempotency storage.
- PII redaction before LLM calls.
- Automated evaluation datasets and prompt regression tests.
- Human-review feedback loops.
- Jira, Zendesk, and Slack integrations.
- Monitoring for model drift, latency, and cost.

## Validation Checklist

- [x] Required folder structure exists.
- [x] Five input requests are included.
- [x] Five complete expected output records are included.
- [x] Prompt defines categories, priorities, schema, confidence, and no-invention rules.
- [x] Routing and escalation are documented as deterministic.
- [x] Billing discrepancy threshold is deterministic and Request 3 is not escalated solely by amount.
- [x] Request 5 routes to Human Review while preserving Incident Response as recommended queue.
- [x] `.env.example` avoids hard-coded secrets.
- [x] Google Sheets tabs and columns are documented.
- [x] Workflow JSON marks instance-specific credentials and document ID for manual configuration.
