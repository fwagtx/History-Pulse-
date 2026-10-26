"""Where the finished videos live: GitHub releases of this repository, or a
Cloudflare R2 bucket (free tier), which took over while GitHub's Actions and
releases were unavailable to the account (2026-09-29 to 2026-10-26).

Which one is the mode (mode()):
  - a build on GitHub's own machines (GitHub Actions) always publishes to releases;
  - everywhere else, creator-code/storage.json's "use" decides: "github" or "r2"
    (without the bucket's settings it is GitHub).
In GitHub mode a "tag" is a release and a file is one of its assets, at
https://github.com/<repo>/releases/download/<tag>/<file>: public, permanent, and
what Metricool imports from. The workflows publish the releases (gh release);
nothing is uploaded from here. Reading needs no key, and the same commands
below work in both modes.

Settings for the bucket, all Code Bad's own. Nothing is read from a generic name that another
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
    python3 scripts/cc_store.py link TAG/FILE [SECS]  # a temporary link Metricool can import from
    python3 scripts/cc_store.py links TAG [SECS]      # the same for every video and cover in TAG/, as JSON

Metricool imports each post's video when the post is scheduled. Since 2026-10-01 it
often can't fetch from the bucket's public r2.dev link (Cloudflare rate-limits that
development address), so the daily job hands it a signed link instead (link): the
same file through R2's main storage address, readable by anyone holding the link
for a few hours, and only that file. The link carries the key's ID (not its
secret) and a signature.
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


def mode() -> str:
    """Where videos are published and read: "github" (releases) or "r2" (the bucket).
    GitHub Actions always uses releases; elsewhere storage.json's "use" decides."""
    if os.environ.get("GITHUB_ACTIONS") == "true":
        return "github"
    try:
        use = str(json.loads(CONFIG.read_text()).get("use") or "").strip().lower()
    except (OSError, ValueError):
        use = ""
    if use == "github":
        return "github"
    return "r2" if all(setting(k) for k in ("R2_ACCOUNT_ID", "R2_BUCKET", "R2_PUBLIC_URL")) else "github"


def enabled() -> bool:
    """Things are published to the bucket (R2 mode)."""
    return mode() == "r2"


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
    if not enabled():
        raise RuntimeError("GitHub mode: the workflows publish the releases (gh release); "
                           "nothing is uploaded from here")
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


