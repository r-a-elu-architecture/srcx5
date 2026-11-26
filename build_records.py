"""Build the first RSC records from the sealed RSOS tests (run once from the research repository root).
Every fingerprint is taken from the seal file AS COMMITTED at its seal commit, and checked against the files at that
commit; the seal time is the seal commit's time; the run time is the first workflow run that used the seal."""
import json, subprocess, hashlib, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import rsc

def git(*a): return subprocess.run(["git", *a], capture_output=True, check=True).stdout

def seal_files(commit, seal):
    out = []
    for line in git("show", f"{commit}:{seal}").decode().splitlines():
        if line.strip() and not line.startswith("#"):
            h, p = line.split(None, 1); p = p.strip()
            got = hashlib.sha256(git("show", f"{commit}:{p}")).hexdigest()
            assert got == h, f"{seal}: {p} does not match at {commit[:8]}"
            out.append({"path": p, "sha256": h})
    return out

def fhash(p): return {"path": p, "sha256": hashlib.sha256(open(p, "rb").read()).hexdigest()}

T = [  # key, title, purpose, criteria, seal file, seal commit, sealed_at (UTC), run id, run started (UTC), outcome, summary, results, parents
 ("REAL3", "REAL3: one shared selector across ten real domains", "Does one shared decision selector beat each domain's standard method across ten real domains?",
  "Per domain: two-look sequential test on fresh cells 201-216; shown when the 97.5 % interval of the gain lies above zero (PREREG_REAL3.md)",
  "real/SEAL_REAL3.txt", "ed5a2f5c783ae000ce43d0f3dec4a3a8c5a1f42e", "2026-11-25T02:55:12Z", "45536337290", "2026-11-25T02:55:17Z",
  "partly", "Shown in 7 of 10 domains under the pre-registered rule (4 after Holm across units); quantum and neural sensing not shown; biology undecided on 6 of 8 cells. Five crashed units re-run under FIX1, disclosed.",
  ["real/RESULTS_REAL3.md"], []),
 ("STRUCT1", "STRUCT1: the structure alone vs plain rollout", "With every domain-written lever off, does the general structure beat plain rollout?",
  "At least 4 of 5 rows pass both tests at Holm p < 1e-5 (PREREG_STRUCT1.md)",
  "real/SEAL_STRUCT1.txt", "925abf5569601a22630696ea832af64cdcd3923d", "2026-11-25T10:37:43Z", "45596832492", "2026-11-25T10:37:57Z",
  "none", "Not met in any of 5 rows: the bare structure matches plain rollout. The full seed replicated its gains on fresh cells.",
  ["real/results_cloud/struct1/RESULTS_STRUCT1.md"], ["REAL3"]),
 ("CONF1", "CONF1: the full seed vs the standard in four domains", "Does the full seed beat each domain's standard on fresh cells, with every lever traced to an RSOS operator?",
  "All 4 domains at Holm p < 1e-5, every used lever traced (PREREG_CONF1.md, FIX1 addendum)",
  "real/SEAL_CONF1_A.txt", "63c7bdeac51f57510af8d3fe51cfa59eda6cb120", "2026-11-25T12:19:24Z", "45615498047", "2026-11-25T12:37:13Z",
  "all", "AI agents 58-69 % fewer tokens with higher accuracy (p 8.5e-11, 5.5e-27); AI-human 42 % (4.9e-21); inventory +1.42 %, 12/12 (1.1e-9); satellite +1.67 %, 12/12 (1.4e-9). Satellite re-ran on frozen orbit data after CelesTrak returned HTTP 503 (FIX1).",
  ["real/RESULTS_CONF1.md"], ["STRUCT1"]),
 ("CONF2", "CONF2: cross-domain seed, communication principle, one move per operator", "Three claims on fresh cells, sealed separately from CONF1.",
  "Claim 1: 5 rows at Holm p < 1e-5; claim 2: 3 AI rows at p < 1e-7 with equal or better result; claim 3: generated moves beat the standard in 4 rows (PREREG_CONF2.md)",
  "real/SEAL_CONF2.txt", "970f5b7de7e0c8583748b81fee1a3fd0545d14bc", "2026-11-25T12:37:49Z", "45615652848", "2026-11-25T12:38:11Z",
  "partly", "Claim 1 met in 4 of 5 rows, claim 2 in 2 of 3, claim 3 in none (one-move-per-operator was a drift from the RSOS grammar, corrected in CONF3).",
  ["real/RESULTS_CONF2.md"], ["CONF1"]),
 ("CONF3", "CONF3: communication principle and moves composed in the RSOS language", "Higher-powered confirmation with a composed-operator arm.",
  "Claim 1: 5 rows at Holm p < 1e-5; claim 2: 3 AI rows at p < 1e-7 with equal or better result; claim 3: composed moves beat the standard in at least 3 of 4 rows (PREREG_CONF3.md)",
  "real/SEAL_CONF3.txt", "eb2e6ea6812623a0e40476ce9125ae74a2834b40", "2026-11-25T13:15:31Z", "45621782974", "2026-11-25T13:15:47Z",
  "partly", "Claim 2 all met (25-61 % fewer tokens in 3 AI rows, p < 1e-7); claim 3 all met (3 of 4 rows: AI agents 45 %, AI-AI 27 %, satellite +1.01 % 22/23); claim 1 met in 4 of 5 rows. Satellite cell 706 timed out.",
  ["real/RESULTS_CONF3.md"], ["CONF2"]),
 ("CONF4", "CONF4: programs by an AI given the RSOS sources vs the same AI without them", "Does the RSOS language as text make better decision programs? Three RSOS agents vs three control agents, same compiled operator channels.",
  "At least 3 of 4 rows at Holm p < 1e-5, no harm, use >= 25 %, above the floor (PREREG_CONF4.md)",
  "real/SEAL_CONF4.txt", "a53eac952c81d4c4566e0f8564e2566b4a3ab748", "2026-11-25T16:55:57Z", "45659293703", "2026-11-25T16:56:11Z",
  "none", "Met in 1 of 4 rows: AI agents (ReAct) 6.7k vs 12.0k tokens, -44 %, p 4.9e-16; other rows no difference. Both sides had the compiled operators, so this measured what the text adds on top of them.",
  ["real/RESULTS_CONF4.md"], ["CONF3"]),
 ("ABL1", "ABL1: one operator switched off per row", "Does each named operator cause the gain it carries?",
  "All 3 rows: switching the row's operator off costs the result at Holm p < 1e-5; full RSOS beats the standard; no harm (PREREG_ABL1.md)",
  "real/SEAL_ABL1.txt", "7c4d1840d67789f2acc944b965687f1f33c59668", "2026-11-25T17:33:16Z", "45666010082", "2026-11-25T17:33:28Z",
  "none", "Not met in any row: full RSOS beat the standard everywhere (p 1e-25 to 2e-15), but the switched operators were barely chosen. Design error, disclosed.",
  ["real/RESULTS_ABL1.md"], ["CONF3"]),
 ("CONF5", "CONF5: the identified RSOS structure vs plain rollout", "Does the structure that carries each host's gain (identified on development cells) beat RSOS-free planning?",
  "All 3 rows: RSOS beats plain rollout, Holm p < 1e-5, guard and no harm (PREREG_CONF5.md)",
  "real/SEAL_CONF5.txt", "15c9b6b018b8a816c7e2014ec1aedf4b157cc181", "2026-11-25T18:29:02Z", "45675642649", "2026-11-25T18:29:13Z",
  "partly", "Met in 2 of 3 rows: AI agents 43 % fewer tokens at accuracy 0.95 vs 0.83 (p 1.9e-13, 44/48); satellite +0.74 %, 20/20 (p 1.5e-8). AI-AI not on tokens (p 0.25).",
  ["real/RESULTS_CONF5.md", "real/pilot/PILOT1_NOTES.md"], ["ABL1", "STRUCT1"]),
 ("CONF6", "CONF6: the whole AI-AI system bound to one RSOS structure vs plain rollout", "Does binding the whole two-agent system to one structure beat RSOS-free planning on accuracy and tokens?",
  "Accuracy gain and tokens saved vs plain rollout both at Holm p < 1e-5, no harm vs the standard, 200 fresh cells (PREREG_CONF6.md)",
  "real/SEAL_CONF6.txt", "23a5e633619b140fbda1d6d0a660cb7b4f058e3c", "2026-11-26T04:03:59Z", "45752828112", "2026-11-26T04:04:05Z",
  "all", "Accuracy 1.000 vs 0.875 (25 better, 0 worse; Holm p 1.3e-7); tokens 1,286 vs 2,645, -51 % (180/200; p 5.1e-28); no harm. Compact-message arm switched off: no difference.",
  ["real/RESULTS_CONF6.md", "real/pilot/PILOT2_NOTES.md"], ["CONF5"]),
]

