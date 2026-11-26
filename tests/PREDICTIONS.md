# RSC v1.2 launch proofs: predictions (sealed before the confirming runs, seed 3; tests/SEAL_RSC.txt)

Development screens (seed 1) were run before this seal on this code; all passed. Earlier development versions of the
protocol found and fixed three issues before any seal of theirs: a tampered copy reusing a held id was answered as
admitted; a forecast could carry a seal dated in the future; one test applied the attribution check to outcomes still
pending. Each is now covered by a check or by the test design.

Pass criteria for the confirming runs (seed 3, fresh valid records and fresh violations), all must hold:
1. **Admission:** 100 % of violations quarantined in each of 15 attack classes (forged id, tampered copy, back-dated
   seal, missing or invalid fingerprints, unknown parent, missing criteria, outcome without a run, wrong version,
   email, phone, payment card, IBAN, declared personal data, replication of an unknown record); 0 of 200 valid records
   blocked; an edited stored entry is detected by `check-log`.
2. **Checks:** for each of DISCLOSURE, CONSENT_PRIVACY, HARM_BOUND, CONFORMANCE, ATTRIBUTION and PURPOSE, 30 of 30
   violations quarantined, each reason naming that check; NON_BLOCKING: 0 of 200 valid blocked; nothing quarantined
   is published.
3. **Supersede:** the modified clone is admitted and active; the old record stays in the log and leaves the active set;
   a clone that changes identity is quarantined.
4. **Peer audit:** a peer with an edited stored entry is flagged (both signals agree); a clean peer and a peer that is
   only behind are not.
5. **Sync:** three live nodes converge with intact chains; the node lacking half moves at most 60 % of a full copy; a
   re-check with nothing missing moves at most 2 %.
