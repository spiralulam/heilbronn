"""Remove license data from Gurobi logs before they are published.

Gurobi prints the license number and the registered name or e-mail address
(e.g. "Academic license 1234567 - for non-commercial use only - registered to ...",
"WLS license ..." or "Set parameter WLSAccessID"). This script replaces every
such line, and any remaining e-mail address, by a fixed marker, in place. It
also shortens home-directory paths (/Users/<name>/...) to ~/...

    python3 redact_logs.py out/logs/*.log batch.log
"""
import re
import sys
from pathlib import Path

LINE = re.compile(r"license|registered to|WLSAccessID|WLSSecret|LicenseID", re.I)
MAIL = re.compile(r"[\w.+-]+@[\w-]+(\.[\w-]+)+")
HOME = re.compile(r"(/Users|/home)/[^/\s\"]+/")
MARK = "[license information removed]"


def redact(path):
    lines = Path(path).read_text(errors="replace").splitlines(keepends=True)
    out, hits = [], 0
    for l in lines:
        new = MARK + "\n" if LINE.search(l) else HOME.sub("~/", MAIL.sub("[e-mail removed]", l))
        hits += new != l
        out.append(new)
    Path(path).write_text("".join(out))
    return hits


if __name__ == "__main__":
    for p in sys.argv[1:]:
        print(f"{p}: {redact(p)} lines redacted")
