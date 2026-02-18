# Chapter 14: Zero Trust: Trust Nothing, Verify Everything

**Playseat Advanced Field Manual** | **Platform v0.2.0**
**Classification: UNCLASSIFIED** | **218 Crates, 225 Migrations, 1100+ Tables, 212 Routes**

> "The network perimeter is a line drawn on a whiteboard in 2003. The adversary erased it in 2004. We're still pretending it's there in 2026."

---

I was in a meeting last month where a senior executive asked, "If we have a firewall and a VPN, why do we need Zero Trust?" I wanted to show him the SolarWinds timeline. The attackers were inside the network for nine months. Behind the firewall. Connected via VPN, effectively. Every access looked legitimate because they were using legitimate credentials on legitimate systems through legitimate network paths.

The firewall didn't fail. It did exactly what it was designed to do: keep unauthorized traffic out. The problem is that the traffic was authorized. The credentials were valid. The access patterns looked normal -- because the attackers studied what normal looked like and mimicked it perfectly.

Zero Trust says: stop trusting the network. Stop trusting the VPN. Stop trusting the credential. Verify everything, every time, based on multiple factors. And if any factor degrades, revoke access immediately.

This chapter shows you how to implement Zero Trust using Playseat's trust evaluation engine, microsegmentation policies, continuous verification, and device posture integration. We'll walk through a real scenario where a compromised laptop gets detected through trust score degradation before any data is exfiltrated.

---

## 14.1 The Trust Scoring Engine

### How Every Access Gets a Score

Every access request in a Zero Trust architecture goes through the trust evaluation engine. The engine collects multiple signals about the request -- who is asking, from what device, on what network, at what time, for what resource -- and computes a composite trust score.

```bash
# Evaluate trust for a device access request
curl -s -X POST http://localhost:3000/api/v1/zerotrust/evaluations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject_id": "01951d01-aa01-7000-8000-000000000001",
    "subject_type": "device",
    "factors": [
      { "name": "device_posture", "weight": 0.25, "value": 0.95 },
      { "name": "authentication_strength", "weight": 0.25, "value": 0.90 },
      { "name": "network_location", "weight": 0.20, "value": 0.80 },
      { "name": "behavioral_baseline", "weight": 0.20, "value": 0.85 },
      { "name": "time_of_day", "weight": 0.10, "value": 0.90 }
    ]
  }' | jq .
```

**Response:**

```json
{
  "id": "01951d05-bb02-7000-8000-000000000002",
  "subject_id": "01951d01-aa01-7000-8000-000000000001",
  "subject_type": "device",
  "trust_score": "high",
  "composite_value": 0.88,
  "evaluated_at": "2026-02-18T13:00:00Z"
}
```

Let me break down the math. The trust score computation is a weighted average:

```
composite = sum(weight_i * value_i) / sum(weight_i)

= (0.25 * 0.95) + (0.25 * 0.90) + (0.20 * 0.80) + (0.20 * 0.85) + (0.10 * 0.90)
  / (0.25 + 0.25 + 0.20 + 0.20 + 0.10)

= (0.2375 + 0.225 + 0.16 + 0.17 + 0.09) / 1.0

= 0.8825 / 1.0

= 0.8825 --> rounded to 0.88
```

The composite score of 0.88 falls in the "high" trust bracket:

| Score Range | Trust Level | Access Decision |
|-------------|-------------|-----------------|
| >= 0.80     | `high`      | Allow           |
| >= 0.50     | `medium`    | Allow with monitoring |
| >= 0.30     | `low`       | Deny            |
| < 0.30      | `untrusted` | Deny and alert  |

This is the core insight of Zero Trust: access isn't binary. It's a spectrum. A score of 0.88 gets full access. A score of 0.55 gets access with every action logged. A score of 0.20 gets nothing and triggers a security investigation.

### The Trust Factor Breakdown

Each factor in the trust evaluation represents a different signal:

**Device Posture (weight: 0.25)**
Is the device patched? Is EDR running? Is disk encryption enabled? Is the firewall active? Each check contributes to the posture score. A fully compliant device scores 1.0. A device with an expired AV signature scores 0.6. A device with no EDR scores 0.2.

**Authentication Strength (weight: 0.25)**
Password-only: 0.40. Password + SMS: 0.60. Password + TOTP: 0.80. Password + hardware key (FIDO2): 0.95. Certificate-based mutual TLS: 1.0. The stronger the authentication, the higher the trust.

