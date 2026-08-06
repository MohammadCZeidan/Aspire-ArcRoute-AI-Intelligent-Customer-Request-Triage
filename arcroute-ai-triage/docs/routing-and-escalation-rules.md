# Routing and Escalation Rules

## Recommended Queue

The LLM returns category, priority, confidence, and extracted facts. It does not decide the queue.

| Condition | Recommended queue |
| --- | --- |
| Bug Report | Engineering Support |
| Feature Request | Product Management |
| Billing Issue | Billing Operations |
| Incident/Outage | Incident Response |
| Technical Question with SSO, authentication, Okta, identity, permissions, or security evidence | Identity & Security |
| Other Technical Question | Engineering Support |

## Escalation

`escalation_flag` becomes `true` when any rule matches:

- Confidence score is below 70.
- The message indicates service outage or widespread unavailability.
- Multiple users or all users are affected.
- The message contains phrases such as `outage`, `down for all users`, `dashboard stopped loading`, `multiple users affected`, or `service unavailable`.
- A billing discrepancy is greater than $500 after deterministic calculation.
- The LLM output is invalid, incomplete, or fails schema validation after one retry.

When escalation is true, `recommended_queue` is preserved and `final_queue` becomes `Human Review`.

## Billing Difference

The workflow calculates billing difference only when it can find both a billed amount and expected amount in `identifiers.amounts`. If labels are unavailable, the code uses the first two amounts in the message as a fallback. The Request 3 discrepancy is `$1,240 - $980 = $260`, so it does not escalate under the greater-than-$500 rule.
