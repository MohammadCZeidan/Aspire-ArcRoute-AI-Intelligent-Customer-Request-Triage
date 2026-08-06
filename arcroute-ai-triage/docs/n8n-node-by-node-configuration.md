# n8n Node-by-Node Configuration

## Concise Implementation Plan

1. Accept customer requests through an n8n webhook.
2. Normalize missing metadata and validate `raw_message`.
3. Branch invalid input before Groq and return a structured 400-style error response.
4. Send valid messages to Groq with a strict JSON-only classification and enrichment prompt.
5. Validate the LLM output against required fields, nested identifier types, enums, and confidence bounds.
6. Retry once when the LLM output is malformed, incomplete, or schema-invalid.
7. Create a fallback low-confidence record when both LLM attempts fail.
8. Calculate billing discrepancy in code.
9. Determine the recommended queue in code.
10. Evaluate escalation rules in code.
11. Create the final JSON record.
12. Prepare top-level Google Sheets rows, store every valid processed request in `All Requests`, store escalations in `Human Review Queue`, and return the final record from the webhook.

## Final Project Folder Structure

```text
arcroute-ai-triage/
├── README.md
├── .env.example
├── workflow/
│   └── arcroute-n8n-workflow.json
├── prompts/
│   ├── classification-system-prompt.md
│   └── prompt-design-notes.md
├── samples/
│   ├── input-requests.json
│   └── output-records.json
├── docs/
│   ├── architecture.md
│   ├── architecture-diagram.md
│   ├── routing-and-escalation-rules.md
│   ├── n8n-node-by-node-configuration.md
│   └── demo-script.md
├── screenshots/
│   └── README.md
└── tests/
    └── validate_repository.py
```

## Workflow Nodes

| Node | Type | Purpose |
| --- | --- | --- |
| `Webhook - Receive Request` | `n8n-nodes-base.webhook` | Receives POST requests and waits for an explicit webhook response. |
| `Normalize Input` | `n8n-nodes-base.code` | Generates missing IDs/timestamps, defaults source, and validates raw message presence. |
| `IF - Input Valid` | `n8n-nodes-base.if` | Prevents missing or empty `raw_message` from calling Groq or writing to Google Sheets. |
| `Create Validation Error Response` | `n8n-nodes-base.code` | Creates structured invalid-input response data. |
| `Respond Invalid Request` | `n8n-nodes-base.respondToWebhook` | Returns invalid input as JSON with status 400 when supported by the imported n8n version. |
| `LLM - Classify and Enrich` | `n8n-nodes-base.httpRequest` | Calls Groq Chat Completions with the strict system prompt and low temperature. |
| `Parse and Validate JSON` | `n8n-nodes-base.code` | Parses model JSON and validates top-level and nested fields. |
| `IF - LLM Output Valid` | `n8n-nodes-base.if` | Sends valid output forward and invalid output to retry. |
| `Retry Invalid LLM Output` | `n8n-nodes-base.httpRequest` | Performs one repair retry against Groq with the full schema and previous validation errors. |
| `Parse Retry JSON` | `n8n-nodes-base.code` | Validates retry output or creates fallback Human Review data. |
| `Calculate Billing Difference` | `n8n-nodes-base.code` | Computes deterministic billing discrepancy from extracted amounts. |
| `Determine Recommended Queue` | `n8n-nodes-base.code` | Applies deterministic destination queue rules. |
| `Evaluate Escalation Rules` | `n8n-nodes-base.code` | Applies confidence, outage, multi-user, phrase, billing, and validation escalation rules. |
| `Set Final Queue` | `n8n-nodes-base.code` | Routes escalations to Human Review while preserving recommended queue. |
| `Create Final Record` | `n8n-nodes-base.code` | Builds the final JSON schema. |
| `Prepare All Requests Sheet Row` | `n8n-nodes-base.code` | Emits top-level fields matching exact spreadsheet headers. |
| `Google Sheets - Store All Records` | `n8n-nodes-base.googleSheets` | Appends every valid processed request to `All Requests`. |
| `IF - Escalated` | `n8n-nodes-base.if` | Sends only escalated records to the human-review sheet. |
| `Prepare Human Review Sheet Row` | `n8n-nodes-base.code` | Emits top-level fields matching exact Human Review Queue headers. |
| `Google Sheets - Escalation Queue` | `n8n-nodes-base.googleSheets` | Appends escalated records to `Human Review Queue`. |
| `Webhook Response` | `n8n-nodes-base.respondToWebhook` | Returns the completed final JSON record, not the Google Sheets node output. |

## Required Manual Configuration

- Replace `CONFIGURE_IN_N8N` credential placeholders with real n8n credentials.
- Configure Groq auth as `Authorization: Bearer <GROQ_API_KEY>`.
- Set `GOOGLE_SHEETS_DOCUMENT_ID` in the n8n environment or directly in the Google Sheets nodes.
- Confirm Google Sheets tab names match `All Requests` and `Human Review Queue`.
- If your n8n version imports response-code options differently, set the invalid-request response to 400 manually in the UI.

## Code Nodes

The JavaScript for every Code node is embedded directly in [workflow/arcroute-n8n-workflow.json](../workflow/arcroute-n8n-workflow.json). The important responsibilities are:

- `Normalize Input`: metadata defaults and required-message validation.
- `Create Validation Error Response`: structured invalid input response.
- `Parse and Validate JSON` and `Parse Retry JSON`: JSON parsing, nested field validation, safe normalization, and fallback record generation.
- `Calculate Billing Difference`: deterministic difference calculation using billed and expected amount labels.
- `Determine Recommended Queue`: deterministic queue mapping.
- `Evaluate Escalation Rules`: deterministic escalation reason collection.
- `Set Final Queue`: Human Review override.
- `Create Final Record`: final schema creation.
- `Prepare All Requests Sheet Row` and `Prepare Human Review Sheet Row`: spreadsheet serialization.

## Validation Checklist

- Run `python tests/validate_repository.py`.
- Import workflow JSON into n8n without committing real credentials.
- Run all five sample requests.
- Confirm all five webhook responses are valid JSON.
- Confirm empty `raw_message` returns an error and does not call Groq or write sheets.
- Confirm Request 3 billing difference is `$260` and does not trigger the greater-than-$500 rule.
- Confirm Request 5 has `recommended_queue: "Incident Response"` and `final_queue: "Human Review"`.
- Confirm all valid processed rows appear in `All Requests`.
- Confirm only escalated rows appear in `Human Review Queue`.
- Confirm malformed LLM output or retry failure creates a fallback Human Review record.