**Network Location (weight: 0.20)**
On-premises wired: 1.0. On-premises wireless: 0.85. Corporate VPN: 0.70. Home network with known IP: 0.50. Public WiFi: 0.20. Tor exit node: 0.0.

**Behavioral Baseline (weight: 0.20)**
How closely does this access pattern match the entity's historical behavior? Same time of day, same resources, same volume? Score 0.95. First time accessing this resource at 3 AM from a new IP? Score 0.20.

**Time of Day (weight: 0.10)**
Normal business hours: 0.90. Extended hours (evening): 0.70. Middle of the night: 0.30. Weekend: 0.50.

---

## 14.2 Access Decisions: Allow, Monitor, or Deny

Once the trust evaluation is complete, the access decision engine determines what happens:

```bash
# Store the evaluation ID
export EVAL_ID="01951d05-bb02-7000-8000-000000000002"

# Make an access decision based on the evaluation
curl -s -X POST http://localhost:3000/api/v1/zerotrust/access/decide \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"evaluation_id\": \"$EVAL_ID\",
    \"resource_id\": \"01951d10-cc03-7000-8000-000000000010\"
  }" | jq .
```

**Response:**

```json
{
  "id": "01951d15-dd04-7000-8000-000000000015",
  "evaluation_id": "01951d05-bb02-7000-8000-000000000002",
  "resource_id": "01951d10-cc03-7000-8000-000000000010",
  "decision": "allow",
  "reason": null,
  "decided_at": "2026-02-18T13:05:00Z"
}
```

For a "high" trust score (0.88), the decision is straightforward: allow access with no additional conditions. Now let's see what happens when the trust degrades:

```bash
# Evaluate trust for a medium-trust scenario
curl -s -X POST http://localhost:3000/api/v1/zerotrust/evaluations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject_id": "01951d01-aa01-7000-8000-000000000001",
    "subject_type": "device",
    "factors": [
      { "name": "device_posture", "weight": 0.25, "value": 0.60 },
      { "name": "authentication_strength", "weight": 0.25, "value": 0.90 },
      { "name": "network_location", "weight": 0.20, "value": 0.40 },
      { "name": "behavioral_baseline", "weight": 0.20, "value": 0.35 },
      { "name": "time_of_day", "weight": 0.10, "value": 0.30 }
    ]
  }' | jq .
```

```json
{
  "id": "01951d20-ee05-7000-8000-000000000020",
  "subject_id": "01951d01-aa01-7000-8000-000000000001",
  "subject_type": "device",
  "trust_score": "medium",
  "composite_value": 0.54,
  "evaluated_at": "2026-02-18T13:10:00Z"
}
```

```bash
# Access decision for medium trust
curl -s -X POST http://localhost:3000/api/v1/zerotrust/access/decide \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "evaluation_id": "01951d20-ee05-7000-8000-000000000020",
    "resource_id": "01951d10-cc03-7000-8000-000000000010"
  }' | jq .
```

```json
{
  "id": "01951d25-ff06-7000-8000-000000000025",
  "evaluation_id": "01951d20-ee05-7000-8000-000000000020",
  "resource_id": "01951d10-cc03-7000-8000-000000000010",
  "decision": "allow_monitored",
  "reason": "Medium trust score requires continuous monitoring",
  "decided_at": "2026-02-18T13:10:30Z"
}
```

The same device, accessing the same resource, but with degraded trust factors. The decision changes from "allow" to "allow_monitored." The device still gets access -- blocking it outright would create friction for a potentially legitimate user -- but every action is now logged at a higher fidelity level, and the SOC receives a notification.

---

## 14.3 Microsegmentation: Dynamic Network Boundaries

Traditional network segmentation is static: VLANs, subnets, firewall rules carved in stone. Microsegmentation is dynamic: segments are defined by policy, and membership changes based on trust scores.

### Creating Segments

```bash
# Create a high-security segment for classified resources
curl -s -X POST http://localhost:3000/api/v1/zerotrust/segments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Classified Systems - SCI",
    "segment_type": "security_boundary"
  }' | jq .
```

