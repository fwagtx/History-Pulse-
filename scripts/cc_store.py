"""Where the finished videos live: a Cloudflare R2 bucket (free tier), in place
of the GitHub releases the pipeline used before. Metricool picks each video up
from the bucket's public URL, exactly as it did from a release.

Settings. The two keys only ever come from the environment's variables (they
are secrets); the other three aren't secret, so they live in
creator-code/storage.json, and an environment variable of the same name wins:

    AWS_ACCESS_KEY_ID      an R2 API token's Access Key ID (32 characters)
    AWS_SECRET_ACCESS_KEY  that token's Secret Access Key (64 characters)
    R2_ACCOUNT_ID          the Cloudflare account id (32 hex characters)   storage.json "account_id"
    R2_BUCKET              the bucket's name                               storage.json "bucket"
    R2_PUBLIC_URL          its public URL, e.g. https://pub-....r2.dev     storage.json "public_url"

A "tag" (shop-2026-10-01, quiz-2026-10-14, music-library, cosmetics-data) is a
folder in the bucket, the way it was a release on GitHub. Without the R2
settings everything falls back to the GitHub release URLs.

    python3 scripts/cc_store.py check                 # can we reach and write the bucket?
    python3 scripts/cc_store.py put DIR TAG [GLOB..]  # upload DIR's files into TAG/
    python3 scripts/cc_store.py ls [TAG]
    python3 scripts/cc_store.py cat TAG/FILE
    python3 scripts/cc_store.py has TAG/FILE          # exit 0 if it's there
"""
import json
import mimetypes
import os
import sys
from pathlib import Path

GITHUB = "https://github.com/{repo}/releases/download/{tag}/"
REPO = os.environ.get("GITHUB_REPOSITORY", "fwagtx/History-Pulse-")
CONFIG = Path(__file__).resolve().parent.parent / "creator-code" / "storage.json"
FIELDS = {"R2_ACCOUNT_ID": "account_id", "R2_BUCKET": "bucket", "R2_PUBLIC_URL": "public_url"}
TYPES = {".mp4": "video/mp4", ".webm": "video/webm", ".png": "image/png", ".jpg": "image/jpeg",
         ".json": "application/json", ".mp3": "audio/mpeg", ".gz": "application/gzip"}


def setting(name: str) -> str:
    """A setting: the environment's variable, else (for the three that aren't
    secret) creator-code/storage.json's field."""
    if os.environ.get(name):
        return os.environ[name]
    if name not in FIELDS:
        return ""
    try:
        return str(json.loads(CONFIG.read_text()).get(FIELDS[name]) or "")
    except (OSError, ValueError):
        return ""


def enabled() -> bool:
    return all(setting(k) for k in ("R2_ACCOUNT_ID", "AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY",
                                     "R2_BUCKET", "R2_PUBLIC_URL"))


def base_url(tag: str) -> str:
    """The public folder URL for a tag, ending in '/'."""
    if enabled():
        return f"{setting('R2_PUBLIC_URL').rstrip('/')}/{tag}/"
    return GITHUB.format(repo=REPO, tag=tag)


_S3 = None


def _client():
    global _S3
    if _S3 is None:
        try:
            import boto3
        except ImportError:
            import subprocess
            subprocess.run([sys.executable, "-m", "pip", "install", "-q", "boto3"], check=True)
            import boto3
        from botocore.config import Config
        endpoint = os.environ.get("R2_ENDPOINT") or f"https://{setting('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com"
        _S3 = boto3.client("s3", endpoint_url=endpoint,
                           region_name="auto",
                           config=Config(retries={"max_attempts": 5, "mode": "standard"}, connect_timeout=20,
                                         read_timeout=120))
    return _S3


def _bucket() -> str:
    return setting("R2_BUCKET")


