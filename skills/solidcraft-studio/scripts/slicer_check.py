#!/usr/bin/env python3
"""Check a model in OrcaSlicer from the command line (no MCP server needed).

  python slicer_check.py part.3mf --material PETG
  python slicer_check.py part.3mf --material ASA --nozzle 0.6 --bed supertack --support-quality clean
  python slicer_check.py part.3mf --material PETG --json

It runs the slicer headless three times on the Bambu Lab H2C profiles and reports:
  1. geometry   : size, volume, manifold (watertight) or not
  2. as exported: print time, filament, layers, any support the file already asks for
  3. supports on: the same slice with tree supports forced on. If no support extrusion appears, the orientation needs none.
  4. best orient: the slicer's own pick (--orient). The tool reports whether your orientation matches it.

Finds OrcaSlicer (ORCA_SLICER env var, PATH, Program Files, /Applications) and the Bambu Lab profiles in the Bambu Studio or
OrcaSlicer user folder (ORCA_PROFILES env var or --profiles). Writes G-code only into --outdir (default: next to the 3MF, in
'slicer-check/'). It never edits your presets.

Verified on Windows with OrcaSlicer 2.5.0-dev and the Bambu Studio H2C profiles. Other OS paths are best effort: check.
"""
import argparse, json, os, re, shutil, subprocess, sys, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
MATS = json.load(open(os.path.join(HERE, "..", "assets", "materials.json"), encoding="utf-8"))["materials"]


def find_exe(arg):
    for c in [arg, os.environ.get("ORCA_SLICER"), shutil.which("orca-slicer"), shutil.which("OrcaSlicer"),
              r"C:\Program Files\OrcaSlicer\orca-slicer.exe", "/Applications/OrcaSlicer.app/Contents/MacOS/OrcaSlicer"]:
        if c and os.path.exists(c):
            return c
    sys.exit("OrcaSlicer not found. Install it, or set ORCA_SLICER to the executable (or pass --exe).")


def find_profiles(arg):
    home = os.path.expanduser("~")
    for c in [arg, os.environ.get("ORCA_PROFILES"),
              os.path.join(os.environ.get("APPDATA", ""), "BambuStudio", "system", "BBL"),
              os.path.join(os.environ.get("APPDATA", ""), "OrcaSlicer", "system", "BBL"),
              os.path.join(home, "Library", "Application Support", "BambuStudio", "system", "BBL"),
              os.path.join(home, "Library", "Application Support", "OrcaSlicer", "system", "BBL"),
              os.path.join(home, ".config", "BambuStudio", "system", "BBL")]:
        if c and os.path.isdir(os.path.join(c, "machine")):
            return c.replace("\\", "/")
    sys.exit("Bambu Lab profile JSON not found. OrcaSlicer keeps its profiles in a binary BBL.opc bundle the CLI cannot read. Install Bambu Studio and open it once (it writes %APPDATA%/BambuStudio/system/BBL), or pass --profiles <.../system/BBL>, or set ORCA_PROFILES.")


def flatten(pdir, name):
    """Resolve a process preset's 'inherits' chain into one standalone preset (the CLI cannot resolve inherits for user files)."""
    d = json.load(open(os.path.join(pdir, name + ".json"), encoding="utf-8"))
    base = flatten(pdir, d["inherits"]) if d.get("inherits") else {}
    base.update(d)
    return base


def run(cmd, timeout=600):
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def gcode_stats(path):
    t = open(path, encoding="utf-8", errors="replace").read()
    g = lambda pat: (re.search(pat, t) or [None, None])[1]
    feats = {}
    for f in re.findall(r"^; FEATURE: (.+)$", t, re.M):
        feats[f.strip()] = feats.get(f.strip(), 0) + 1
    return {"time": g(r"total estimated time: ([^\n]+)"), "layers": g(r"total layer number: (\d+)"),
            "filament_g": g(r"filament used \[g\] = ([\d.]+)"), "filament_g_each": g(r"filament used \[g\] = ([\d., ]+)"), "filament_cm3": g(r"filament used \[cm3\] = ([\d.]+)"),
            "features": feats, "support_lines": sum(v for k, v in feats.items() if "upport" in k)}


BEDS = {  # friendly name -> OrcaSlicer --curr-bed-type
    "cool": "Cool Plate", "supertack": "Supertack Plate", "cool-supertack": "Supertack Plate", "textured-cool": "Textured Cool Plate",
    "engineering": "Engineering Plate", "high-temp": "High Temp Plate", "textured-pei": "Textured PEI Plate", "textured": "Textured PEI Plate",
}
DEFAULT_PROCESS = {"0.2": "0.12mm Balanced Quality", "0.4": "0.20mm Standard", "0.6": "0.30mm Standard", "0.8": "0.40mm Standard"}
# Support-interface gap as a multiple of layer height (community + Bambu wiki starting points, see references/clean-supports.md)
GAP_X = {"PLA": 1.0, "PETG": 1.5, "ASA": 1.25, "ABS": 1.25}


