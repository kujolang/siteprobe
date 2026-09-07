"""Verify generated source ZIPs using the platform's qualified Kujo runtime."""
import hashlib
import json
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
import zipfile


def main():
    dist, runtime = Path(sys.argv[1]), Path(sys.argv[2]).resolve()
    expected = Path("VERSION").read_text().strip()
    archives = sorted(dist.glob("*.zip"))
    if not archives:
        raise AssertionError("No release archives found")
    for archive in archives:
        checksum = archive.with_suffix(".zip.sha256").read_text().split()
        assert checksum == [hashlib.sha256(archive.read_bytes()).hexdigest(), archive.name]
        with tempfile.TemporaryDirectory(prefix="siteprobe-release-") as tmp:
            root = Path(tmp)
            with zipfile.ZipFile(archive) as bundle:
                names = bundle.namelist()
                assert all(not PurePosixPath(n).is_absolute() and ".." not in PurePosixPath(n).parts for n in names)
                assert "src/siteprobe.kujo" in names and "src/siteprobe.py" not in names
                assert "docs/audits/repository-hardening.md" in names
                assert "docs/release-qualification-" + expected + ".md" in names
                assert ".github/workflows/validate.yml" in names
                bundle.extractall(root)
            assert (root / "VERSION").read_text().strip() == expected
            for command in ["doctor", "version"]:
                result = subprocess.run([str(runtime), "run", "src/main.kujo", "--", command], cwd=root,
                                        capture_output=True, encoding="utf-8", check=True, timeout=30)
                receipt = json.loads(result.stdout)
                if command == "doctor":
                    assert receipt["ok"] and receipt["implementation"] == "kujo" and receipt["python"] is None
                else:
                    assert receipt["version"] == expected and receipt["contract"] == "siteprobe.run/v1"
        print("PASS " + archive.name + " checksum, extracted native doctor and version")


if __name__ == "__main__":
    main()