def put(path: Path, key: str) -> str:
    """Upload one file to `key`; its public URL."""
    path = Path(path)
    ctype = TYPES.get(path.suffix.lower()) or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    # Manifests change on a rebuild; the media never change under the same name.
    cache = "no-cache" if path.suffix == ".json" else "public, max-age=604800"
    _client().upload_file(str(path), _bucket(), key, ExtraArgs={"ContentType": ctype, "CacheControl": cache})
    return f"{setting('R2_PUBLIC_URL').rstrip('/')}/{key}"


def put_dir(folder: Path, tag: str, patterns=("*",)) -> list:
    """Upload the files in `folder` matching `patterns` into tag/, the manifest
    last (so a reader never finds a manifest whose videos aren't there yet)."""
    files = sorted({f for p in patterns for f in Path(folder).glob(p) if f.is_file()},
                   key=lambda f: (f.name == "manifest.json", f.name))
    return [put(f, f"{tag}/{f.name}") for f in files]


def get(key: str) -> bytes:
    return _client().get_object(Bucket=_bucket(), Key=key)["Body"].read()


def exists(key: str) -> bool:
    try:
        _client().head_object(Bucket=_bucket(), Key=key)
        return True
    except Exception:  # noqa: BLE001 - missing, or unreachable: either way not there for us
        return False


def ls(prefix: str = "") -> list:
    out, token = [], None
    while True:
        kw = {"Bucket": _bucket(), "Prefix": prefix}
        if token:
            kw["ContinuationToken"] = token
        r = _client().list_objects_v2(**kw)
        out += [(o["Key"], o["Size"]) for o in r.get("Contents", [])]
        if not r.get("IsTruncated"):
            return out
        token = r["NextContinuationToken"]


def fetch(tag: str, name: str, timeout: int = 120) -> bytes:
    """A published file: from the bucket when R2 is set up, else the GitHub release."""
    if enabled():
        return get(f"{tag}/{name}")
    import urllib.request
    req = urllib.request.Request(GITHUB.format(repo=REPO, tag=tag) + name, headers={"User-Agent": "usecodebad"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def check() -> list:
    """What's missing or wrong, in plain words ([] = ready)."""
    problems = []
    for k, n in (("R2_ACCOUNT_ID", 32), ("AWS_ACCESS_KEY_ID", 32), ("AWS_SECRET_ACCESS_KEY", 64)):
        v = setting(k)
        if not v:
            problems.append(f"{k} isn't set")
        elif len(v) != n:
            problems.append(f"{k} is {len(v)} characters; an R2 one is {n} (is it a placeholder?)")
    for k in ("R2_BUCKET", "R2_PUBLIC_URL"):
        if not setting(k):
            problems.append(f"{k} isn't set")
    if problems:
        return problems
    try:
        import tempfile
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write('{"ok": true}')
        put(Path(f.name), "_check/ok.json")
        assert get("_check/ok.json") == b'{"ok": true}'
        _client().delete_object(Bucket=_bucket(), Key="_check/ok.json")
    except Exception as e:  # noqa: BLE001
        msg = str(e)
        for k in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"):
            msg = msg.replace(os.environ.get(k) or "\0", "***")
        problems.append(f"writing to the bucket failed: {msg[:240]}")
    return problems


def main(argv: list) -> int:
    cmd = argv[1] if len(argv) > 1 else "check"
    if cmd == "check":
        problems = check()
        print("R2 is ready." if not problems else "R2 isn't ready:\n  " + "\n  ".join(problems))
        return 1 if problems else 0
    if cmd == "put":
        urls = put_dir(Path(argv[2]), argv[3], tuple(argv[4:]) or ("*",))
        print("\n".join(urls))
        return 0
    if cmd == "ls":
        for k, size in ls(argv[2] if len(argv) > 2 else ""):
            print(f"{size:>12,}  {k}")
        return 0
    if cmd == "cat":
        sys.stdout.buffer.write(get(argv[2]))
        return 0
    if cmd == "has":
        return 0 if exists(argv[2]) else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