```json
{
  "id": "01951d30-aa07-7000-8000-000000000030",
  "name": "Classified Systems - SCI",
  "segment_type": "security_boundary",
  "policy": {},
  "members": [],
  "created_at": "2026-02-18T13:15:00Z",
  "updated_at": "2026-02-18T13:15:00Z"
}
```

```bash
export SEGMENT_ID="01951d30-aa07-7000-8000-000000000030"

# Create additional segments
curl -s -X POST http://localhost:3000/api/v1/zerotrust/segments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "OT/ICS Critical Infrastructure",
    "segment_type": "operational_boundary"
  }' | jq .

curl -s -X POST http://localhost:3000/api/v1/zerotrust/segments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Developer Workstations",
    "segment_type": "workload_boundary"
  }' | jq .
```

### Setting Segment Policies

Policies define the rules for accessing resources within a segment:

```bash
# Set minimum trust score policy
curl -s -X POST "http://localhost:3000/api/v1/zerotrust/segments/$SEGMENT_ID/policy" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "min_trust_score",
    "value": "high"
  }' | jq .

# Require hardware MFA
curl -s -X POST "http://localhost:3000/api/v1/zerotrust/segments/$SEGMENT_ID/policy" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "require_hardware_mfa",
    "value": "true"
  }' | jq .

# Require device posture check
curl -s -X POST "http://localhost:3000/api/v1/zerotrust/segments/$SEGMENT_ID/policy" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "require_device_posture",
    "value": "compliant"
  }' | jq .

# Set re-evaluation interval
curl -s -X POST "http://localhost:3000/api/v1/zerotrust/segments/$SEGMENT_ID/policy" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "key": "reevaluation_interval_minutes",
    "value": "15"
  }' | jq .
```

```json
{
  "policy_set": true,
  "segment_id": "01951d30-aa07-7000-8000-000000000030",
  "key": "reevaluation_interval_minutes",
  "value": "15"
}
```

### Adding Members to a Segment

```bash
# Add a server to the classified segment
curl -s -X POST "http://localhost:3000/api/v1/zerotrust/segments/$SEGMENT_ID/members" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_id": "01951d35-bb08-7000-8000-000000000035",
    "entity_type": "server"
  }' | jq .
```

```json
{
  "added": true,
  "segment_id": "01951d30-aa07-7000-8000-000000000030",
  "entity_id": "01951d35-bb08-7000-8000-000000000035",
  "member_count": 1
}
```

```bash
# Add more members
curl -s -X POST "http://localhost:3000/api/v1/zerotrust/segments/$SEGMENT_ID/members" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_id": "01951d35-bb08-7000-8000-000000000036",
    "entity_type": "database"
  }' | jq .

curl -s -X POST "http://localhost:3000/api/v1/zerotrust/segments/$SEGMENT_ID/members" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "entity_id": "01951d35-bb08-7000-8000-000000000037",
    "entity_type": "application"
  }' | jq .
```

### Viewing Segment Configuration

```bash
# Get the full segment with policy and members
curl -s "http://localhost:3000/api/v1/zerotrust/segments/$SEGMENT_ID" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "id": "01951d30-aa07-7000-8000-000000000030",
  "name": "Classified Systems - SCI",
  "segment_type": "security_boundary",
  "policy": {
    "min_trust_score": "high",
    "require_hardware_mfa": "true",
    "require_device_posture": "compliant",
    "reevaluation_interval_minutes": "15"
  },
  "members": [
    { "entity_id": "01951d35-bb08-7000-8000-000000000035", "entity_type": "server" },
    { "entity_id": "01951d35-bb08-7000-8000-000000000036", "entity_type": "database" },
    { "entity_id": "01951d35-bb08-7000-8000-000000000037", "entity_type": "application" }
  ],
  "created_at": "2026-02-18T13:15:00Z",
  "updated_at": "2026-02-18T13:20:00Z"
}
```

---

## 14.4 Continuous Verification

This is where Zero Trust goes from policy to enforcement. Trust isn't evaluated once at login -- it's re-evaluated continuously throughout the session. Context changes trigger immediate re-evaluation.

### Recording Verification Results

```bash
# Device posture check -- passing
curl -s -X POST http://localhost:3000/api/v1/zerotrust/verifications \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject_id": "01951d01-aa01-7000-8000-000000000001",
    "verification_type": "device_posture",
    "passed": true,
    "details": {
      "os_version": "Windows 11 23H2",
      "patch_level": "2026-02-12",
      "edr_status": "active",
      "edr_signatures": "2026-02-18",
      "disk_encryption": "BitLocker AES-256",
      "firewall": "enabled"
    },
    "next_check_hours": 4
  }' | jq .
```

