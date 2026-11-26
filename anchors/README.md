# Anchors
Proofs that the log head (and so every record before it) existed at a time, on a public network. Kept beside the log,
never inside it, so any network can be added without changing a record. `<head>.json` names the network and status;
`<head>.ots` is the OpenTimestamps proof for Bitcoin (verify with `ots verify <head>.ots`). Anyone may anchor the head on
any other network and add the proof here with a pull request.
