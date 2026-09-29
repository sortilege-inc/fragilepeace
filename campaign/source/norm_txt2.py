import re, sys, pathlib
lines = [l.strip() for l in pathlib.Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace").split("\n")]
out, i, n = [], 0, 0
while i < len(lines):
    m = re.match(r"^\[Speaker (\d+)\]:?$", lines[i])
    if m:
        spk = m.group(1); i += 1
        txt = []
        while i < len(lines) and not re.match(r"^\[Speaker \d+\]:?$", lines[i]):
            if lines[i]: txt.append(lines[i])
            i += 1
        if txt:
            n += 1
            out.append("%d|(S%s) %s" % (n, spk, " ".join(txt)))
    else:
        if lines[i]:
            n += 1
            out.append("%d|(cont) %s" % (n, lines[i]))
        i += 1
print("\n".join(out))
