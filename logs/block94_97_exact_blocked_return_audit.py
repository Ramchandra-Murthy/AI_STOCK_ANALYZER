from pathlib import Path
import subprocess

targets = {
    94: Path(r"services\quantitative\block94_portfolio_stress_scenario_engine.py"),
    95: Path(r"services\quantitative\block95_stress_evidence_gate.py"),
    96: Path(r"services\quantitative\block96_stress_decision_gate.py"),
    97: Path(r"services\quantitative\block97_stress_readiness_gate.py"),
}

out = []

def p(x=""):
    print(x)
    out.append(str(x))

p("=" * 100)
p("EROS 3.0 - BLOCK 94-97 EXACT BLOCKED RETURN DICTIONARY AUDIT")
p("=" * 100)

for block_id, path in targets.items():

    p()
    p("=" * 100)
    p(f"BLOCK {block_id}")
    p("=" * 100)
    p(f"SOURCE: {path}")

    lines = path.read_text(encoding="utf-8").splitlines()

    for i, line in enumerate(lines, start=1):

        stripped = line.strip()

        if (
            "return {" in stripped
            or "return _deepcopy" in stripped
            or '"status": "BLOCKED"' in line
            or '"status": STATUS_BLOCKED' in line
            or '"gate_status": STATUS_BLOCKED' in line
            or '"decision_status": STATUS_BLOCKED' in line
            or '"readiness_status": STATUS_BLOCKED' in line
        ):

            start = max(1, i - 5)
            end = min(len(lines), i + 25)

            p()
            p(f"--- RETURN CANDIDATE L{start}-L{end} ---")

            for n in range(start, end + 1):
                marker = ">>" if n == i else "  "
                p(f"{marker} L{n}: {lines[n-1]}")

p()
p("=" * 100)
p("EXACT BLOCKED RETURN AUDIT COMPLETE")
p("=" * 100)
p("READ ONLY")
p("NO SOURCE CHANGES")
p("NO BROKER")
p("NO LIVE EXECUTION")
p("NO ORDER CREATION")
p("NO MUTATION")
p("=" * 100)

text = "\n".join(out)

try:
    subprocess.run(
        ["clip.exe"],
        input=text,
        text=True,
        check=True,
    )
    print()
    print("=" * 100)
    print("CLIPBOARD : PASS")
    print("OUTPUT COPIED - CTRL+V INTO CHATGPT")
    print("=" * 100)
except Exception as exc:
    print("CLIPBOARD : FAIL")
    print(type(exc).__name__, str(exc))
