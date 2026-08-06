# ArcRoute AI - Intelligent Customer Request Triage

ArcRoute AI is a technical assessment project for a fictional B2B software company called ArcVault. It uses n8n, Groq, deterministic routing logic, and Google Sheets to convert unstructured customer requests into complete, reviewable JSON records.

## What Is Implemented

- Importable n8n workflow JSON for webhook intake, normalization, Groq classification/enrichment, validation, retry, deterministic routing, deterministic escalation, Google Sheets writes, and webhook response.
- Strict LLM system prompt and retry prompt behavior that keep routing and escalation outside the model.
- Pre-LLM validation branch for missing or empty `raw_message`; invalid input returns a structured error and does not write to Google Sheets.
- Fallback Human Review record when Groq/API output is missing, malformed, or schema-invalid after one retry.
- Google Sheets row preparation nodes with top-level fields matching the documented spreadsheet headers.
- Five sample input requests and five expected sample output records.
- Documentation for architecture, routing, escalation, prompt design, node configuration, and demo recording.
- Standard-library repository validation script.

## What Must Be Configured Manually

- Groq credential in n8n Cloud using the dedicated `Groq` credential type.
- Google Sheets OAuth credential in n8n.
- `GOOGLE_SHEETS_DOCUMENT_ID` or the document ID directly in both Google Sheets nodes.
- Google Sheet tabs named `All Requests` and `Human Review Queue`.
- Optional webhook authentication or signature verification before production use.

The workflow contains placeholders such as `CONFIGURE_IN_N8N`. They are intentional and must not be replaced with real secrets in Git.

## What Requires Live Execution

This repository does not include fake execution evidence. The workflow still needs to be imported into a real n8n instance, connected to real Groq and Google Sheets credentials, and executed against the sample requests.

The records in [samples/output-records.json](samples/output-records.json) are expected sample outputs, not claimed live execution results. After a real run, save actual webhook responses separately or replace the sample file only if you clearly label the replacement as real execution output.

## Technology Stack

- n8n for workflow orchestration.
- Groq API with `openai/gpt-oss-120b` or another available JSON Object Mode capable Groq model.
- n8n Webhook, Code, IF, HTTP Request, Google Sheets, and Respond to Webhook nodes.
- Google Sheets as the persistent review surface.
- Environment variables for API keys and configuration.

## Architecture Summary

Inbound requests hit an n8n webhook, are normalized, validated, classified and enriched by Groq, parsed and schema-checked, routed by deterministic code, evaluated for escalation by deterministic code, written to Google Sheets, and returned as final JSON. The LLM handles semantic understanding. Code handles queue selection, escalation, billing thresholds, invalid input, and fallback behavior.

See [docs/architecture.md](docs/architecture.md), [docs/architecture-diagram.md](docs/architecture-diagram.md), and [docs/n8n-node-by-node-configuration.md](docs/n8n-node-by-node-configuration.md).

## Environment Variables

```bash
GROQ_API_KEY=your_groq_api_key
N8N_WEBHOOK_AUTH_TOKEN=replace_with_shared_secret
GOOGLE_SHEETS_DOCUMENT_ID=replace_with_google_sheet_id
```

The workflow hard-codes `model_name: 'openai/gpt-oss-120b'` and `workflow_version: '1.0.0'` inside the `Normalize Input` node because n8n Cloud does not require local `$env` access for these values.

## Google Sheets Setup

Create one Google Sheet with two tabs:

- `All Requests`
- `Human Review Queue`

Add these exact headers to both tabs:

`Request ID`, `Source`, `Raw message`, `Category`, `Priority`, `Confidence`, `Core issue`, `Identifiers`, `Urgency`, `Recommended queue`, `Final queue`, `Escalation flag`, `Escalation reasons`, `Summary`, `Processed timestamp`

Nested objects and arrays are serialized as JSON strings before writing to cells.

After creating the sheet, configure either:

- `GOOGLE_SHEETS_DOCUMENT_ID` in the n8n runtime environment, or
- the concrete sheet ID directly inside the two Google Sheets nodes.

## Importing the n8n Workflow

1. In n8n, choose `Import from File`.
2. Select [workflow/arcroute-n8n-workflow.json](workflow/arcroute-n8n-workflow.json).
3. Open `LLM - Classify and Enrich` and `Retry Invalid LLM Output`; select your n8n Cloud `Groq` credential. The workflow uses `predefinedCredentialType` with `nodeCredentialType: groqApi`, not generic Header Auth.
4. Open `Google Sheets - Store All Records` and `Google Sheets - Escalation Queue`; configure Google Sheets OAuth and document ID.
5. Confirm the webhook response mode is handled by response nodes.
6. Activate or test the workflow.

Some n8n versions represent response status codes and Google Sheets column mapping slightly differently in exported JSON. If import warns on those fields, keep the same node structure and set the response code or column mapping manually in the n8n UI.

