"""Run a packaged EXE headlessly and verify the exported report bundle."""

import argparse
import csv
import hashlib
import json
import re
import subprocess
import tempfile
from collections import Counter
from itertools import zip_longest
from pathlib import Path, PurePosixPath

from rotary_melter.Paths import PROJECT_ROOT


LINK = re.compile(r"\]\(([^\s)]+)\)")
REFERENCE = "CALCULATION_EQUATIONS.md"


def local_links(document):
    return [target for target in LINK.findall(document.read_text(encoding="utf-8"))
            if not re.match(r"^(?:[\w+.-]+:|//|#)", target)]


def verify_catalogue(folder, exported_name, original_name):
    original = PROJECT_ROOT / "docs" / original_name
    expected_links = Counter()
    relocated_targets = {}
    attachments = set()
    for target in local_links(original):
        path, separator, anchor = target.partition("#")
        if path == REFERENCE:
            expected_links[target] += 1
            continue
        source = (original.parent / path).resolve()
        relative = source.relative_to(PROJECT_ROOT)
        attachment = PurePosixPath("source", relative.as_posix())
        relocated = attachment.as_posix() + separator + anchor
        relocated_targets[target] = relocated
        expected_links[relocated] += 1
        attachments.add(relative)

    actual_links = Counter(local_links(folder / exported_name))
    if actual_links != expected_links:
        raise ValueError(f"{exported_name} link mismatch. Missing: "
                         f"{dict(expected_links - actual_links)}. Unexpected: "
                         f"{dict(actual_links - expected_links)}")
    expected_text = LINK.sub(
        lambda match: f"]({relocated_targets.get(match[1], match[1])})",
        original.read_text(encoding="utf-8"),
    )
    if (folder / exported_name).read_text(encoding="utf-8") != expected_text:
        raise ValueError(f"{exported_name} catalogue content differs from checkout")
    for relative in sorted(attachments):
        if (folder / "source" / relative).read_bytes() != (PROJECT_ROOT / relative).read_bytes():
            raise ValueError(f"Source attachment differs from checkout: {relative}")
    return sum(expected_links.values()), len(attachments)


def verify_history(folder, samples):
    path = folder / "history.csv"
    if not samples:
        if path.exists() and path.stat().st_size:
            raise ValueError("history.csv contains data for a run without samples")
        return

    columns = list(dict.fromkeys(key for sample in samples for key in sample))
    with path.open(encoding="utf-8-sig", newline="") as stream:
        rows = csv.reader(stream, strict=True)
        if next(rows, None) != columns:
            raise ValueError("history.csv headers differ from result.json")
        for index, (row, sample) in enumerate(zip_longest(rows, samples), start=1):
            if row is None or sample is None:
                raise ValueError("history.csv sample count differs from result.json")
            expected = []
            for column in columns:
                value = sample.get(column, "")
                if isinstance(value, (list, dict)):
                    value = json.dumps(value, ensure_ascii=False)
                expected.append("" if value is None else str(value))
            if row != expected:
                raise ValueError(f"history.csv sample {index} differs from result.json")
    print(f"history.csv: {len(samples)} matching samples, {len(columns)} columns")


def verify_report(folder):
    report = folder / "RUN_REPORT.md"
    if "EQUATIONS.md" not in local_links(report):
        raise ValueError("RUN_REPORT.md has no link to EQUATIONS.md")

    manifest = json.loads((folder / "run_manifest.json").read_text(encoding="utf-8"))
    if (not isinstance(manifest, dict) or manifest.get("engine") != "Rotary Melter C++"
            or manifest.get("cancelled") is not False):
        raise ValueError("Manifest does not describe a completed C++ run")
    payload = (folder / "result.json").read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    if manifest.get("resultSha256") != digest:
        raise ValueError("Manifest SHA-256 differs from result.json")
    if f"- Result JSON SHA-256: `{digest}`" not in report.read_text(encoding="utf-8").splitlines():
        raise ValueError("RUN_REPORT.md SHA-256 differs from result.json")

    verify_history(folder, json.loads(payload).get("hist", []))

    for exported, original in (("EQUATIONS.md", "CPP_CALCULATION_EQUATIONS.md"),
                               (REFERENCE, REFERENCE)):
        link_count, file_count = verify_catalogue(folder, exported, original)
        print(f"{exported}: {link_count} local links, {file_count} matching source attachments")
    print(f"result.json SHA-256: {digest}")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("exe", type=Path, help="Path to the packaged Rotary Melter EXE")
    args = parser.parse_args(argv)
    exe = args.exe.resolve()
    if exe.suffix.lower() != ".exe" or not exe.is_file():
        parser.error(f"EXE file not found: {exe}")

    work = PROJECT_ROOT / ".autodev"
    work.mkdir(exist_ok=True)
    folder = Path(tempfile.mkdtemp(prefix="verify-desktop-", dir=work))
    print(f"Report output: {folder}", flush=True)
    try:
        subprocess.run([str(exe), "--run", "--output", str(folder)], cwd=folder,
                       check=True, timeout=120,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        verify_report(folder)
    except (OSError, ValueError, csv.Error, subprocess.SubprocessError) as error:
        parser.exit(1, f"Package verification failed: {error}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
