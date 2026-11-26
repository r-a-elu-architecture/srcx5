# FIX2: anchor status label (found after T7 ran; disclosed)

T7 ran once (GitHub Actions run 45785355641, FIX1 workflow). The OpenTimestamps proof for the log head
d3d70d58bafd97ab91ce9b9d977d0b5578b27e46f86866074b2fb87575bcbdda was created (875 bytes) and submitted to four
public calendars. `ots info` on the proof shows a `PendingAttestation` (alice.btc.calendar.opentimestamps.org): pending,
as expected minutes after stamping.

The JSON written by `srcx5_net.py anchor` said "confirmed": its check matched the word "complete" inside "not complete".
The proof itself is correct; only the label was wrong. T7's criterion (a proof created for the head and its status
recorded) is met, with the status corrected to **pending**.

Correction: `srcx5_anchor.py` (new file; `srcx5_net.py` stays exactly as sealed and tested) reads the status from the
proof itself: confirmed only when it holds a Bitcoin block-header attestation. Bitcoin confirmation is recorded when it
arrives (expected within hours).