## Running Repository Validation

Run this local static check before submitting:

```bash
python tests/validate_repository.py
```

The script checks workflow JSON validity, unique node names, connection references, sample counts, output schema, valid enums, REQ-003 billing difference, REQ-005 escalation, null arrays, and obvious real-secret patterns.

## Testing the Five Requests

Use [samples/input-requests.json](samples/input-requests.json). Example:

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

Expected high-level results:

- `REQ-001`: Bug Report, Engineering Support.
- `REQ-002`: Feature Request, Product Management.
- `REQ-003`: Billing Issue, Billing Operations; $260 difference, no escalation solely by amount.
- `REQ-004`: Technical Question, Identity & Security.
- `REQ-005`: Incident/Outage, recommended queue Incident Response, final queue Human Review.

## Testing Empty Requests

Submit an empty message:

```bash
curl -X POST "https://YOUR_N8N_HOST/webhook/arcroute-ai-triage" \
  -H "Content-Type: application/json" \
  -d '{"source":"Email","raw_message":""}'
```

Expected behavior:

- Groq is not called.
- Google Sheets is not written.
- The webhook returns a structured error with `request_id`, `source`, `received_at`, `error`, and `validation_errors`.
- HTTP status should be 400 when supported by the imported Respond to Webhook node settings.

## Testing Billing Escalation Over $500

Submit a billing discrepancy above $500:

```bash
curl -X POST "https://YOUR_N8N_HOST/webhook/arcroute-ai-triage" \
  -H "Content-Type: application/json" \
  -d '{
    "source": "Support Portal",
    "raw_message": "Invoice #9910 shows a charge of $1,850 but our contract rate is $980/month. Please review."
  }'
```

Expected behavior:

- Category should be Billing Issue.
- Recommended queue should be Billing Operations.
- Escalation should be true if both amounts are extracted and the deterministic difference exceeds $500.
- Final queue should be Human Review.

## Expected Output Records

[samples/output-records.json](samples/output-records.json) contains prepared expected outputs for assessment review. These are not hard-coded into the workflow and are not claimed to be real execution results.

To replace them with real execution results:

1. Run all five requests through the configured n8n workflow.
2. Save each webhook response exactly as returned.
3. Replace or add a clearly named file such as `samples/live-output-records.json`.
4. Keep secrets, private URLs, and sensitive customer data out of committed files.

## Placeholders

Use these placeholders until real submission assets exist:

- `ADD_LOOM_LINK_AFTER_RECORDING`
- `ADD_VIEW_ONLY_GOOGLE_SHEET_LINK`
- `CONFIGURE_IN_N8N`

Do not invent fake screenshots, fake Google Sheet links, fake Loom links, or fake n8n execution IDs.

## Limitations

- Static validation can confirm JSON structure and repository consistency, but it cannot guarantee a specific n8n instance will import every option without UI adjustment.
- Live Groq and Google Sheets behavior requires configured credentials.
- PII redaction, webhook signatures, async queues, and durable idempotency are documented production improvements rather than fully implemented in this assessment workflow.

## Future Improvements

- Queue-based async processing.
- Webhook signature verification and idempotency storage.
- PII redaction before LLM calls.
- Automated evaluation datasets and prompt regression tests.
- Human-review feedback loops.
- Jira, Zendesk, and Slack integrations.
- Monitoring for model drift, latency, and cost.

## Final Manual Submission Steps

1. Import the workflow into n8n.
2. Configure Groq and Google Sheets credentials.
3. Connect the Google Sheet with the required tabs and headers.
4. Run the five sample requests.
5. Save actual webhook outputs, clearly labelled as live execution results.
6. Capture screenshots of the workflow canvas, webhook execution, All Requests sheet, and Human Review Queue sheet.
7. Record the Loom demonstration using [docs/demo-script.md](docs/demo-script.md).
8. Add the Loom link and view-only Google Sheet link.
9. Verify no secrets, credentials, private tokens, or sensitive runtime outputs are committed.

## Validation Checklist

- [x] Required folder structure exists.
- [x] Five input requests are included.
- [x] Five complete expected output records are included.
- [x] Prompt defines categories, priorities, schema, confidence, and no-invention rules.
- [x] Invalid empty input is branched before Groq.
- [x] Routing and escalation are deterministic.
- [x] Billing discrepancy threshold is deterministic and Request 3 is not escalated solely by amount.
- [x] Request 5 routes to Human Review while preserving Incident Response as recommended queue.
- [x] `.env.example` avoids hard-coded secrets.
- [x] `.gitignore` excludes local secrets and temporary files.
- [x] Google Sheets tabs and columns are documented.
- [x] Workflow JSON marks instance-specific credentials and document ID for manual configuration.
- [x] Static repository validation script is included.