def main(out_dir):
    os.makedirs(out_dir, exist_ok=True); ids = {}
    for key, title, purpose, crit, seal, commit, sat, run, rat, oc, summ, res, parents in T:
        rec = {"type": "claim", "title": title, "purpose": purpose, "prediction": {"criteria": crit},
               "seal": {"seal_file": seal, "commit": commit, "sealed_at": sat, "files": seal_files(commit, seal)},
               "run": {"run_id": run, "started_at": rat, "where": "GitHub Actions, r-a-elu-architecture/RSOS-Multimodal-World"},
               "outcome": {"criteria_met": oc, "summary": summ, "result_files": [fhash(p) for p in res]},
               "lineage": {"parents": [ids[p] for p in parents], "source": "sealed research record"},
               "consent_harm": {"personal_data": False, "harm_reports": []},
               "evidence": "both", "declarations": {"affects_people": False, "predicted_harm": 0, "serves_mission": True,
                                                     "note": "AI, data and simulated hosts; no living participants"}}
        rec = rsc.finalize(rec); R = rsc.check(rec, known=set(ids.values()))
        assert not R, (key, R)
        ids[key] = rec["id"]; json.dump(rec, open(os.path.join(out_dir, f"{key}.json"), "w"), indent=1, ensure_ascii=False)
        print(key, rec["id"][:16], len(rec["seal"]["files"]), "files", oc)
    json.dump(ids, open(os.path.join(out_dir, "INDEX.json"), "w"), indent=1)

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "protocol/records")