```json
{
  "id": "01951d40-cc09-7000-8000-000000000040",
  "subject_id": "01951d01-aa01-7000-8000-000000000001",
  "verification_type": "device_posture",
  "result": true,
  "details": {
    "os_version": "Windows 11 23H2",
    "patch_level": "2026-02-12",
    "edr_status": "active",
    "edr_signatures": "2026-02-18",
    "disk_encryption": "BitLocker AES-256",
    "firewall": "enabled"
  },
  "verified_at": "2026-02-18T13:25:00Z",
  "next_check": "2026-02-18T17:25:00Z"
}
```

```bash
# MFA verification -- passing
curl -s -X POST http://localhost:3000/api/v1/zerotrust/verifications \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject_id": "01951d01-aa01-7000-8000-000000000001",
    "verification_type": "mfa_check",
    "passed": true,
    "details": {
      "method": "FIDO2 hardware key",
      "key_model": "YubiKey 5 NFC",
      "last_used": "2026-02-18T13:00:00Z"
    },
    "next_check_hours": 8
  }' | jq .

# Certificate validity check -- passing
curl -s -X POST http://localhost:3000/api/v1/zerotrust/verifications \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject_id": "01951d01-aa01-7000-8000-000000000001",
    "verification_type": "certificate_check",
    "passed": true,
    "details": {
      "cert_subject": "CN=SYNTH-LAPTOP-0042",
      "cert_issuer": "CN=Playseat Internal CA",
      "cert_expiry": "2027-02-18",
      "revocation_status": "valid"
    },
    "next_check_hours": 24
  }' | jq .
```

### Checking What's Due for Verification

```bash
# Find all subjects due for re-verification
curl -s "http://localhost:3000/api/v1/zerotrust/verifications/due" \
  -H "Authorization: Bearer $TOKEN" | jq '[.[] | {
    subject_id,
    verification_type,
    last_result: .result,
    next_check
  }]'
```

```json
[
  {
    "subject_id": "01951d01-aa01-7000-8000-000000000001",
    "verification_type": "device_posture",
    "last_result": true,
    "next_check": "2026-02-18T17:25:00Z"
  }
]
```

### Computing Pass Rates

```bash
# Get verification pass rate for a subject
curl -s "http://localhost:3000/api/v1/zerotrust/verifications/01951d01-aa01-7000-8000-000000000001/rate" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "subject_id": "01951d01-aa01-7000-8000-000000000001",
  "total": 12,
  "passed": 11,
  "failed": 1,
  "pass_rate": 0.917
}
```

A pass rate of 91.7% is good but not perfect. That one failure is worth investigating.

---

## 14.5 Real Scenario: Detecting a Compromised Laptop

Here's the scenario. It's 14:30 on a Tuesday. Analyst Williams' laptop (SYNTH-LAPTOP-0042) has been compromised via a spearphishing email. The attacker has a foothold and is beginning to move laterally. Let's watch how the trust scoring engine detects this.

**14:00 -- Baseline evaluation (normal):**

```bash
# Normal afternoon evaluation
curl -s -X POST http://localhost:3000/api/v1/zerotrust/evaluations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject_id": "01951d01-aa01-7000-8000-000000000001",
    "subject_type": "device",
    "factors": [
      { "name": "device_posture", "weight": 0.25, "value": 0.95 },
      { "name": "authentication_strength", "weight": 0.25, "value": 0.90 },
      { "name": "network_location", "weight": 0.20, "value": 0.80 },
      { "name": "behavioral_baseline", "weight": 0.20, "value": 0.90 },
      { "name": "time_of_day", "weight": 0.10, "value": 0.95 }
    ]
  }' | jq '{trust_score, composite_value}'
```

```json
{ "trust_score": "high", "composite_value": 0.90 }
```

**14:30 -- Compromise occurs (not yet detected).**
The attacker runs a malicious PowerShell script that disables Windows Defender real-time protection.

**14:45 -- Device posture check fires (automated):**

