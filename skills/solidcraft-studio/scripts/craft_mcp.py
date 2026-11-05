#!/usr/bin/env python3
"""Talk to a Craft app's MCP server (stdio) from a shell, for when the client has no MCP tools loaded.

  python craft_mcp.py ping                              # solidcraft: initialize + tool list
  python craft_mcp.py tools                             # tool names
  python craft_mcp.py call execute '{"command":"sketch.new","params":{}}'
  python craft_mcp.py call batch @steps.json            # @file reads the JSON from a file
  python craft_mcp.py --app materialcraft ping
  python craft_mcp.py --app texturecraft call <tool> '{...}'
  python craft_mcp.py --app effectcraft  call command_list '{}'
  python craft_mcp.py --app texturecraft --allow proj run steps.json     # several calls in ONE session: [{"tool":..,"args":{..}}, ..]

Apps: solidcraft (default), materialcraft, texturecraft, effectcraft. Each is `<app>-cli mcp`.
Find the exe: --exe, env <APP>_CLI, PATH, then C:/Program Files/<App>/<app>-cli.exe.
--live PORT bridges to the running desktop app (solidcraft-cli mcp --connect 127.0.0.1:PORT; others use --bridge PORT).
--allow DIR (repeatable) adds a folder the agent may read/write: solidcraft --allow-path, effectcraft --automation-read/write-root, the others --read-root/--write-root.
Each invocation is a NEW headless session unless --live is used, so for multi-step work send one `batch`, or use the MCP tools
the client loaded, or --live. Output is the tool's JSON text.
"""
import argparse, base64, json, os, shutil, subprocess, sys

APPS = {"solidcraft": "SolidCraft", "materialcraft": "MaterialCraft", "texturecraft": "TextureCraft", "effectcraft": "EffectCraft"}


def find_exe(app, arg):
    name = app + "-cli"
    for c in [arg, os.environ.get(name.upper().replace("-", "_")), shutil.which(name),
              rf"C:\Program Files\{APPS[app]}\{name}.exe", f"/usr/bin/{name}", f"/Applications/{APPS[app]}.app/Contents/MacOS/{name}"]:
        if c and os.path.exists(c):
            return c
    sys.exit(f"{name} not found. Install {APPS[app]}, or pass --exe / set {name.upper().replace('-', '_')}.")


def argv_for(app, exe, live, allow, extra=()):
    a = [exe, "mcp", *extra]
    if live:
        a += ["--connect", f"127.0.0.1:{live}"] if app == "solidcraft" else ["--bridge", str(live)]
    for d in allow:
        d = os.path.abspath(d)
        if app == "solidcraft":
            a += ["--allow-path", d]
        elif app == "effectcraft":
            a += ["--automation-read-root", d, "--automation-write-root", d]
        else:
            a += ["--read-root", d, "--write-root", d]
    return a


class Session:
    def __init__(self, argv):
        self.p = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True, encoding="utf-8")
        self.n = 0
        self.info = self.rpc("initialize", {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "craft_mcp.py", "version": "1"}})
        self.send({"jsonrpc": "2.0", "method": "notifications/initialized"})

    def send(self, m):
        self.p.stdin.write(json.dumps(m) + "\n")
        self.p.stdin.flush()

    def rpc(self, method, params=None):
        self.n += 1
        self.send({"jsonrpc": "2.0", "id": self.n, "method": method, "params": params or {}})
        while True:
            line = self.p.stdout.readline()
            if not line:
                sys.exit("MCP server exited. Is the app running (--live) and the folder allowed (--allow)?")
            m = json.loads(line)
            if m.get("id") == self.n:
                if "error" in m:
                    sys.exit("MCP error: " + json.dumps(m["error"]))
                return m["result"]

    def call(self, tool, args):
        r = self.rpc("tools/call", {"name": tool, "arguments": args})
        text = "\n".join(c.get("text", f"[{c.get('type')} content]") for c in r.get("content", []))
        for c in r.get("content", []):
            if c.get("type") == "image" and getattr(self, "imgdir", None):  # --img-dir: keep returned images so you can look at them
                self.n_img = getattr(self, "n_img", 0) + 1
                fp = os.path.join(self.imgdir, "%s_%02d.png" % (tool, self.n_img))
                open(fp, "wb").write(base64.b64decode(c["data"]))
                text += "\n[image saved: %s]" % fp
        return text, bool(r.get("isError"))


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--app", default="solidcraft", choices=list(APPS))
    ap.add_argument("--exe")
    ap.add_argument("--live", type=int, help="bridge to the running app on this control port")
    ap.add_argument("--allow", action="append", default=[], help="folder the agent may read/write")
    ap.add_argument("--img-dir", help="save images a tool returns (renders, screenshots) into this folder")
    ap.add_argument("--arg", action="append", default=[], help="extra argument for `<app>-cli mcp`, e.g. --arg=--gpu (effectcraft GPU render)")
    ap.add_argument("cmd", choices=["ping", "tools", "call", "run"])
    ap.add_argument("tool", nargs="?")
    ap.add_argument("args", nargs="?", default="{}", help="JSON object, or @file.json")
    a = ap.parse_args()
    s = Session(argv_for(a.app, find_exe(a.app, a.exe), a.live, a.allow, a.arg))
    if a.img_dir:
        os.makedirs(a.img_dir, exist_ok=True)
        s.imgdir = a.img_dir
    try:
        if a.cmd == "ping":
            si = s.info.get("serverInfo", {})
            print(f"{a.app}: {si.get('name')} {si.get('version')}, protocol {s.info.get('protocolVersion')}")
            print("tools:", ", ".join(t["name"] for t in s.rpc("tools/list")["tools"]))
        elif a.cmd == "tools":
            for t in s.rpc("tools/list")["tools"]:
                print(t["name"], "-", t.get("description", "").split(". ")[0][:110])
        elif a.cmd == "run":
            steps = json.load(open(a.tool, encoding="utf-8"))
            bad = 0
            for i, st in enumerate(steps):
                text, err = s.call(st["tool"], st.get("args", {}))
                print("#%d %s %s %s" % (i, st["tool"], "ERROR" if err else "ok", text[:300].replace(chr(10), " ")))
                bad += err
                if err:
                    break
            sys.exit(1 if bad else 0)
        else:
            if not a.tool:
                sys.exit("call needs a tool name")
            raw = open(a.args[1:], encoding="utf-8").read() if a.args.startswith("@") else a.args
            text, err = s.call(a.tool, json.loads(raw))
            print(text)
            sys.exit(1 if err else 0)
    finally:
        s.p.terminate()


if __name__ == "__main__":
    main()
