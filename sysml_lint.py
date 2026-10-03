#!/usr/bin/env python3
"""
sysml_lint.py FILE... -- validate SysML v2 text with the OMG pilot implementation, headless.

Setup once (Java 17+):
    pip install jupyter_client
    curl -LO https://github.com/Systems-Modeling/SysML-v2-Pilot-Implementation/releases/download/2026-08/jupyter-sysml-kernel-0.62.0.zip
    sha256sum jupyter-sysml-kernel-0.62.0.zip   # 5a015ed3f2b3d2dae14e9c3fb9602d9e1fef5f9ce33cf396c422329405cc3cb2
    unzip jupyter-sysml-kernel-0.62.0.zip -d sysml-kernel && python3 sysml-kernel/install.py --user
Files are evaluated in order in one session, so later files may import earlier ones.
Exit 1 if any file reports an error.
"""
import sys
from jupyter_client.manager import start_new_kernel


def run(kc, code):
    msg_id = kc.execute(code)
    out, err = [], False
    while True:
        m = kc.get_iopub_msg(timeout=600)
        if m["parent_header"].get("msg_id") != msg_id:
            continue
        t, c = m["msg_type"], m["content"]
        if t == "stream":
            txt = "".join(l for l in c["text"].splitlines(True)
                          if not l.startswith(("Reading ", "log4j:")))
            out.append(txt)
            err |= c.get("name") == "stderr" and bool(txt.strip())
        elif t in ("execute_result", "display_data"):
            out.append(c["data"].get("text/plain", ""))
        elif t == "error":
            out.append(c.get("evalue", "") + "\n" + "\n".join(c.get("traceback", [])))
            err = True
        elif t == "status" and c["execution_state"] == "idle":
            break
    text = "".join(out).strip()
    return text, err or "ERROR" in text


def main(files):
    km, kc = start_new_kernel(kernel_name="sysml", startup_timeout=300)
    bad = 0
    try:
        for f in files:
            text, err = run(kc, open(f).read())
            bad += err
            print(f"{'FAIL' if err else 'OK  '}  {f}\n{text}\n")
    finally:
        kc.stop_channels()
        km.shutdown_kernel(now=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