def pick(prof, kind, base, noz):
    """First existing preset: '<base> @BBL H2C <noz> nozzle', then the shared '<base> @BBL H2C'."""
    names = ["%s @BBL H2C %s nozzle" % (base, noz), "%s @BBL H2C" % base]
    for n in names:
        if os.path.exists("%s/%s/%s.json" % (prof, kind, n)):
            return n
    sys.exit("No %s preset for '%s' on a %s mm nozzle. Tried: %s" % (kind, base, noz, "; ".join(names)))


def clean_supports(flat, material, nozzle):
    lh = float(flat.get("layer_height", 0.2))
    gap = round(lh * GAP_X.get(material, 1.25), 3)
    flat.update({"support_top_z_distance": str(gap), "support_bottom_z_distance": str(gap),
                 "support_interface_top_layers": "3", "support_interface_bottom_layers": "2",
                 "support_interface_spacing": "0", "support_interface_pattern": "rectilinear",
                 "support_object_xy_distance": str(round(float(nozzle) * 0.875, 3)), "support_threshold_angle": "40"})
    return gap


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("model")
    ap.add_argument("--material", default="PETG", choices=list(MATS))
    ap.add_argument("--nozzle", default="0.4", choices=["0.2", "0.4", "0.6", "0.8"])
    ap.add_argument("--bed", help="cool | supertack | textured-cool | engineering | high-temp | textured-pei (default: the material's usual plate)")
    ap.add_argument("--filament", help="exact Bambu filament name, e.g. 'Bambu PLA Matte' (default: the material's Basic)")
    ap.add_argument("--process", help="process name without the printer suffix (default depends on nozzle)")
    ap.add_argument("--support-quality", choices=["default", "clean"], default="clean",
                    help="clean: tighter interface (3 top layers, solid, gap scaled to layer height) so supports peel off smooth")
    ap.add_argument("--support-type", default="tree(auto)", help="tree(auto), normal(auto), tree(manual), normal(manual)")
    ap.add_argument("--interface-filament", help="second Bambu filament for the support INTERFACE layers, e.g. 'Bambu PETG Basic' under PLA (dual-nozzle H2C). Reports grams per filament")
    ap.add_argument("--on-plate-only", action="store_true", help="supports only from the build plate (no scars on the part, more material)")
    ap.add_argument("--printer", default="Bambu Lab H2C", help="profile family; only the H2C is resolved")
    ap.add_argument("--exe")
    ap.add_argument("--profiles")
    ap.add_argument("--outdir")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    exe, prof = find_exe(a.exe), find_profiles(a.profiles)
    model = os.path.abspath(a.model)
    out = os.path.abspath(a.outdir or os.path.join(os.path.dirname(model), "slicer-check"))
    os.makedirs(out, exist_ok=True)
    if a.printer != "Bambu Lab H2C":
        sys.exit("Preset names are resolved for the H2C ('@BBL H2C'); extend pick() for other printers.")
    machine_name = "%s %s nozzle" % (a.printer, a.nozzle)
    if not os.path.exists("%s/machine/%s.json" % (prof, machine_name)):
        sys.exit("No machine preset %s" % machine_name)
    proc_name = pick(prof, "process", a.process or DEFAULT_PROCESS[a.nozzle], a.nozzle)
    fil_name = pick(prof, "filament", a.filament or MATS[a.material]["slicer"]["bbl_filament"], a.nozzle)
    bed = BEDS.get(a.bed.lower(), a.bed) if a.bed else MATS[a.material]["slicer"]["bed"]
    res = {"model": model, "material": a.material, "nozzle": a.nozzle, "bed": bed, "filament_profile": fil_name, "process": proc_name}

    def flat_copy(kind, name):  # newer Bambu bundles fail the CLI's vendor check; standalone presets load fine
        d = flatten(os.path.join(prof, kind), name)
        d.pop("inherits", None)
        d["from"] = "User"
        fp = os.path.join(out, "_flat", kind + ".json")
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        json.dump(d, open(fp, "w"), indent=1)
        return fp.replace("\\", "/"), d
    machine, _ = flat_copy("machine", machine_name)
    fil, _ = flat_copy("filament", fil_name)
    proc_flat, pdata = flat_copy("process", proc_name)
    fil2 = None
    if a.interface_filament:
        n2 = pick(prof, "filament", a.interface_filament, a.nozzle)
        d2 = flatten(os.path.join(prof, "filament"), n2); d2.pop("inherits", None); d2["from"] = "User"
        fil2 = os.path.join(out, "_flat", "filament2.json").replace("\\", "/")
        json.dump(d2, open(fil2, "w"), indent=1)
        res["interface_filament"] = n2
    res["layer_height"] = pdata.get("layer_height")

    code, txt = run([exe, "--info", model])
    info = dict(re.findall(r"^(\w+) = (\S+)", txt, re.M))
    res["geometry"] = {"size_mm": [float(info.get(k, 0)) for k in ("size_x", "size_y", "size_z")], "volume_mm3": float(info.get("volume", 0)),
                       "manifold": info.get("manifold") == "yes", "facets": int(info.get("number_of_facets", 0))}

    def slice_once(label, process_file, extra=(), two=False):
        d = os.path.join(out, label)
        shutil.rmtree(d, ignore_errors=True)
        c, t = run([exe, "--load-settings", "%s;%s" % (machine, process_file), "--load-filaments", fil + (";" + fil2 if two and fil2 else ""), "--curr-bed-type", bed,
                    *extra, "--slice", "1", "--outputdir", d, model])
        g = os.path.join(d, "plate_1.gcode")
        if c != 0 or not os.path.exists(g):
            return {"error": t.strip().splitlines()[-2:] or ["slice failed"]}, t
        st = gcode_stats(g)
        bt = re.findall(r"^M1(?:40|90) S(\d+)", open(g, encoding="utf-8", errors="replace").read(), re.M)
        st["bed_temp"] = int(bt[0]) if bt else None
        return st, t

    res["as_exported"], _ = slice_once("as-exported", proc_flat)
    sup = dict(pdata)
    sup.update({"name": "supports forced on", "enable_support": "1", "support_type": a.support_type})
    if a.on_plate_only:
        sup["support_on_build_plate_only"] = "1"
    res["support_gap_mm"] = clean_supports(sup, a.material, a.nozzle) if a.support_quality == "clean" else float(sup.get("support_top_z_distance", 0.2))
    pf = os.path.join(out, "process-supports.json")
    json.dump(sup, open(pf, "w"), indent=1)
    if fil2:
        sup["support_interface_filament"] = "2"
        sup["enable_prime_tower"] = "0"  # the CLI refuses the default 60 mm tower (outside the plate); no tower = estimate only, set the purge/tower in Bambu Studio for the real print
        json.dump(sup, open(pf, "w"), indent=1)
    res["supports_forced"], _ = slice_once("supports-on", pf.replace("\\", "/"), two=bool(fil2))
    res["supports_needed"] = None if "error" in res["supports_forced"] else res["supports_forced"]["support_lines"] > 0
    res["best_orientation"] = None
    c, t = run([exe, "--load-settings", "%s;%s" % (machine, proc_flat), "--load-filaments", fil, "--curr-bed-type", bed,
                "--orient", "1", "--slice", "1", "--outputdir", os.path.join(out, "oriented"), model])
    m = re.search(r"^best:\s*(-?[\d.]+)\s+(-?[\d.]+)\s+(-?[\d.]+)", t, re.M)
    if m:
        v = [float(x) for x in m.groups()]
        res["best_orientation"] = {"up_vector": v, "matches_export": abs(v[2] - 1) < 0.01 and abs(v[0]) < 0.01 and abs(v[1]) < 0.01}

    if a.json:
        print(json.dumps(res, indent=2)); return
    g = res["geometry"]
    print("%s in %s, %s mm nozzle (%s, %s, %s mm layers, %s bed)" % (os.path.basename(model), a.material, a.nozzle, fil_name, proc_name, res["layer_height"], bed))
    print("  geometry : %.1f x %.1f x %.1f mm, %.2f cm3, %s" % (*g["size_mm"], g["volume_mm3"] / 1000, "watertight" if g["manifold"] else "NOT WATERTIGHT: repair before printing"))
    e = res["as_exported"]
    print("  as exported: " + ("slice failed: %s" % e["error"] if "error" in e else "%s, %s g, %s layers, support lines: %d, bed %s C" % (e["time"], e["filament_g"], e["layers"], e["support_lines"], e["bed_temp"])))
    s = res["supports_forced"]
    if "error" not in s:
        print("  supports on (%s, %s, gap %.2f mm): %s, %s g, support lines: %d  ->  %s" % (a.support_type, a.support_quality, res["support_gap_mm"], s["time"], s["filament_g"], s["support_lines"],
              "supports ARE needed in this orientation" if res["supports_needed"] else "no support generated: this orientation needs none") + ("  [grams per filament: %s]" % s["filament_g_each"] if fil2 else ""))
    else:
        print("  supports on: slice failed: %s" % s["error"])
    b = res["best_orientation"]
    if b:
        print("  best orientation by the slicer: up = %s  ->  %s" % (b["up_vector"], "matches your export" if b["matches_export"] else "DIFFERS from your export: compare time and supports"))
    print("  G-code and logs in %s. Confirm in the slicer GUI before printing." % out)


if __name__ == "__main__":
    main()