```bash
# Automated posture check detects EDR disruption
curl -s -X POST http://localhost:3000/api/v1/zerotrust/verifications \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject_id": "01951d01-aa01-7000-8000-000000000001",
    "verification_type": "device_posture",
    "passed": false,
    "details": {
      "os_version": "Windows 11 23H2",
      "patch_level": "2026-02-12",
      "edr_status": "DISABLED",
      "edr_signatures": "N/A",
      "disk_encryption": "BitLocker AES-256",
      "firewall": "enabled",
      "alert": "Windows Defender Real-Time Protection disabled at 14:32:00Z"
    },
    "next_check_hours": 1
  }' | jq .
```

The device posture check FAILED. EDR is disabled. This triggers an immediate trust re-evaluation:

**14:46 -- Forced re-evaluation:**

```bash
# Re-evaluate with degraded posture and new behavioral anomalies
curl -s -X POST http://localhost:3000/api/v1/zerotrust/evaluations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject_id": "01951d01-aa01-7000-8000-000000000001",
    "subject_type": "device",
    "factors": [
      { "name": "device_posture", "weight": 0.25, "value": 0.15 },
      { "name": "authentication_strength", "weight": 0.25, "value": 0.90 },
      { "name": "network_location", "weight": 0.20, "value": 0.80 },
      { "name": "behavioral_baseline", "weight": 0.20, "value": 0.30 },
      { "name": "time_of_day", "weight": 0.10, "value": 0.95 }
    ]
  }' | jq '{trust_score, composite_value}'
```

```json
{ "trust_score": "medium", "composite_value": 0.54 }
```

The trust score dropped from 0.90 to 0.54 in 46 minutes. The device posture crashed from 0.95 to 0.15 (EDR disabled), and the behavioral baseline dropped to 0.30 (unusual process execution patterns). The device is now in "allow_monitored" territory.

**15:00 -- Attacker attempts lateral movement:**

The attacker uses stolen credentials to access a file share on a classified systems server. The access request triggers another evaluation:

```bash
# Re-evaluate after suspicious network activity
curl -s -X POST http://localhost:3000/api/v1/zerotrust/evaluations \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "subject_id": "01951d01-aa01-7000-8000-000000000001",
    "subject_type": "device",
    "factors": [
      { "name": "device_posture", "weight": 0.25, "value": 0.10 },
      { "name": "authentication_strength", "weight": 0.25, "value": 0.90 },
      { "name": "network_location", "weight": 0.20, "value": 0.80 },
      { "name": "behavioral_baseline", "weight": 0.20, "value": 0.10 },
      { "name": "time_of_day", "weight": 0.10, "value": 0.95 }
    ]
  }' | jq '{trust_score, composite_value}'
```

```json
{ "trust_score": "low", "composite_value": 0.44 }
```

Trust is now "low" (0.44). The access decision:

```bash
curl -s -X POST http://localhost:3000/api/v1/zerotrust/access/decide \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "evaluation_id": "01951d60-jj12-7000-8000-000000000060",
    "resource_id": "01951d35-bb08-7000-8000-000000000035"
  }' | jq .
```

```json
{
  "id": "01951d65-kk13-7000-8000-000000000065",
  "evaluation_id": "01951d60-jj12-7000-8000-000000000060",
  "resource_id": "01951d35-bb08-7000-8000-000000000035",
  "decision": "deny",
  "reason": "Trust score too low for access",
  "decided_at": "2026-02-18T15:00:30Z"
}
```

**Access denied.** The attacker's lateral movement was blocked because the trust score had degraded below the threshold. The classified systems segment requires "high" trust, but the device is at "low." No access.

This is the power of Zero Trust. The credentials were valid. The network path was legitimate. A traditional firewall would have allowed the access. But the continuous trust evaluation detected the behavioral anomalies and blocked the attacker before any data was accessed.

---

## 14.6 Monitoring Untrusted Subjects

```bash
# List all subjects currently evaluated as untrusted
curl -s "http://localhost:3000/api/v1/zerotrust/evaluations/untrusted" \
  -H "Authorization: Bearer $TOKEN" | jq '[.[] | {
    subject_id,
    subject_type,
    trust_score,
    evaluated_at,
    factors
  }]'
```

```bash
# List all denied access requests
curl -s "http://localhost:3000/api/v1/zerotrust/access/denied" \
  -H "Authorization: Bearer $TOKEN" | jq '[.[] | {
    evaluation_id,
    resource_id,
    decision,
    reason,
    decided_at
  }]'
```

