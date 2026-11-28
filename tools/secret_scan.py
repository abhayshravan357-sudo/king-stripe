"""Lightweight high-confidence secret scan; reports locations only, never values."""
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = {
    "private_key": re.compile(rb"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "aws_access_key": re.compile(rb"\bAKIA[0-9A-Z]{16}\b"),
    "github_token": re.compile(rb"\bgh[pousr]_[A-Za-z0-9_]{30,}\b"),
    "stripe_secret": re.compile(rb"\bsk_(?:live|test)_[A-Za-z0-9]{16,}\b"),
    "razorpay_secret": re.compile(rb"RAZORPAY_KEY_SECRET\s*=\s*[^\s#]{12,}"),
    "database_url_password": re.compile(rb"postgres(?:ql)?(?:\+[a-z0-9]+)?://[^\s:/@]+:[^\s/@]{8,}@"),
}


def findings(name: str, content: bytes):
    if name.endswith(".env.example"):
        return []
    hits = []
    for line_no, line in enumerate(content.splitlines(), 1):
        for rule, pattern in RULES.items():
            if pattern.search(line):
                hits.append((rule, line_no))
    return hits


def working_tree():
    names = subprocess.check_output(["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT).split(b"\0")
    results = []
    for raw_name in filter(None, names):
        name = raw_name.decode("utf-8", "replace")
        path = ROOT / name
        if not path.is_file() or path.stat().st_size > 5_000_000:
            continue
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if b"\0" in data[:4096]:
            continue
        results.extend(("working tree", name, rule, line) for rule, line in findings(name, data))
    return results


def history():
    output = subprocess.check_output(["git", "log", "--all", "--format=", "--patch", "--", ".", ":(exclude)assets/**", ":(exclude)**/*.png", ":(exclude)**/*.jpg", ":(exclude)**/*.webp"], cwd=ROOT, stderr=subprocess.DEVNULL)
    results, filename, line_no = [], "history", 0
    for line in output.splitlines():
        if line.startswith(b"+++ b/"):
            filename = line[6:].decode("utf-8", "replace")
        elif line.startswith(b"@@"):
            match = re.search(rb"\+(\d+)", line)
            line_no = int(match.group(1)) if match else 0
        elif line.startswith(b"+") and not line.startswith(b"+++"):
            for rule, _ in findings(filename, line[1:]):
                results.append(("git history", filename, rule, line_no))
            line_no += 1
        elif line.startswith(b" "):
            line_no += 1
    return results


def main():
    results = working_tree() + history()
    if results:
        for source, filename, rule, line in results:
            print(f"Potential {rule}: {source} {filename}:{line}")
        return 1
    print("No high-confidence secret patterns found in the working tree or scanned Git text history.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
