# n8n Node-by-Node Configuration

## Concise Implementation Plan

1. Accept customer requests through an n8n webhook.
2. Normalize missing metadata and validate `raw_message`.
3. Send the message to Groq with a strict JSON-only classification and enrichment prompt.
4. Validate the LLM output against enums and required fields.
5. Retry once when the LLM output is malformed or incomplete.
6. Calculate billing discrepancy in code.
7. Determine the recommended queue in code.
8. Evaluate escalation rules in code.
9. Create the final JSON record and flattened Google Sheets row.
10. Store every record in `All Requests`, store escalations in `Human Review Queue`, and return the final record from the webhook.

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
└── screenshots/
    └── README.md
```

## Workflow Nodes

| Node | Type | Purpose |
| --- | --- | --- |
| `Webhook - Receive Request` | `n8n-nodes-base.webhook` | Receives POST requests and waits for an explicit webhook response. |
| `Normalize Input` | `n8n-nodes-base.code` | Generates missing IDs/timestamps, defaults source, and validates raw message presence. |
| `LLM - Classify and Enrich` | `n8n-nodes-base.httpRequest` | Calls Groq Chat Completions with the strict system prompt and low temperature. |
| `Parse and Validate JSON` | `n8n-nodes-base.code` | Parses model JSON and validates required fields, enums, and confidence range. |
| `IF - LLM Output Valid` | `n8n-nodes-base.if` | Sends valid output forward and invalid output to retry. |
| `Retry Invalid LLM Output` | `n8n-nodes-base.httpRequest` | Performs one repair retry against Groq. |
| `Parse Retry JSON` | `n8n-nodes-base.code` | Validates retry output or creates fallback Human Review data. |
| `Calculate Billing Difference` | `n8n-nodes-base.code` | Computes deterministic billing discrepancy from extracted amounts. |
| `Determine Recommended Queue` | `n8n-nodes-base.code` | Applies deterministic destination queue rules. |
| `Evaluate Escalation Rules` | `n8n-nodes-base.code` | Applies confidence, outage, multi-user, phrase, billing, and validation escalation rules. |
| `Set Final Queue` | `n8n-nodes-base.code` | Routes escalations to Human Review while preserving recommended queue. |
| `Create Final Record` | `n8n-nodes-base.code` | Builds final JSON schema and flattened spreadsheet row. |
| `Google Sheets - Store All Records` | `n8n-nodes-base.googleSheets` | Appends every record to `All Requests`. |
| `IF - Escalated` | `n8n-nodes-base.if` | Sends only escalated records to the human-review sheet. |
| `Google Sheets - Escalation Queue` | `n8n-nodes-base.googleSheets` | Appends escalated records to `Human Review Queue`. |
| `Webhook Response` | `n8n-nodes-base.respondToWebhook` | Returns the completed final JSON record. |

## Required Manual Configuration

- Replace `CONFIGURE_IN_N8N` credential placeholders with real n8n credentials.
- Configure Groq auth as `Authorization: Bearer <GROQ_API_KEY>`.
- Set `GOOGLE_SHEETS_DOCUMENT_ID` in the n8n environment or directly in the Google Sheets nodes.
- Confirm Google Sheets tab names match `All Requests` and `Human Review Queue`.

## Code Nodes

The JavaScript for every Code node is embedded directly in [workflow/arcroute-n8n-workflow.json](../workflow/arcroute-n8n-workflow.json). The important responsibilities are:

- `Normalize Input`: metadata defaults and required-message validation.
- `Parse and Validate JSON` and `Parse Retry JSON`: JSON parsing, enum validation, confidence validation, fallback record generation.
- `Calculate Billing Difference`: deterministic difference calculation using billed and expected amount labels.
- `Determine Recommended Queue`: deterministic queue mapping.
- `Evaluate Escalation Rules`: deterministic escalation reason collection.
- `Set Final Queue`: Human Review override.
- `Create Final Record`: final schema creation and spreadsheet serialization.

## Validation Checklist

- Import workflow JSON into n8n without committing real credentials.
- Run all five sample requests.
- Confirm all five webhook responses are valid JSON.
- Confirm Request 3 billing difference is `$260` and does not trigger the greater-than-$500 rule.
- Confirm Request 5 has `recommended_queue: "Incident Response"` and `final_queue: "Human Review"`.
- Confirm all rows appear in `All Requests`.
- Confirm only escalated rows appear in `Human Review Queue`.
- Confirm malformed LLM output or retry failure creates a fallback Human Review record.
