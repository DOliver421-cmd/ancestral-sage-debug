"""
deploy_sim.py — Railway deploy simulation (application layer).

Reproduces how Railway launches the backend and measures whether the
/api/version healthcheck endpoint becomes available within the healthcheck
window, under the adverse condition Railway might actually have: MongoDB
unreachable. A robust deploy MUST answer /api/version fast regardless of DB
state, because that is what Railway probes to mark the container healthy.

Usage:
  SIM_DEADLINE=60 python deploy_sim.py            # single run
  SIM_RUNS=5 SIM_DEADLINE=30 python deploy_sim.py # N runs, report streak
Env:
  SIM_MONGO    Mongo URL to inject (default: unreachable 10.255.255.1)
  SIM_PORT     base port (default 8799; each run uses port+i)
  SIM_DEADLINE seconds to wait for first 200 (default 60)
  SIM_RUNS     number of consecutive runs (default 1)
"""
import os, sys, time, subprocess, urllib.request, urllib.error

BASE_PORT = int(os.environ.get("SIM_PORT", "8799"))
DEADLINE = float(os.environ.get("SIM_DEADLINE", "60"))
RUNS = int(os.environ.get("SIM_RUNS", "1"))
MONGO = os.environ.get("SIM_MONGO", "mongodb://10.255.255.1:27017")


def poll(port):
    url = f"http://127.0.0.1:{port}/api/version"
    try:
        with urllib.request.urlopen(url, timeout=3) as r:
            return r.status, r.read(160).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception:
        return None, ""


def run(port):
    env = os.environ.copy()
    env["PORT"] = str(port)
    env["MONGO_URL"] = MONGO
    env["DB_NAME"] = "wai_sim"
    env["JWT_SECRET"] = "sim-secret"
    env["CORS_ORIGINS"] = "*"
    env["SERVE_FRONTEND"] = "0"
    cmd = [sys.executable, "-m", "uvicorn", "server:app",
           "--host", "127.0.0.1", "--port", str(port), "--log-level", "warning"]
    t0 = time.time()
    proc = subprocess.Popen(cmd, env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    res = {"healthy": False, "latency": None, "last_code": None, "exit": None}
    try:
        while time.time() - t0 < DEADLINE:
            if proc.poll() is not None:
                res["exit"] = proc.returncode
                break
            code, body = poll(port)
            res["last_code"] = code
            if code == 200:
                res["healthy"] = True
                res["latency"] = round(time.time() - t0, 2)
                res["body"] = body
                break
            time.sleep(1)
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()
    return res


def main():
    print(f"SIM: mongo={MONGO} deadline={DEADLINE}s runs={RUNS}")
    streak = 0
    ok = 0
    for i in range(RUNS):
        r = run(BASE_PORT + i)
        status = "PASS" if r["healthy"] else "FAIL"
        if r["healthy"]:
            ok += 1
            streak += 1
        else:
            streak = 0
        print(f"  run {i+1}/{RUNS}: {status} "
              f"latency={r['latency']}s last_code={r['last_code']} exit={r['exit']} "
              f"{r.get('body','')}".rstrip())
    print(f"SIM RESULT: {ok}/{RUNS} passed (max consecutive streak={streak})")
    sys.exit(0 if ok == RUNS and RUNS > 0 else 1)


if __name__ == "__main__":
    main()