```bash
# List all monitored access requests
curl -s "http://localhost:3000/api/v1/zerotrust/access/monitored" \
  -H "Authorization: Bearer $TOKEN" | jq '[.[] | {
    evaluation_id,
    resource_id,
    decided_at
  }]'
```

---

## 14.7 Zero Trust for OT/ICS Environments

Operational Technology environments need special Zero Trust consideration. You can't just deny access to a PLC controller because a trust score dipped -- that might shut down a physical process with real-world safety implications.

```bash
# Create an OT-specific segment with special policies
curl -s -X POST http://localhost:3000/api/v1/zerotrust/segments \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "OT/ICS Safety-Critical Systems",
    "segment_type": "operational_boundary"
  }' | jq -r '.id'

export OT_SEGMENT_ID="01951d70-aa14-7000-8000-000000000070"

# Set OT-specific policies
curl -s -X POST "http://localhost:3000/api/v1/zerotrust/segments/$OT_SEGMENT_ID/policy" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "key": "min_trust_score", "value": "medium" }' | jq .

curl -s -X POST "http://localhost:3000/api/v1/zerotrust/segments/$OT_SEGMENT_ID/policy" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "key": "deny_action", "value": "alert_only" }' | jq .

curl -s -X POST "http://localhost:3000/api/v1/zerotrust/segments/$OT_SEGMENT_ID/policy" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "key": "require_physical_override", "value": "true" }' | jq .

curl -s -X POST "http://localhost:3000/api/v1/zerotrust/segments/$OT_SEGMENT_ID/policy" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{ "key": "max_session_duration_minutes", "value": "60" }' | jq .
```

Key differences for OT:
- `deny_action: alert_only` -- In OT, automatic access denial could be more dangerous than the threat. Instead of blocking, the system alerts with high priority and lets a human decide.
- `require_physical_override: true` -- Safety-critical changes require someone physically present at the console, not remote access.
- `max_session_duration_minutes: 60` -- Shorter session durations force more frequent re-authentication, limiting the window of opportunity for an attacker.

---

## 14.8 Trust Score Degradation SQL Analysis

To understand trust trends over time and detect systematic issues, use these SQL queries:

```sql
-- Trust score history for a specific subject
SELECT
    te.id,
    te.trust_score,
    te.factors,
    te.evaluated_at,
    te.expires_at
FROM trust_evaluations te
WHERE te.subject_id = '01951d01-aa01-7000-8000-000000000001'
ORDER BY te.evaluated_at DESC;

-- Detect trust score degradation patterns
-- (subjects whose trust dropped by more than one level in 24 hours)
WITH score_ranking AS (
    SELECT
        subject_id,
        subject_type,
        trust_score,
        evaluated_at,
        LAG(trust_score) OVER (
            PARTITION BY subject_id ORDER BY evaluated_at
        ) AS previous_score,
        LAG(evaluated_at) OVER (
            PARTITION BY subject_id ORDER BY evaluated_at
        ) AS previous_eval_time
    FROM trust_evaluations
)
SELECT
    subject_id,
    subject_type,
    previous_score,
    trust_score AS current_score,
    previous_eval_time,
    evaluated_at,
    evaluated_at - previous_eval_time AS time_delta
FROM score_ranking
WHERE previous_score IS NOT NULL
    AND previous_score IN ('high', 'medium')
    AND trust_score IN ('low', 'untrusted')
    AND evaluated_at - previous_eval_time < INTERVAL '24 hours'
ORDER BY evaluated_at DESC;

-- Zero Trust dashboard statistics
SELECT
    trust_score,
    COUNT(*) AS evaluation_count,
    COUNT(DISTINCT subject_id) AS unique_subjects
FROM trust_evaluations
WHERE evaluated_at > NOW() - INTERVAL '24 hours'
GROUP BY trust_score
ORDER BY
    CASE trust_score
        WHEN 'high' THEN 1
        WHEN 'medium' THEN 2
        WHEN 'low' THEN 3
        WHEN 'untrusted' THEN 4
    END;
```

---

## 14.9 Measuring Zero Trust Maturity

Zero Trust isn't a product you buy -- it's a journey you measure. Here's the maturity model we use:

