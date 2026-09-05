#!/usr/bin/env python3
"""Hidden runner for task 02 (Go). Builds a temp Go module from the candidate's
csvkit package + the hidden driver, runs it, and prints the standard JSON contract
{load_error, results:[...]}. Invoked by grade.py as: harness.py <candidate csv.go>."""
import json, os, shutil, subprocess, sys, tempfile

def emit(load_error, results=None):
    print(json.dumps({"load_error": load_error, "results": results or []}))
    sys.exit(0)

def main():
    if len(sys.argv) < 2:
        emit("usage: harness.py <candidate csv.go>")
    candidate = os.path.abspath(sys.argv[1])
    here = os.path.dirname(os.path.abspath(__file__))
    driver = os.path.join(here, "driver.go")
    if not os.path.isfile(candidate):
        emit(f"candidate not found: {candidate}")
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, "csvkit"))
        shutil.copy(candidate, os.path.join(d, "csvkit", "csv.go"))
        shutil.copy(driver, os.path.join(d, "driver.go"))
        with open(os.path.join(d, "go.mod"), "w") as f:
            f.write("module v3task\n\ngo 1.27\n")
        env = dict(os.environ, GOFLAGS="-mod=mod", GO111MODULE="on", CGO_ENABLED="0")
        try:
            p = subprocess.run(["go", "run", "."], cwd=d, capture_output=True,
                               text=True, timeout=90, env=env)
        except subprocess.TimeoutExpired:
            emit("go run timed out (candidate loop?)"); return
        except FileNotFoundError:
            emit("go toolchain not found"); return
        if p.returncode != 0:
            emit(f"build/run failed (candidate does not compile?): {p.stderr[-600:]}")
        for line in reversed(p.stdout.splitlines()):
            line = line.strip()
            if line.startswith("{"):
                try:
                    obj = json.loads(line)
                    print(json.dumps(obj))
                    return
                except json.JSONDecodeError:
                    continue
        emit(f"driver produced no JSON; stdout tail: {p.stdout[-300:]}")

if __name__ == "__main__":
    main()
