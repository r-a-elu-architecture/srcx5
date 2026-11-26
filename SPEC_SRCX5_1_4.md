# SRC-X.5, specification v1.4

An open record of sealed claims, verified at the source.

**Status:** v1.4, 26 November 2026. v1.4 adds connection at every layer (§L); the record format and every rule are those of v1.3. Text CC BY 4.0; reference code Apache 2.0.
**Reference implementation:** `srcx5.py` (the rules: admission, the log, the core node; sealed, unchanged since v1.3), `srcx5_net.py` (the v1.4 network layer) and `srcx5_mcp.py` (the AI-agent interface). Python standard library only.

## 0. Name and versions
- **Name:** SRC-X.5. Written `srcx5` where punctuation cannot go (file, package, repository). It was first written on
  8 June 2025 for a compact key that re-expands into its full content; a record's id is exactly that.
- **v1.3 changes the name only.** Every rule, check and threshold is the same as v1.2. The version field is now
  `srcx5`; a v1.3 node also admits records carrying `rsc: "1.2"`, so the genesis log keeps every id and its chain.
- **v1.2** (`rsc.py`, sealed in `tests/SEAL_RSC.txt`) is kept unchanged as the reference that made the genesis log.
- **v1.4 changes connection only** (§L). The record format stays `srcx5: "1.3"`; `srcx5.py` is unchanged.

## L. Layers: where anyone connects (v1.4)
A record is canonical bytes whose identity is their own SHA-256. Every layer of every communication model can carry
bytes and every system can compute a hash, so SRC-X.5 is applied at each layer through that layer's main standard.
Whoever enters at any layer meets the protocol in the form native to that layer.

**The OSI model**

| Layer | Main standard there | SRC-X.5 at that layer |
|---|---|---|
| 8 Meaning (above OSI) | purpose, criteria, lineage; agents | every record states its purpose, its pass criteria fixed before the run, and its lineage; AI agents connect through MCP (`srcx5_mcp.py`) |
| 7 Application | HTTP/REST, git, MCP | the node API (`openapi.json`, OpenAPI 3.1); the log as a git repository; the browser verifier |
| 6 Presentation | UTF-8, JSON, JSON-LD | one canonical encoding (sorted keys, no spaces, UTF-8, integers only); `schema/record.schema.json`; a W3C PROV view in JSON-LD (`ld/<id>.jsonld`, `context.jsonld`) |
| 5 Session | peer synchronisation | digest sync: compare heads, move only missing records, resume after any break; first peer that answers is used |
| 4 Transport | TCP, QUIC; Bundle Protocol (space) | carried unchanged; each record is self-contained, so store-and-forward and long delays need nothing extra |
| 3 Network | IP; content addressing | the id is the address: the same id finds and proves the same bytes over any route |
| 2 Data link | Ethernet, Wi-Fi, CCSDS space data link | any frame; integrity is end to end by the hash, not by the link |
| 1 Physical | fibre, radio, optical, print | any medium; bytes read back from any medium verify identically |

**The other models, the same way**

| Model | Where SRC-X.5 binds |
|---|---|
| TCP/IP (the internet) | layers 7-3 above, merged |
| Space and interplanetary (CCSDS, delay-tolerant networking) | records travel as bundles or files unchanged; sync tolerates hours of delay and broken links |
| Web and linked data (W3C) | JSON-LD and PROV: records are provenance entities in any semantic or scientific tool |
| Decentralized ledgers | the head hash anchored in a transaction (Bitcoin through OpenTimestamps in the reference set); anyone may anchor on any ledger |
| Archives and identifiers | DOI snapshots (Zenodo) and Software Heritage keep the log permanently citable |

**One shape for every copy.** A running node and a static mirror answer the same read paths: `ids.json`, `active.json`,
`head.json`, `log.json`, `records/<id>.json`, `ld/<id>.jsonld`, `.well-known/srcx5.json`. A running node also answers the
v1.3 paths and `POST /submit`. A client never needs to know which kind it reached.

**Mirrors and failover.** `MIRRORS.json` lists every known copy. Sync takes a list of peers and mirrors and uses the
first that answers; a copy that answers with a record whose id is not its own hash is skipped. A scheduled check
compares each mirror's head with the log and refreshes any that is stale. Anyone who runs a node holds a full copy and
can be added to the list with one pull request. No copy is trusted; every copy is checked.

**Anchors.** An anchor proves that the log head (and so every record before it) existed at a time, on a public
network. Anchors are stored beside the log (`anchors/<head>.json` and the network's proof), not inside it, so any
network can be added without changing a record.

**Hardening.** A node accepts at most 256 kB per submission and 30 submissions per client per minute, accepts only
UTF-8 JSON objects, answers 4xx to anything else, never crashes on bad input, and refuses edits and deletion (405).

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
