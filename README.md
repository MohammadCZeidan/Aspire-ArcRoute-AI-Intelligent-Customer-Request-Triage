# ArcRoute AI - Intelligent Customer Request Triage

ArcRoute AI is a technical assessment project for a fictional B2B software company, ArcVault. It demonstrates an end-to-end AI-assisted intake workflow that receives unstructured customer requests, classifies and enriches them with an LLM, applies deterministic routing and escalation rules, stores reviewable records in Google Sheets, and returns a structured JSON response.

The implementation lives in [`arcroute-ai-triage/`](arcroute-ai-triage/).

## What This Project Includes

- An importable n8n workflow export.
- Groq-based classification and enrichment using `openai/gpt-oss-120b`.
- Strict JSON output expectations for the LLM.
- Deterministic queue routing outside the LLM.
- Deterministic human-escalation rules outside the LLM.
- Google Sheets persistence for all requests and escalations.
- Five sample input requests and expected sample output records.
- Prompt, architecture, routing, escalation, demo, and validation documentation.
- A standard-library validation script for repository consistency checks.

## Architecture

```text
Webhook
  -> Normalize Input
  -> Groq Classification and Enrichment
  -> JSON Validation and Retry
  -> Deterministic Routing
  -> Deterministic Escalation
  -> Final JSON Record
  -> Google Sheets
  -> Webhook Response
```

The LLM is used for semantic understanding only. It does not choose the final queue and does not set the escalation flag.

## Repository Structure

```text
arcroute-ai-triage/
├── README.md
├── .env.example
├── workflow/
│   └── arcroute-n8n-workflow.json
├── prompts/
├── samples/
├── docs/
├── screenshots/
└── tests/
    └── validate_repository.py
```

## Quick Validation

From the repository root:

```bash
cd arcroute-ai-triage
python tests/validate_repository.py
```

The validator checks workflow JSON, node references, sample schemas, model configuration, routing expectations, billing discrepancy behavior, outage escalation, and obvious committed-secret patterns.

## Manual Configuration Required

This repository does not contain live credentials or fake execution artifacts. To run the workflow, configure these in n8n:

- Groq API credential.
- Google Sheets OAuth credential.
- Google Sheets document ID.
- `All Requests` and `Human Review Queue` sheet tabs with the documented headers.

See [`arcroute-ai-triage/README.md`](arcroute-ai-triage/README.md) for full setup, testing, and final submission instructions.

## Honesty Note

The sample outputs are expected records for assessment review. They are not claimed to be live n8n execution results. Real webhook outputs, screenshots, Google Sheet links, and a Loom recording should be added only after the workflow is configured and executed in a real environment.
