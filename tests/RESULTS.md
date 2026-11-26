# RSC v1.2 launch proofs: results (confirming runs, seed 3, after seal 59f9c5d6 at 2026-11-26T05:39:47Z)

Pass criteria: `tests/PREDICTIONS.md`, sealed in `tests/SEAL_RSC.txt`. No crash, no re-run. All criteria met.

| Proof | Measured |
|---|---|
| Admission | 600 of 600 violations quarantined, each of 15 classes 40/40; 0 of 200 valid records blocked; an edited stored entry detected |
| Checks | DISCLOSURE, CONSENT_PRIVACY, HARM_BOUND, CONFORMANCE, ATTRIBUTION, PURPOSE: each 30/30 quarantined and named; NON_BLOCKING: 0 of 200 valid blocked; nothing quarantined published |
| Supersede | clone admitted and active; old record kept, not active; identity change quarantined |
| Peer audit | edited peer flagged (both signals); clean peer and lagging peer not flagged |
| Sync | three live nodes converged, chains intact; the half-missing node moved 50.3 % of a full copy; a re-check moved 0.86 % |