```sql
-- Zero Trust maturity metrics
SELECT
    -- Evaluation coverage: what % of access requests get trust-evaluated?
    (SELECT COUNT(*) FROM trust_evaluations) AS total_evaluations,

    -- Segment coverage: how many segments are defined?
    (SELECT COUNT(*) FROM microsegments) AS total_segments,

    -- Verification frequency: how often are subjects re-verified?
    (SELECT COUNT(*) FROM continuous_verifications
     WHERE verified_at > NOW() - INTERVAL '24 hours') AS verifications_24h,

    -- Denial rate: what % of requests are denied?
    (SELECT COUNT(*) FROM access_decisions
     WHERE decision = 'deny') AS total_denials,

    -- Monitored rate: what % are allowed with monitoring?
    (SELECT COUNT(*) FROM access_decisions
     WHERE decision = 'allow_monitored') AS total_monitored;
```

### The Stats Dashboard

```bash
# Get Zero Trust statistics
curl -s "http://localhost:3000/api/v1/zerotrust/stats" \
  -H "Authorization: Bearer $TOKEN" | jq .
```

```json
{
  "trust_evaluations": 847,
  "untrusted_subjects": 3,
  "access_decisions": 1204,
  "denied_requests": 47,
  "segments": 8,
  "verifications": 2156
}
```

47 denied requests out of 1,204 total -- that's a 3.9% denial rate. In a healthy Zero Trust deployment, you want to see a denial rate between 2-5%. Below 2% suggests your policies are too permissive. Above 10% suggests they're causing excessive friction and users will start finding workarounds.

---

## 14.10 Lessons Learned

**1. Trust score degradation is the detection mechanism.** You don't need to detect the specific attack technique. You need to detect that the trust signals have changed. EDR disabled? Trust drops. Anomalous behavior? Trust drops. New network location? Trust drops. The composite score catches things that individual detections miss.

**2. Microsegmentation is only as good as its policies.** Creating segments without setting meaningful policies is security theater. Every segment needs a minimum trust score, a re-evaluation interval, and specific enforcement actions.

**3. OT/ICS needs a different playbook.** Automatic denial in an OT environment can cause safety incidents. Use "alert_only" for safety-critical systems and always require human approval for access changes.

**4. Continuous verification is the killer feature.** Trust evaluated once at login is barely better than a password. Trust evaluated every 15 minutes is Zero Trust. The re-verification interval should match the sensitivity of the resource.

**5. The pass rate trend is your maturity indicator.** A subject with a 99% pass rate that suddenly drops to 80% is more suspicious than a subject that's always been at 85%. Track the trend, not just the absolute value.

---

## 14.11 Quick Reference

| Operation | Endpoint | Method |
|-----------|----------|--------|
| Evaluate trust | `/api/v1/zerotrust/evaluations` | POST |
| List evaluations | `/api/v1/zerotrust/evaluations` | GET |
| Get evaluation | `/api/v1/zerotrust/evaluations/{id}` | GET |
| Untrusted subjects | `/api/v1/zerotrust/evaluations/untrusted` | GET |
| Decide access | `/api/v1/zerotrust/access/decide` | POST |
| List access records | `/api/v1/zerotrust/access` | GET |
| Denied requests | `/api/v1/zerotrust/access/denied` | GET |
| Monitored requests | `/api/v1/zerotrust/access/monitored` | GET |
| Create segment | `/api/v1/zerotrust/segments` | POST |
| List segments | `/api/v1/zerotrust/segments` | GET |
| Get segment | `/api/v1/zerotrust/segments/{id}` | GET |
| Add member | `/api/v1/zerotrust/segments/{id}/members` | POST |
| Set policy | `/api/v1/zerotrust/segments/{id}/policy` | POST |
| Record verification | `/api/v1/zerotrust/verifications` | POST |
| List verifications | `/api/v1/zerotrust/verifications` | GET |
| Due for check | `/api/v1/zerotrust/verifications/due` | GET |
| Pass rate | `/api/v1/zerotrust/verifications/{subject_id}/rate` | GET |
| Zero Trust stats | `/api/v1/zerotrust/stats` | GET |

---

*Next chapter: AI Pipeline Operations -- making machine learning actually work in production threat detection.*

---

`(c) 2026 Playseat -- All Rights Reserved | Proprietary and Confidential`
