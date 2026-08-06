import json
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

CATEGORIES = {"Bug Report", "Feature Request", "Billing Issue", "Technical Question", "Incident/Outage"}
PRIORITIES = {"Low", "Medium", "High"}
URGENCY = {"None", "Low", "Medium", "High"}
QUEUES = {
    "Engineering Support",
    "Product Management",
    "Billing Operations",
    "Identity & Security",
    "Incident Response",
    "Human Review",
}
SECRET_PATTERNS = [
    re.compile(r"gsk_[A-Za-z0-9_-]{20,}"),
    re.compile(r"gh[opsu]_[A-Za-z0-9_]{20,}"),
    re.compile(r"AIza[0-9A-Za-z_-]{20,}"),
]


def fail(message):
    raise AssertionError(message)


def read_json(path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def assert_string_or_null(value, field):
    if value is not None and not isinstance(value, str):
        fail(f"{field} must be string or null")


def validate_amounts(amounts, request_id):
    if not isinstance(amounts, list):
        fail(f"{request_id}: identifiers.amounts must be an array")
    for index, amount in enumerate(amounts):
        if not isinstance(amount, dict):
            fail(f"{request_id}: amount {index} must be an object")
        if not isinstance(amount.get("label"), str) or not amount["label"].strip():
            fail(f"{request_id}: amount {index} needs a usable label")
        if not isinstance(amount.get("value"), (int, float)):
            fail(f"{request_id}: amount {index} needs a numeric value")


def validate_record(record):
    request_id = record.get("request_id", "<missing>")
    required = [
        "request_id",
        "source",
        "received_at",
        "raw_message",
        "category",
        "priority",
        "confidence_score",
        "core_issue",
        "identifiers",
        "urgency_signal",
        "urgency_reason",
        "customer_impact",
        "requires_follow_up_information",
        "missing_information",
        "recommended_queue",
        "final_queue",
        "escalation_flag",
        "escalation_reasons",
        "human_readable_summary",
        "model_name",
        "workflow_version",
        "processed_at",
    ]
    for field in required:
        if field not in record:
            fail(f"{request_id}: missing {field}")

    if record["category"] not in CATEGORIES:
        fail(f"{request_id}: invalid category")
    if record["priority"] not in PRIORITIES:
        fail(f"{request_id}: invalid priority")
    if record["urgency_signal"] not in URGENCY:
        fail(f"{request_id}: invalid urgency")
    if record["recommended_queue"] not in QUEUES:
        fail(f"{request_id}: invalid recommended queue")
    if record["final_queue"] not in QUEUES:
        fail(f"{request_id}: invalid final queue")
    if not isinstance(record["confidence_score"], int) or not 0 <= record["confidence_score"] <= 100:
        fail(f"{request_id}: confidence_score must be integer 0-100")
    for field in ["core_issue", "urgency_reason", "customer_impact", "human_readable_summary"]:
        if not isinstance(record[field], str) or not record[field].strip():
            fail(f"{request_id}: {field} must be a non-empty string")
    if not isinstance(record["requires_follow_up_information"], bool):
        fail(f"{request_id}: requires_follow_up_information must be boolean")
    if not isinstance(record["missing_information"], list):
        fail(f"{request_id}: missing_information must be an array")
    if not isinstance(record["escalation_flag"], bool):
        fail(f"{request_id}: escalation_flag must be boolean")
    if not isinstance(record["escalation_reasons"], list):
        fail(f"{request_id}: escalation_reasons must be an array")

    identifiers = record["identifiers"]
    if not isinstance(identifiers, dict):
        fail(f"{request_id}: identifiers must be an object")
    assert_string_or_null(identifiers.get("account_reference"), f"{request_id}: account_reference")
    assert_string_or_null(identifiers.get("invoice_number"), f"{request_id}: invoice_number")
    assert_string_or_null(identifiers.get("error_code"), f"{request_id}: error_code")
    validate_amounts(identifiers.get("amounts"), request_id)
    if not isinstance(identifiers.get("time_references"), list):
        fail(f"{request_id}: identifiers.time_references must be an array")
    assert_string_or_null(identifiers.get("authentication_provider"), f"{request_id}: authentication_provider")
    affected_users = identifiers.get("affected_users")
    if affected_users is not None and not isinstance(affected_users, (str, int, float)):
        fail(f"{request_id}: affected_users must be string, number, or null")


def validate_workflow():
    workflow = read_json(ROOT / "workflow" / "arcroute-n8n-workflow.json")
    nodes = workflow.get("nodes", [])
    names = [node.get("name") for node in nodes]
    if len(names) != len(set(names)):
        fail("Workflow node names must be unique")
    known = set(names)
    for source, outputs in workflow.get("connections", {}).items():
        if source not in known:
            fail(f"Connection source references missing node: {source}")
        for output_group in outputs.get("main", []):
            for connection in output_group:
                target = connection.get("node")
                if target not in known:
                    fail(f"Connection target references missing node: {target}")
    return workflow


def validate_no_real_secrets():
    for path in ROOT.rglob("*"):
        if not path.is_file() or ".git" in path.parts:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                fail(f"Potential real secret found in {path.relative_to(ROOT)}")


def main():
    validate_workflow()
    validate_no_real_secrets()

    inputs = read_json(ROOT / "samples" / "input-requests.json")
    outputs = read_json(ROOT / "samples" / "output-records.json")
    if len(inputs) != 5:
        fail("Expected five sample inputs")
    if len(outputs) != 5:
        fail("Expected five sample outputs")

    for record in outputs:
        validate_record(record)

    by_id = {record["request_id"]: record for record in outputs}
    req3_amounts = by_id["REQ-003"]["identifiers"]["amounts"]
    values = {amount["label"]: amount["value"] for amount in req3_amounts}
    difference = abs(values["billed_amount"] - values["expected_amount"])
    if difference != 260:
        fail("REQ-003 billing difference should be 260")
    if by_id["REQ-003"]["escalation_flag"]:
        fail("REQ-003 should not be escalated solely by billing amount")
    if by_id["REQ-005"]["recommended_queue"] != "Incident Response":
        fail("REQ-005 recommended queue should be Incident Response")
    if by_id["REQ-005"]["final_queue"] != "Human Review" or not by_id["REQ-005"]["escalation_flag"]:
        fail("REQ-005 should escalate to Human Review")

    print("Repository validation passed.")


if __name__ == "__main__":
    main()