def _github(key: str, timeout: int = 120, first_byte: bool = False) -> bytes:
    """A file from its GitHub release (GitHub mode)."""
    tag, _, name = key.partition("/")
    headers = {"User-Agent": "usecodebad"}
    if first_byte:
        headers["Range"] = "bytes=0-0"
    req = urllib.request.Request(GITHUB.format(repo=REPO, tag=tag) + name, headers=headers)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def _github_assets(tag: str) -> list:
    """[(file name, size)] of one release, from GitHub's API ([] if there's no such release).
    Asked without a token: the few calls a day stay far inside GitHub's limit."""
    req = urllib.request.Request(f"https://api.github.com/repos/{REPO}/releases/tags/{tag}",
                                 headers={"User-Agent": "usecodebad", "Accept": "application/vnd.github+json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            release = json.loads(r.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return []
        raise
    return [(a["name"], a["size"]) for a in release.get("assets", [])]


def get(key: str, timeout: int = 120) -> bytes:
    """A published file. GitHub mode: from its release. R2 mode: with the keys straight
    from the bucket, without them from its public URL. Where neither can be reached
    from this machine, a manifest comes from the repo's copy."""
    if enabled() and has_keys():
        return _client().get_object(Bucket=_bucket(), Key=key)["Body"].read()
    try:
        return (_public if enabled() else _github)(key, timeout)
    except urllib.error.HTTPError:
        raise  # the bucket answered: it isn't there (or isn't public)
    except OSError:  # this machine can't reach it
        tag, _, name = key.partition("/")
        rec = _published(tag)
        if name != "manifest.json" or "manifest" not in rec:
            raise
        return json.dumps(rec["manifest"], indent=1, ensure_ascii=False).encode()


def exists(key: str) -> bool:
    if enabled() and has_keys():
        try:
            _client().head_object(Bucket=_bucket(), Key=key)
            return True
        except Exception:  # noqa: BLE001 - missing, or unreachable: either way not there for us
            return False
    try:
        (_public if enabled() else _github)(key, 30, first_byte=True)
        return True
    except urllib.error.HTTPError:
        return False
    except OSError:  # can't reach the public URL from here: the repo's copy says
        tag, _, name = key.partition("/")
        return name in _published(tag).get("files", {})


def ls(prefix: str = "") -> list:
    if not enabled():   # GitHub mode: one release, its assets
        tag, _, start = prefix.partition("/")
        if not tag:
            raise ValueError("GitHub mode lists one release at a time: ls TAG")
        return [(f"{tag}/{n}", size) for n, size in _github_assets(tag) if n.startswith(start)]
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


def link(key: str, seconds: int = 6 * 3600) -> str:
    """A link Metricool can import one file from. GitHub mode: the release's own
    (public, permanent) URL. R2 mode: a signed, read-only link, valid for `seconds`."""
    if not exists(key):
        raise FileNotFoundError(f"{key} isn't published")
    if not enabled():
        tag, _, name = key.partition("/")
        return GITHUB.format(repo=REPO, tag=tag) + name
    return _client().generate_presigned_url("get_object", Params={"Bucket": _bucket(), "Key": key},
                                             ExpiresIn=int(seconds))


MEDIA = (".mp4", ".png", ".jpg", ".jpeg")


def links(tag: str, seconds: int = 6 * 3600) -> dict:
    """Links to every video and cover in one folder, {file name: link}: what the daily
    job needs for a day's posts, in one command it can run exactly as the permission file allows.
    GitHub mode: the release URLs of the files its manifest lists. R2 mode: signed links."""
    tag = tag.strip("/")
    if not enabled():
        m = json.loads(get(f"{tag}/manifest.json"))
        names = {str(e[k]).rsplit("/", 1)[-1] for e in (m.get("videos") or []) + (m.get("long_videos") or [])
                 for k in ("url", "cover_url", "thumbnail_url") if e.get(k)}
        return {n: GITHUB.format(repo=REPO, tag=tag) + n for n in sorted(names)
                if n.lower().endswith(MEDIA) and "-qa." not in n}
    return {key.split("/", 1)[1]: _client().generate_presigned_url(
                "get_object", Params={"Bucket": _bucket(), "Key": key}, ExpiresIn=int(seconds))
            for key, _size in ls(tag + "/") if key.lower().endswith(MEDIA) and "-qa." not in key}


def check() -> list:
    """What's missing or wrong, in plain words ([] = ready)."""
    if not enabled():   # GitHub mode: the workflows publish; here we only read releases
        try:
            json.loads(_github("music-library/catalog.json", 60))
            return []
        except Exception as e:  # noqa: BLE001
            return [f"can't read this repository's GitHub releases from here: {str(e)[:200]}"]
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
        what = "R2" if enabled() else f"Reading the GitHub releases of {REPO}"
        print(f"{what} is ready." if not problems else f"{what} isn't ready:\n  " + "\n  ".join(problems))
        return 1 if problems else 0
    if cmd == "put":
        urls = put_dir(Path(argv[2]), argv[3], tuple(argv[4:]) or ("*",))
        print("\n".join(urls))
        return 0
    if cmd == "where":
        print(f"mode:        {mode()}  ({'GitHub Actions' if os.environ.get('GITHUB_ACTIONS') == 'true' else 'creator-code/storage.json'})")
        if not enabled():
            print(f"releases:    https://github.com/{REPO}/releases")
            return 0
        print(f"bucket:      {setting('R2_BUCKET')}  (creator-code/storage.json)")
        print(f"public link: {setting('R2_PUBLIC_URL')}  (creator-code/storage.json)")
        print(f"key:         {keys()[2] or 'not set (CODEBAD_R2_ACCESS_KEY_ID / CODEBAD_R2_SECRET_ACCESS_KEY)'}")
        ignored = [k for k in (*FIELDS, "R2_ENDPOINT", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY") if os.environ.get(k)]
        if ignored:
            print(f"ignored:     {', '.join(ignored)} (set in this environment; Code Bad doesn't read them)")
        return 0
    if cmd == "ls":
        if enabled() and not has_keys():
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
    if cmd == "link":
        if enabled() and not has_keys():
            print("A signed link needs the bucket's key (CODEBAD_R2_ACCESS_KEY_ID, CODEBAD_R2_SECRET_ACCESS_KEY).")
            return 1
        try:
            print(link(argv[2], int(argv[3]) if len(argv) > 3 else 6 * 3600))
        except FileNotFoundError as e:
            print(e)
            return 1
        return 0
    if cmd == "links":
        if enabled() and not has_keys():
            print("Signed links need the bucket's key (CODEBAD_R2_ACCESS_KEY_ID, CODEBAD_R2_SECRET_ACCESS_KEY).")
            return 1
        found = links(argv[2], int(argv[3]) if len(argv) > 3 else 6 * 3600)
        if not found:
            print(f"{argv[2].strip('/')}/ has no videos or covers published")
            return 1
        print(json.dumps(found, indent=1, sort_keys=True))
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
