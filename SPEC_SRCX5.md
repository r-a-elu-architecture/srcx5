# SRC-X.5, specification v1.3

An open record of sealed claims, verified at the source.

**Status:** v1.3, 26 November 2026 (renames v1.2, "RSOS Sealed Claims"; rules unchanged, see §0). Text CC BY 4.0; reference code Apache 2.0.
**Reference implementation:** `srcx5.py` (node, command-line tool and sync in one file, Python standard library only).

## 0. Name and versions
- **Name:** SRC-X.5. Written `srcx5` where punctuation cannot go (file, package, repository). It was first written on
  8 June 2025 for a compact key that re-expands into its full content; a record's id is exactly that.
- **v1.3 changes the name only.** Every rule, check and threshold is the same as v1.2. The version field is now
  `srcx5`; a v1.3 node also admits records carrying `rsc: "1.2"`, so the genesis log keeps every id and its chain.
- **v1.2** (`rsc.py`, sealed in `tests/SEAL_RSC.txt`) is kept unchanged as the reference that made the genesis log.

## 1. Purpose
A claim is easy to make and hard to check. An SRC-X.5 record makes one claim checkable by anyone, in any field. It states:
- what was intended;
- what was predicted, and by which pass criteria;
- which files were fixed, and when;
- when it ran;
- what came out;
- who replicated it;
- where it came from;
- that it carries no personal data.

SRC-X.5 carries no domain content. It works the same for an AI benchmark, a clinical protocol, a policy forecast or a
satellite schedule.

## 2. The record
A record is one JSON object. Its `id` is the SHA-256 of its canonical form without `id`. The canonical form is JSON
with sorted keys, no spaces, UTF-8. Changing any byte changes the id.

| Field | Required for | Meaning |
|---|---|---|
| `srcx5` | all | protocol version, `"1.3"`. Records sealed under v1.2 carry `rsc: "1.2"` instead and stay valid with their ids |
| `type` | all | `claim` (a sealed test), `replication` (someone re-ran a claim), `forecast` (a sealed prediction about the future) |
| `title`, `purpose` | claim, forecast | what is tested, and why |
| `prediction.criteria` | claim, forecast | the pass criteria, fixed before the run |
| `seal.files[]` | claim, forecast | `{path, sha256}` for every file fixed before the run |
| `seal.sealed_at` | claim, forecast | ISO time the seal was committed |
| `seal.commit`, `seal.seal_file` | optional | where the seal can be checked |
| `run.started_at`, `run.run_id` | claim with an outcome | when and where it ran |
| `outcome.criteria_met` | all | `all`, `partly`, `none` or `pending`, plus `summary` and `result_files[]` |
| `replicates`, `by` | replication | the id replicated, and by whom |
| `lineage.parents[]` | optional | ids of the records it builds on |
| `consent_harm.personal_data` | all | must be `false`: the open log holds no personal data |
| `consent_harm.harm_reports[]` | optional | harm reported about this record |

**Outcomes are reported, not ranked.** `criteria_met` says whether the criteria fixed before the run were met. It says
nothing about importance. Records whose criteria were not met belong in the log as much as the others.

## 2a. Checks, quarantine, supersede and peer audit
Every node runs seven checks on every record. Each reason a node returns names its check.

| Check | What a node checks in a record |
|---|---|
| `DISCLOSURE` | content matches its id; pass criteria stated; sealed before the run; no seal dated in the future |
| `CONSENT_PRIVACY` | no personal data; if people are affected, consent is declared |
| `HARM_BOUND` | declared predicted harm at or below 0.3 |
| `CONFORMANCE` | version, evidence domain, lineage, replicated and superseded records all valid |
| `NON_BLOCKING` | a valid record is never blocked (measured in every proof) |
| `ATTRIBUTION` | a measured outcome carries fingerprinted result files; a replication names who made it |
| `PURPOSE` | the record declares that it serves the stated mission |

