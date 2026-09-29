#!/usr/bin/env python3
"""The creator's heritage table against the corpus — both directions.

system/l5r5e/heritage-rules.js names, per heritage entry, what the result obliges the player to
settle (ported from the pregens archive's scripts/heritage_tables.py). The creator reads every
HERITAGE_TABLE in the corpus; this fails the build when:

  * an entry grants something the creator cannot ask for: it is not in REQUIRES, and its
    SUB_TABLE ranges do not all read as core skills ("Gain +1 ^"Composition"", "Tactics");
  * an entry with an EFFECT and no sub-table is not in REQUIRES (an effect nobody handles);
  * a REQUIRES key names a table or an entry the corpus does not print;
  * REQUIRES says sub="skill" and a range does not read as a skill, or declares a sub-table
    reading for an entry that has none;
  * a peculiarity REQUIRES grants is not an advantage or disadvantage the corpus defines.

    python3 build/check_chargen.py
"""
import glob, json, os, re, sys, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_data():
    ents = {}
    for p in glob.glob(os.path.join(ROOT, "data", "*.js")):
        txt = open(p, encoding="utf-8").read()
        if "var d=" not in txt:
            continue
        # `var d={…};var T=window.L5R5E=…` — the object is the first JSON value after `var d=`
        d, _ = json.JSONDecoder().raw_decode(txt, txt.index("var d=") + 6)
        ents.update(d.get("entities", {}))
    return ents


def rules():
    txt = open(os.path.join(ROOT, "system", "l5r5e", "heritage-rules.js"), encoding="utf-8").read()
    txt = txt[txt.index("window.L5RHeritageRules ="):]
    return json.loads(txt[txt.index("=") + 1:].strip().rstrip(";"))


def norm(s):
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s.replace("’", "'").lower()).strip()


def block(e, kw):
    return next((b for b in e.get("blocks") or [] if b.get("kw") == kw), None)


def main():
    E = load_data()
    R = rules()
    req = R["REQUIRES"]
    skills = {e["name"] for e in E.values() if e["file"].endswith("core-traits.ttrpg") and block(e, "SKILL_GROUP")}
    pec_types = ("Distinction", "Adversity", "Passion", "Anxiety")
    pecs = {re.sub(r"\s*\((air|earth|fire|water|void)\)\s*$", "", norm(e["name"])) for e in E.values() if e.get("type") in pec_types}

    def as_skill(t):
        t = re.sub(r'\^"([^"]*)"', r"\1", t).strip().rstrip(".")
        m = re.match(r"^Gain\s*\+\s*1\s+(.+)$", t, re.I)
        if m:
            t = m.group(1).strip()
        return t == "Martial Arts [Choose One]" or t in skills

    problems, tables, entries = [], {}, 0
    for t in E.values():
        hb = block(t, "HERITAGE_TABLE")
        if not hb:
            continue
        rows = []
        for x in hb.get("body") or []:
            if x.get("num") is not None and x.get("def"):
                rows.append((x["args"][0]["c"], x.get("body") or []))
            elif x.get("ent") and x["ent"] in E:
                rows.append((E[x["ent"]]["name"], E[x["ent"]].get("blocks") or []))
        if len(rows) < 2:
            continue
        tables[t["name"]] = {n for n, _ in rows}
        spec_t = req.get(t["name"], {})
        for name, body in rows:
            entries += 1
            spec = spec_t.get(name)
            st = next((b for b in body if b.get("kw") == "SUB_TABLE"), None)
            eff = next((b for b in body if b.get("kw") == "EFFECT"), None)
            strs = [y["s"] for y in (st or {}).get("body", []) if "s" in y]
            ranges = strs[1::2]
            how = (spec or {}).get("sub", "skill")
            if st and how == "skill":
                bad = [r for r in ranges if not as_skill(r)]
                if bad:
                    problems.append(f"{t['name']} / {name}: sub-table range(s) neither a skill nor declared in REQUIRES — {bad!r}")
            if not st and spec and "sub" in spec:
                problems.append(f"{t['name']} / {name}: REQUIRES declares sub={how!r} but the entry has no sub-table")
            if eff and not st and spec is None:
                problems.append(f"{t['name']} / {name}: has an EFFECT, no sub-table and no REQUIRES entry")
            for r in (spec or {}).get("requires", []):
                for q in [r] + r.get("options", []) if r.get("kind") == "pick_one" else [r]:
                    if q.get("kind") == "peculiarity":
                        for n in ([q["name"]] if q.get("name") else q.get("options", [])):
                            if norm(n) not in pecs:
                                problems.append(f"{t['name']} / {name}: REQUIRES grants {n!r}, which the corpus does not define")
    for tname, spec_t in req.items():
        if tname not in tables:
            problems.append(f"REQUIRES names a table the corpus does not print: {tname!r}")
            continue
        for ename in spec_t:
            if ename not in tables[tname]:
                problems.append(f"REQUIRES names an entry {tname!r} does not print: {ename!r}")
    print(f"check_chargen: {len(tables)} heritage tables, {entries} entries, {sum(len(v) for v in req.values())} with a REQUIRES entry")
    if problems:
        for p in problems:
            print("   ", p)
        sys.exit(f"check_chargen: {len(problems)} problem(s)")
    print("check_chargen: OK")


if __name__ == "__main__":
    main()
