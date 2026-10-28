"""
Runs the whole Week 5 submission in order and saves each script's printed
output to part*_output.txt (UTF-8, so it also works on Windows).

    python run_all.py
"""
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
STEPS = [
    ("partD_bubble.py", "partD_bubble_output.txt"),
    ("partD_pcp.py", "partD_pcp_output.txt"),
    ("partD_choropleth.py", "partD_choropleth_output.txt"),
    ("partA_charts.py", "partA_output.txt"),
    ("partB_decisions.py", "partB_output.txt"),
    ("partC_maps.py", "partC_output.txt"),
    ("partF_map.py", "partF_output.txt"),
    ("build_reports.py", None),
]
env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8", MPLBACKEND="Agg")
for script, out in STEPS:
    print(f"running {script} ...", flush=True)
    res = subprocess.run([sys.executable, script], cwd=HERE, env=env, capture_output=True,
                         text=True, encoding="utf-8")
    if out:
        (HERE / out).write_text(res.stdout + res.stderr, encoding="utf-8")
    if res.returncode != 0:
        print(res.stdout[-2000:], res.stderr[-3000:])
        sys.exit(f"FAILED: {script} — see the error above")
    print(f"   ok{'  -> ' + out if out else ''}")
print("\nAll done. Figures (*.png) and PDFs are in this folder.")
print("Part C still needs at least 5 REAL readers:  python partC_maps.py --record  (once per reader)")
print("then:  python partC_maps.py --score   and   python build_reports.py")
