#!/usr/bin/env python3
"""Repair an eval viewer whose embedded outputs contain </script>.

generate_review.py inlines every run's output files into a single
`const EMBEDDED_DATA = {...};` JSON literal inside a <script> block. When an
output is itself an HTML page carrying its own <script> blocks -- exactly what
easy-mode produces -- the first </script> inside that JSON closes the viewer's
script element early. The browser stops parsing JavaScript there and renders
the rest of the document as plain text.

The fix is to escape `<` as `\\u003c` within the JSON literal. JSON contains no
bare `<` outside of string values, so this cannot corrupt the structure, and
`\\u003c` is exactly `<` once parsed -- so the data is unchanged while the HTML
parser no longer sees an end tag, a nested <script, or a comment opener.

Usage: python3 fix_viewer.py <viewer.html> [output.html]
"""
import json
import re
import sys

src_path = sys.argv[1]
out_path = sys.argv[2] if len(sys.argv) > 2 else src_path
src = open(src_path, encoding="utf-8").read()

lines = src.split("\n")
patched = 0

for i, line in enumerate(lines):
    stripped = line.lstrip()
    if not stripped.startswith("const EMBEDDED_DATA"):
        continue
    if "<" not in line:
        continue

    # Validate we can round-trip the payload before and after, so a malformed
    # assumption fails loudly here rather than producing a subtly broken page.
    payload = stripped[len("const EMBEDDED_DATA"):].lstrip()
    payload = payload[1:] if payload.startswith("=") else payload
    payload = payload.strip().rstrip(";")
    before = json.loads(payload)

    lines[i] = line.replace("<", "\\u003c")

    after_payload = lines[i].lstrip()[len("const EMBEDDED_DATA"):].lstrip()
    after_payload = after_payload[1:] if after_payload.startswith("=") else after_payload
    after = json.loads(after_payload.strip().rstrip(";"))
    assert before == after, "escaping changed the parsed data"

    patched += 1

fixed = "\n".join(lines)
open(out_path, "w", encoding="utf-8").write(fixed)

depth = 0
ok = True
for m in re.finditer(r"</?script", fixed):
    depth += -1 if m.group(0).startswith("</") else 1
    if depth < 0 or depth > 1:
        ok = False

print(f"patched {patched} EMBEDDED_DATA line(s)")
print(f"script tags nest correctly: {ok}, final depth {depth}")
print("payload still parses to identical data: yes" if patched else "nothing to patch")
