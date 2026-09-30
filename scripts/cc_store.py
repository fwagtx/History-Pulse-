"""Where the finished videos live: a Cloudflare R2 bucket (free tier), in place
of the GitHub releases the pipeline used before. Metricool picks each video up
from the bucket's public URL, exactly as it did from a release.

Settings, all Code Bad's own. Nothing is read from a generic name that another
project sharing the workspace could set (R2_BUCKET, R2_PUBLIC_URL, R2_ACCOUNT_ID,
R2_ACCESS_KEY_ID ... are ignored):

    creator-code/storage.json      the bucket's name, the Cloudflare account id and
                                   its public URL (not secrets, so committed)
    CODEBAD_R2_ACCESS_KEY_ID       the usecodebad-pipelineR2 token's Access Key ID
    CODEBAD_R2_SECRET_ACCESS_KEY   that token's Secret Access Key

The key is the only setting in the environment (it is a secret). Until the
CODEBAD_ names are set, AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY are used.
Either way nothing is built unless the key can write, read and delete in Code
Bad's bucket (check()), so a key for anything else stops the build.

A "tag" (shop-2026-10-01, quiz-2026-10-14, music-library, cosmetics-data) is a
folder in the bucket, the way it was a release on GitHub. Without the R2
settings everything falls back to the GitHub release URLs.

Writing needs the keys; reading doesn't. Without them a file comes from the
bucket's public URL, and where that can't be reached (a workspace whose network
access leaves out r2.dev), a folder's manifest and its list of files come from
the copy the nightly build commits to creator-code/published/<tag>.json once
every file in the folder is checked in the bucket. That is how the 7 AM Routine,
which runs in a workspace without the keys, reads what the nightly build made.

    python3 scripts/cc_store.py check                 # can we reach and write the bucket?
    python3 scripts/cc_store.py where                 # which bucket, link and key are in use
    python3 scripts/cc_store.py put DIR TAG [GLOB..]  # upload DIR's files into TAG/
    python3 scripts/cc_store.py ls [TAG]
    python3 scripts/cc_store.py cat TAG/FILE
    python3 scripts/cc_store.py has TAG/FILE          # exit 0 if it's there
"""
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

