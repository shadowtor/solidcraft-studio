#!/usr/bin/env python3
"""Print a filament's design numbers, and the SolidCraft steps that create them as parameters.

  python print_profile.py PETG            # table
  python print_profile.py ASA --nozzle 0.6   # walls and features scale with the nozzle
  python print_profile.py ASA --batch     # JSON `batch` steps (parameters.change) to send to solidcraft

Fits are DIAMETRAL (total across both sides): fit = base + material offset. See references/materials.md.
"""
import json, os, sys

D = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets", "materials.json"), encoding="utf-8"))


def profile(name, nozzle=0.4):
    m = D["materials"].get(name.upper().replace("_", "-"))
    if not m:
        sys.exit(f"unknown material {name}; one of: {', '.join(D['materials'])}")
    b, o = D["fit_base_diametral_mm"], m["fit_offset_mm"]
    r = lambda x: round(x, 3)
    return m, {"fit_press": r(b["press"] + o), "fit_close": r(b["close"] + o), "fit_free": r(b["free"] + o),
               "min_wall": max(0.8, r(m["min_wall_mm"] * nozzle / 0.4)), "min_feature": r(m["min_feature_mm"] * nozzle / 0.4), "hole_comp": m["hole_comp_mm"],
               "overhang_max": m["overhang_max_deg"], "bridge_max": m["bridge_max_mm"]}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    nz = float(sys.argv[sys.argv.index("--nozzle") + 1]) if "--nozzle" in sys.argv else 0.4
    m, p = profile(sys.argv[1], nz)
    if "--batch" in sys.argv:
        # ponytail: assumes parameters.change creates a missing parameter; if solidcraft refuses, run describe_command parameters.change
        print(json.dumps({"commands": [{"command": "parameters.change", "params": {"name": k, "expression": f"{round(v, 3)} mm" if k not in ("overhang_max",) else f"{v} deg"}} for k, v in p.items()]}, indent=1))
    else:
        for k, v in p.items():
            print(f"{k:14} {v}")
        print(f"slicer         {m['slicer']['bbl_filament']} on {m['slicer']['bed']}")
        print(f"enclosure      {'yes (warps in drafts)' if m['enclosure'] else 'not required'}")
        for n in m["notes"]:
            print(" -", n)