**Mission:** "Healing, transforming and evolving, and signalling this to others, for the growth, development,
transformation and healing of all living beings."

**Quarantine, not rejection.** A record that fails a check is quarantined: kept by the node with its reasons, never
published, and the submitter receives the reasons (`202`). Nothing is prohibited from being submitted, and nothing is
deleted: the log is append-only.

**Evidence domain.** Every record declares `evidence`: `real` (shown on real-world data or systems), `simulated` (shown
in a simulated world) or `both`.

**Declarations.** Every record carries `declarations`: `affects_people`, `consent` (required if people are affected),
`predicted_harm`, `serves_mission`.

**Supersede with stable identity.** A record may carry `supersedes: <id>` and `lineage.identity`; the identity must
equal that of the record it supersedes. The superseded record stays in the log and leaves the active set (`GET /active`).

**Targeted repair.** Sync heals only the records that differ (digest sync, §5).

**Peer audit.** `srcx5.py audit --peer <node>` checks a peer with two independent signals: its chain does not verify, and
a record it serves differs from the auditor's. Drift is flagged only when both agree.

## 3. Admission
Every node, the command-line tool and the public workflow run the same function, `check()`. A record is admitted only
if all of these hold:
1. **Format:** the version, type and required fields are present, and the pass criteria are not empty.
2. **Identity:** `id` equals the hash of the content. A tampered or forged record fails.
3. **Seal before run:** `sealed_at` is earlier than `run.started_at`.
4. **Fingerprints:** at least one file, each with a 64-hex SHA-256. With `--repo`, every file is checked byte for byte.
5. **Lineage:** every parent and every replicated id is already in the log.
6. **No personal data:** `personal_data` is false, and no text field contains an email address, phone number,
   payment card number (Luhn-checked) or IBAN.
7. **Held ids:** a record with an id already held is a no-op if identical, and is rejected otherwise.

A rejection returns every reason. Nothing is admitted silently, and nothing is deleted. A harmful record found later is
answered by a new record (a harm report or a replication with `criteria_met: none`), so the history stays whole.

## 4. The log
- Append-only, one JSON line per entry: `{seq, prev, record, entry_hash}`.
- `entry_hash` is the SHA-256 of the canonical entry without `entry_hash`; `prev` is the previous entry's hash.
- Editing any stored entry breaks the chain from that point on. `srcx5.py check-log` finds it.

## 5. Nodes and sync
A node serves the following over plain HTTP, open to every origin:

| Request | Answer |
|---|---|
| `GET /ids` | sorted ids held |
| `GET /record/<id>` | one record |
| `GET /log?ids=a,b` | entries, all or the listed ones |
| `GET /head` | chain head and count |
| `POST /submit` | `201` admitted, or `422` with reasons |

**Sync sends only what the receiver lacks.** A node fetches the peer's ids, requests only the missing entries, and
admits each through the same `check()`. A node never trusts a peer: every record is checked again on arrival.

## 6. Replication
Anyone who re-runs a claim adds a `replication` record:

`srcx5.py replicate <id> --by <name or handle> --outcome all|partly|none --summary "…"`

Trust grows with independent replications, not with the number of claims.

## 7. Privacy and safety
- Only hashes, criteria, times and outcomes are public. Data stays with its owner; a record proves that a file existed
  unchanged, without publishing the file.
- Names in `by` are handles chosen by the replicator.
- The personal-data guard is a safety net, not a guarantee. Submitters remain responsible for what they submit.

## 8. Roadmap
Runtime monitors for further invariants; need-based distribution (nodes subscribe to the relations and fields they
need instead of receiving everything); multiple audit perspectives (whole-log, per-record, per-peer); a defined
lifecycle order for records; path queries over the lineage graph; node declarations of their links; further checks.
Each enters the protocol only with a sealed proof.

## 9. Versioning
Version changes are new records about the protocol itself, sealed before they take
effect. A node states the version it checks in `/health`.