GITHUB = "https://github.com/{repo}/releases/download/{tag}/"
REPO = os.environ.get("GITHUB_REPOSITORY", "fwagtx/History-Pulse-")
CONFIG = Path(__file__).resolve().parent.parent / "creator-code" / "storage.json"
PUBLISHED = CONFIG.parent / "published"
FIELDS = {"R2_ACCOUNT_ID": "account_id", "R2_BUCKET": "bucket", "R2_PUBLIC_URL": "public_url"}
KEY_NAMES = (("CODEBAD_R2_ACCESS_KEY_ID", "CODEBAD_R2_SECRET_ACCESS_KEY"),   # Code Bad's own
             ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"))                # the older names
TYPES = {".mp4": "video/mp4", ".webm": "video/webm", ".png": "image/png", ".jpg": "image/jpeg",
         ".json": "application/json", ".mp3": "audio/mpeg", ".gz": "application/gzip"}


def setting(name: str) -> str:
    """One of the bucket's three settings, from creator-code/storage.json only
    (never the environment's variable of the same name)."""
    if name not in FIELDS:
        return ""
    try:
        return str(json.loads(CONFIG.read_text()).get(FIELDS[name]) or "")
    except (OSError, ValueError):
        return ""


def keys() -> tuple:
    """(access key id, secret, where they came from): Code Bad's own variable
    names first, then the older ones; ("", "", "") if neither pair is set."""
    for kid, secret in KEY_NAMES:
        if os.environ.get(kid) and os.environ.get(secret):
            return os.environ[kid], os.environ[secret], f"{kid} / {secret}"
    return "", "", ""


def enabled() -> bool:
    """Things are published to the bucket (its settings are there)."""
    return all(setting(k) for k in ("R2_ACCOUNT_ID", "R2_BUCKET", "R2_PUBLIC_URL"))


def has_keys() -> bool:
    """We can write to the bucket (and read it directly)."""
    return bool(keys()[0])


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
        endpoint = os.environ.get("CC_R2_ENDPOINT") or f"https://{setting('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com"
        kid, secret, _ = keys()
        _S3 = boto3.client("s3", endpoint_url=endpoint, aws_access_key_id=kid, aws_secret_access_key=secret,
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


def _matching(folder: Path, patterns) -> list:
    """`folder`'s files matching `patterns`, the manifest last."""
    return sorted({f for p in patterns for f in Path(folder).glob(p) if f.is_file()},
                  key=lambda f: (f.name == "manifest.json", f.name))


def put_dir(folder: Path, tag: str, patterns=("*",)) -> list:
    """Upload the files in `folder` matching `patterns` into tag/, the manifest
    last (so a reader never finds a manifest whose videos aren't there yet)."""
    return [put(f, f"{tag}/{f.name}") for f in _matching(folder, patterns)]


def record(tag: str, local: Path | None = None) -> Path:
    """Write the repo's copy of tag/ (PUBLISHED/<tag>.json) from what is in the
    bucket: its files with their sizes - with `local`, the build's folder, only
    those at the built size - and its manifest. The caller commits it."""
    files = {k.split("/", 1)[1]: size for k, size in ls(f"{tag}/")}
    if local is not None:
        files = {n: size for n, size in files.items()
                 if (Path(local) / n).is_file() and (Path(local) / n).stat().st_size == size}
    rec = {"tag": tag, "url": base_url(tag),
           "checked_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "files": files}
    if "manifest.json" in files:
        rec["manifest"] = json.loads(get(f"{tag}/manifest.json"))
    PUBLISHED.mkdir(parents=True, exist_ok=True)
    out = PUBLISHED / f"{tag}.json"
    out.write_text(json.dumps(rec, indent=1, ensure_ascii=False) + "\n")
    return out


def _published(tag: str) -> dict:
    """The repo's copy of what the nightly build published to tag/ ({} if none)."""
    try:
        return json.loads((PUBLISHED / f"{tag}.json").read_text())
    except (OSError, ValueError):
        return {}


def _public(key: str, timeout: int = 120, first_byte: bool = False) -> bytes:
    """A file from the bucket's public URL (what Metricool fetches)."""
    headers = {"User-Agent": "usecodebad"}
    if first_byte:
        headers["Range"] = "bytes=0-0"
    req = urllib.request.Request(f"{setting('R2_PUBLIC_URL').rstrip('/')}/{key}", headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def get(key: str, timeout: int = 120) -> bytes:
    """A file in the bucket: with the keys straight from it; without them from its
    public URL, or, where that can't be reached, a manifest from the repo's copy."""
    if has_keys():
        return _client().get_object(Bucket=_bucket(), Key=key)["Body"].read()
    try:
        return _public(key, timeout)
    except urllib.error.HTTPError:
        raise  # the bucket answered: it isn't there (or isn't public)
    except OSError:  # this machine can't reach it
        tag, _, name = key.partition("/")
        rec = _published(tag)
        if name != "manifest.json" or "manifest" not in rec:
            raise
        return json.dumps(rec["manifest"], indent=1, ensure_ascii=False).encode()


def exists(key: str) -> bool:
    if has_keys():
        try:
            _client().head_object(Bucket=_bucket(), Key=key)
            return True
        except Exception:  # noqa: BLE001 - missing, or unreachable: either way not there for us
            return False
    try:
        _public(key, 30, first_byte=True)
        return True
    except urllib.error.HTTPError:
        return False
    except OSError:  # can't reach the public URL from here: the repo's copy says
        tag, _, name = key.partition("/")
        return name in _published(tag).get("files", {})


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
        return get(f"{tag}/{name}", timeout)
    req = urllib.request.Request(GITHUB.format(repo=REPO, tag=tag) + name, headers={"User-Agent": "usecodebad"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def check() -> list:
    """What's missing or wrong, in plain words ([] = ready)."""
    problems = []
    kid, secret, names = keys()
    if not kid:
        problems.append("the bucket's key isn't set: CODEBAD_R2_ACCESS_KEY_ID and CODEBAD_R2_SECRET_ACCESS_KEY "
                        "(the usecodebad-pipelineR2 token) in the workspace's environment variables")
    else:
        for label, v, n in (("access key id", kid, 32), ("secret access key", secret, 64)):
            if len(v) != n:
                problems.append(f"the {label} ({names}) is {len(v)} characters; an R2 one is {n} "
                                "(is it a placeholder?)")
    for k in ("R2_ACCOUNT_ID", "R2_BUCKET", "R2_PUBLIC_URL"):
        if not setting(k):
            problems.append(f"creator-code/storage.json has no {FIELDS[k]}")
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
        msg = str(e).replace(kid, "***").replace(secret, "***")
        problems.append(f"writing to {setting('R2_BUCKET')} with the key in {names} failed: {msg[:240]}")
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
    if cmd == "where":
        print(f"bucket:      {setting('R2_BUCKET')}  (creator-code/storage.json)")
        print(f"public link: {setting('R2_PUBLIC_URL')}  (creator-code/storage.json)")
        print(f"key:         {keys()[2] or 'not set (CODEBAD_R2_ACCESS_KEY_ID / CODEBAD_R2_SECRET_ACCESS_KEY)'}")
        ignored = [k for k in (*FIELDS, "R2_ENDPOINT", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY") if os.environ.get(k)]
        if ignored:
            print(f"ignored:     {', '.join(ignored)} (set in this environment; Code Bad doesn't read them)")
        return 0
    if cmd == "ls":
        if not has_keys():
            print("Listing the bucket needs its key (CODEBAD_R2_ACCESS_KEY_ID, CODEBAD_R2_SECRET_ACCESS_KEY).")
            return 1
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
