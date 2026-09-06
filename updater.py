import hashlib
import json
import logging
import os
import re
import struct
import sys
import tempfile
import threading
import time
import urllib.request

APP_VERSION = "1.0.2"
GITHUB_OWNER = "chamarawickramarathne-spec"
GITHUB_REPO = "facebook-reel-downloader"
RELEASES_API = (
    f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
)
VERSION_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")
_SHA_RE = re.compile(r"sha256:([\w\-\.]+)=([0-9a-fA-F]{64})")


def _log_dir():
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return os.path.join(base, "FacebookReelDownloader")


def _setup_logging():
    d = _log_dir()
    try:
        os.makedirs(d, exist_ok=True)
        logging.basicConfig(
            filename=os.path.join(d, "updater.log"),
            level=logging.INFO,
            format="%(asctime)s %(levelname)s %(message)s",
        )
    except OSError:
        logging.basicConfig(level=logging.INFO,
                            format="%(asctime)s %(levelname)s %(message)s")


def _arch_suffix():
    bits = struct.calcsize("P") * 8
    return "-Setup-x64.exe" if bits == 64 else "-Setup-x86.exe"


def parse_version(text):
    m = VERSION_RE.search(text)
    if not m:
        return None
    return tuple(int(x) for x in m.groups())


def _parse_hashes(release_body):
    hashes = {}
    if not isinstance(release_body, str):
        return hashes
    for m in _SHA_RE.finditer(release_body):
        hashes[m.group(1)] = m.group(2).lower()
    return hashes


class UpdateManager:
    def __init__(self, on_available, on_download_progress):
        self.on_available = on_available
        self.on_download_progress = on_download_progress
        self._latest = None
        self._cancel = False
        _setup_logging()
        logging.info("Updater initialized, app version %s", APP_VERSION)

    def start(self):
        threading.Thread(target=self._check, daemon=True).start()

    def _fetch(self, url, timeout, max_bytes=None):
        req = urllib.request.Request(url,
                                     headers={"User-Agent": "FacebookReelDownloader"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = getattr(resp, "status", 200)
            if status in (403, 429):
                raise RuntimeError(
                    f"GitHub API rate limited (HTTP {status})")
            if max_bytes is not None:
                cl = resp.headers.get("Content-Length")
                if cl and int(cl) > max_bytes:
                    raise RuntimeError("Response exceeds size limit")
            return resp.read(max_bytes) if max_bytes else resp.read()

    def _check(self):
        try:
            data = json.loads(
                self._fetch(RELEASES_API, 15, max_bytes=1 * 1024 * 1024).decode("utf-8"))
            tag = data.get("tag_name", "")
            latest = parse_version(tag)
            current = parse_version(APP_VERSION)
            if not latest or not current or latest <= current:
                logging.debug("No newer version; tag=%s", tag)
                return
            installer = self._find_installer(data.get("assets", []))
            if not installer:
                logging.warning("No matching installer asset in release %s", tag)
                return
            hashes = _parse_hashes(data.get("body"))
            target_name = installer["name"]
            expected_hash = hashes.get(target_name)
            if not expected_hash:
                logging.error(
                    "Release %s has no sha256 for %s; refusing auto-update",
                    tag, target_name)
                return
            installer["sha256"] = expected_hash
            self._latest = {"tag": tag, "version": latest, "asset": installer}
            logging.info("Update available: %s", tag)
            self.on_available(self._latest)
        except Exception as e:
            logging.error("Update check failed: %s", e)

    @staticmethod
    def _find_installer(assets):
        suffix = _arch_suffix()
        for a in assets:
            name = a.get("name", "")
            if name.endswith(suffix):
                return {
                    "name": name,
                    "url": a.get("browser_download_url") or a.get("url"),
                    "size": a.get("size", 0),
                }
        return None

    def download_and_install(self, on_done):
        if not self._latest:
            return
        target = os.path.join(tempfile.gettempdir(), self._latest["asset"]["name"])
        threading.Thread(
            target=self._download_asset, args=(target, on_done), daemon=True).start()

    def _download_asset(self, target, on_done):
        asset = self._latest["asset"]
        expected_hash = asset.get("sha256")
        hasher = hashlib.sha256()
        try:
            req = urllib.request.Request(
                asset["url"], headers={"User-Agent": "FacebookReelDownloader"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                status = getattr(resp, "status", 200)
                if status in (403, 429):
                    raise RuntimeError(f"GitHub rate limited (HTTP {status})")
                total = int(resp.headers.get("Content-Length") or asset["size"] or 0)
                MAX_INSTALLER = 500 * 1024 * 1024
                if total > MAX_INSTALLER:
                    raise RuntimeError("Installer exceeds size limit")
                done = 0
                with open(target, "wb") as f:
                    while True:
                        chunk = resp.read(65536)
                        if not chunk:
                            break
                        f.write(chunk)
                        hasher.update(chunk)
                        done += len(chunk)
                        if total > 0:
                            self.on_download_progress(done / total)
            actual_hash = hasher.hexdigest()
            if expected_hash and actual_hash != expected_hash:
                raise RuntimeError(
                    f"SHA-256 mismatch for {asset['name']}")
            logging.info("Verified %s (sha256 ok)", asset["name"])
            os.startfile(target)
            self._schedule_cleanup(target)
            sys.exit(0)
        except Exception as e:
            logging.error("Update install failed: %s", e)
            if os.path.exists(target):
                try:
                    os.remove(target)
                except OSError:
                    pass
            on_done()

    @staticmethod
    def _schedule_cleanup(target):
        def cleanup():
            deadline = time.time() + 30
            while time.time() < deadline:
                time.sleep(1.0)
                if not os.path.exists(target):
                    return
                try:
                    os.remove(target)
                    return
                except OSError:
                    continue

        t = threading.Thread(target=cleanup, daemon=True)
        t.start()
