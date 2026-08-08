import json
import os
import re
import subprocess
import sys
import tempfile
import threading
import urllib.request

APP_VERSION = "1.0.1"
GITHUB_OWNER = "chamarawickramarathne-spec"
GITHUB_REPO = "facebook-reel-downloader"
RELEASES_API = (
    f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases/latest"
)
INSTALLER_SUFFIX = "-Setup.exe"
VERSION_RE = re.compile(r"(\d+)\.(\d+)\.(\d+)")


def parse_version(text):
    m = VERSION_RE.search(text)
    if not m:
        return None
    return tuple(int(x) for x in m.groups())


class UpdateManager:
    def __init__(self, on_available, on_download_progress):
        self.on_available = on_available
        self.on_download_progress = on_download_progress
        self._latest = None
        self._cancel = False

    def start(self):
        threading.Thread(target=self._check, daemon=True).start()

    def _check(self):
        try:
            req = urllib.request.Request(
                RELEASES_API, headers={"User-Agent": "FacebookReelDownloader"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            tag = data.get("tag_name", "")
            latest = parse_version(tag)
            current = parse_version(APP_VERSION)
            if not latest or not current or latest <= current:
                return
            installer = self._find_installer(data.get("assets", []))
            if not installer:
                return
            self._latest = {"tag": tag, "version": latest, "asset": installer}
            self.on_available(self._latest)
        except Exception:
            pass

    @staticmethod
    def _find_installer(assets):
        for a in assets:
            name = a.get("name", "")
            if name.endswith(INSTALLER_SUFFIX):
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
        try:
            asset = self._latest["asset"]
            req = urllib.request.Request(
                asset["url"], headers={"User-Agent": "FacebookReelDownloader"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                total = int(resp.headers.get("Content-Length") or asset["size"] or 0)
                done = 0
                with open(target, "wb") as f:
                    while True:
                        chunk = resp.read(65536)
                        if not chunk:
                            break
                        f.write(chunk)
                        done += len(chunk)
                        if total > 0:
                            self.on_download_progress(done / total)
            os.startfile(target)
            sys.exit(0)
        except Exception:
            if os.path.exists(target):
                try:
                    os.remove(target)
                except OSError:
                    pass
            on_done()
