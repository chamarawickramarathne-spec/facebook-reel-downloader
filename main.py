import customtkinter as ctk
import tkinter as tk
import threading
import os
import re
import yt_dlp
from PIL import Image, ImageDraw
import urllib.request
import io
import updater

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class FacebookReelDownloader:

    BG          = "#0d1117"
    SURFACE     = "#161b22"
    SURFACE_HVR = "#1f2937"
    ACCENT      = "#58a6ff"
    ACCENT_HVR  = "#79c0ff"
    GREEN       = "#3fb950"
    RED         = "#f85149"
    TEXT        = "#e6edf3"
    TEXT_DIM    = "#8b949e"
    BORDER      = "#30363d"
    ENTRY_BG    = "#0d1117"

    FB_REEL_RE = re.compile(
        r"^https?://(?:www\.|m\.|web\.)?(?:"
        r"facebook\.com/(?:reel|reels|watch/reel)/\d+"
        r"|fb\.watch/\w+"
        r")(?:\?.*)?$"
    )

    SPINNER = ["\u280b", "\u2819", "\u2839", "\u2838",
               "\u283c", "\u2834", "\u2826", "\u2827"]

    def __init__(self, root):
        self.root = root
        self.root.title("Facebook Reel Downloader")
        self.root.geometry("520x580")
        self.root.minsize(520, 580)
        self.root.configure(fg_color=self.BG)

        self.downloading = False
        self.fetching = False
        self.fetched_formats = []
        self.fetched_url = None
        self._thumb_photo = None
        self._spin_idx = 0
        self._spin_on = False
        self._grad_img = None

        self._build_ui()
        self._bind_events()

        self.updater = updater.UpdateManager(
            on_available=self._show_update,
            on_download_progress=self._update_progress,
        )
        self.updater.start()

    def _make_gradient(self, w, h, c1, c2):
        img = Image.new("RGB", (w, h))
        draw = ImageDraw.Draw(img)
        r1, g1, b1 = tuple(int(c1.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
        r2, g2, b2 = tuple(int(c2.lstrip("#")[i:i+2], 16) for i in (0, 2, 4))
        for y in range(h):
            t = y / max(h - 1, 1)
            r = int(r1 + (r2 - r1) * t)
            g = int(g1 + (g2 - g1) * t)
            b = int(b1 + (b2 - b1) * t)
            draw.line([(0, y), (w, y)], fill=(r, g, b))
        return ctk.CTkImage(light_image=img, dark_image=img, size=(w, h))

    def _build_ui(self):
        # ── Header ──────────────────────────────────────────────
        self._grad_img = self._make_gradient(520, 20, "#1a1040", "#0d1117")
        header = ctk.CTkLabel(self.root, image=self._grad_img, text="",
                               width=520, height=20)
        header.pack(fill="x")

        ctk.CTkLabel(
            self.root, text="Facebook Reel Downloader",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color=self.ACCENT,
        ).pack(anchor="w", padx=28, pady=(0, 0))

        ctk.CTkLabel(
            self.root, text="Download videos in high quality",
            font=ctk.CTkFont(size=12),
            text_color=self.TEXT_DIM,
        ).pack(anchor="w", padx=28, pady=(2, 0))

        # ── Update bar (hidden until an update is found) ────────
        self.update_bar = ctk.CTkFrame(self.root, fg_color=self.SURFACE,
                                        corner_radius=12, border_width=1,
                                        border_color=self.GREEN)
        self.update_bar.pack(fill="x", padx=24, pady=(10, 0))

        self.update_var = ctk.StringVar(value="Checking for updates...")
        ctk.CTkLabel(
            self.update_bar, textvariable=self.update_var,
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.GREEN, anchor="w",
        ).pack(side="left", fill="x", expand=True, padx=(16, 8), pady=10)

        self.update_btn = ctk.CTkButton(
            self.update_bar, text="UPDATE", width=90, height=30,
            corner_radius=8, font=ctk.CTkFont(size=12, weight="bold"),
            fg_color=self.GREEN, hover_color="#46d960",
            text_color="#ffffff", command=self._start_update,
        )
        self.update_btn.pack(side="right", padx=(0, 12), pady=8)

        self.update_bar.pack_forget()

        # ── Main scrollable content ─────────────────────────────
        self.scroll = ctk.CTkScrollableFrame(
            self.root, fg_color="transparent",
            scrollbar_button_color=self.BORDER,
            scrollbar_button_hover_color=self.ACCENT,
        )
        self.scroll.pack(fill="both", expand=True, padx=24, pady=(14, 14))

        # ── URL Card ────────────────────────────────────────────
        url_card = ctk.CTkFrame(self.scroll, fg_color=self.SURFACE,
                                 corner_radius=16, border_width=1,
                                 border_color=self.BORDER)
        url_card.pack(fill="x", pady=(0, 12))

        url_inner = ctk.CTkFrame(url_card, fg_color="transparent")
        url_inner.pack(fill="x", padx=18, pady=(16, 14))

        ctk.CTkLabel(
            url_inner, text="\U0001f517  Paste your Reel URL below",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.TEXT_DIM,
        ).pack(anchor="w", pady=(0, 8))

        url_row = ctk.CTkFrame(url_inner, fg_color="transparent")
        url_row.pack(fill="x")

        self.url_var = ctk.StringVar()
        self.url_entry = ctk.CTkEntry(
            url_row, textvariable=self.url_var,
            placeholder_text="https://www.facebook.com/reel/...",
            font=ctk.CTkFont(size=13),
            height=40, corner_radius=10,
            fg_color=self.ENTRY_BG, border_color=self.BORDER,
            border_width=1, text_color=self.TEXT,
            placeholder_text_color=self.TEXT_DIM,
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        self.url_entry.focus_set()

        self.fetch_btn = ctk.CTkButton(
            url_row, text="FETCH", width=90, height=40,
            corner_radius=10, font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=self.ACCENT, hover_color=self.ACCENT_HVR,
            text_color="#ffffff", command=self._start_fetch,
        )
        self.fetch_btn.pack(side="right")

        val_row = ctk.CTkFrame(url_inner, fg_color="transparent")
        val_row.pack(fill="x", pady=(6, 0))

        self.val_dot = ctk.CTkLabel(
            val_row, text="\u25cf", font=ctk.CTkFont(size=10),
            text_color=self.TEXT_DIM, width=14,
        )
        self.val_dot.pack(side="left")

        self.validation_var = ctk.StringVar(value="Paste a Facebook Reel URL")
        ctk.CTkLabel(
            val_row, textvariable=self.validation_var,
            font=ctk.CTkFont(size=11), text_color=self.TEXT_DIM,
        ).pack(side="left")

        # ── Info Card (hidden until fetch) ──────────────────────
        self.info_card = ctk.CTkFrame(self.scroll, fg_color=self.SURFACE,
                                       corner_radius=16, border_width=1,
                                       border_color=self.BORDER)

        row_frame = ctk.CTkFrame(self.info_card, fg_color="transparent")
        row_frame.pack(fill="x", padx=18, pady=(16, 6), anchor="n")

        self.thumb_label = ctk.CTkLabel(
            row_frame, text="", width=180, height=100,
            fg_color=self.ENTRY_BG, corner_radius=12,
        )
        self.thumb_label.pack(side="left", anchor="n")

        right_col = ctk.CTkFrame(row_frame, fg_color="transparent")
        right_col.pack(side="left", fill="both", expand=True, padx=(14, 0), anchor="nw")

        ctk.CTkLabel(
            right_col, text="Quality:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color=self.TEXT_DIM,
        ).pack(anchor="w", pady=(0, 4))

        self.quality_var = ctk.StringVar(value="")
        self.quality_menu = ctk.CTkOptionMenu(
            right_col, variable=self.quality_var,
            values=["Best Quality (auto)"],
            font=ctk.CTkFont(size=12),
            dropdown_font=ctk.CTkFont(size=11),
            fg_color=self.ENTRY_BG, button_color=self.ACCENT,
            button_hover_color=self.ACCENT_HVR,
            dropdown_fg_color=self.SURFACE,
            dropdown_hover_color=self.SURFACE_HVR,
            dropdown_text_color=self.TEXT,
            text_color=self.TEXT, width=240, height=34, corner_radius=10,
        )
        self.quality_menu.pack(anchor="w", pady=(0, 8))

        self.download_btn = ctk.CTkButton(
            right_col, text="\u2b07  DOWNLOAD", width=240, height=36,
            corner_radius=10, font=ctk.CTkFont(size=13, weight="bold"),
            fg_color=self.GREEN, hover_color="#46d960",
            text_color="#ffffff", command=self._start_download,
        )
        self.download_btn.pack(anchor="w")

        # ── Progress Card (always visible) ──────────────────────
        prog_card = ctk.CTkFrame(self.scroll, fg_color=self.SURFACE,
                                  corner_radius=16, border_width=1,
                                  border_color=self.BORDER)
        prog_card.pack(fill="x", pady=(0, 12))

        prog_inner = ctk.CTkFrame(prog_card, fg_color="transparent")
        prog_inner.pack(fill="x", padx=18, pady=(14, 14))

        self.progress_var = ctk.DoubleVar(value=0)
        self.progress_bar = ctk.CTkProgressBar(
            prog_inner, variable=self.progress_var,
            width=400, height=12, corner_radius=6,
            fg_color=self.ENTRY_BG, progress_color=self.ACCENT,
        )
        self.progress_bar.pack(fill="x", pady=(0, 6))
        self.progress_bar.set(0)

        pct_row = ctk.CTkFrame(prog_inner, fg_color="transparent")
        pct_row.pack(fill="x")

        self.status_var = ctk.StringVar(value="Ready")
        self.status_label = ctk.CTkLabel(
            pct_row, textvariable=self.status_var,
            font=ctk.CTkFont(size=11), text_color=self.TEXT_DIM,
        )
        self.status_label.pack(side="left")

        self.pct_var = ctk.StringVar(value="0%")
        ctk.CTkLabel(
            pct_row, textvariable=self.pct_var,
            font=ctk.CTkFont(size=11), text_color=self.TEXT_DIM,
        ).pack(side="right")

        # ── Notification Area ─────────────────────────────────────
        self.notif_card = ctk.CTkFrame(self.scroll, fg_color=self.SURFACE,
                                       corner_radius=16, border_width=1,
                                       border_color=self.BORDER)

        self.notif_label = ctk.CTkLabel(
            self.notif_card, text="",
            font=ctk.CTkFont(size=12), text_color=self.TEXT_DIM,
            wraplength=420, anchor="w", justify="left",
        )
        self.notif_label.pack(fill="x", padx=18, pady=(14, 14))

    # ── Events ──────────────────────────────────────────────────
    def _bind_events(self):
        self.url_entry.bind("<FocusIn>", self._on_url_focus)
        self.url_entry.bind("<KeyRelease>", self._on_url_change)

    def _show_notif(self, text, color):
        self.notif_label.configure(text=text, text_color=color)
        self.notif_card.pack(fill="x", pady=(0, 12))

    # ── Updates ─────────────────────────────────────────────────
    def _show_update(self, latest):
        self.update_var.set(f"Update available: {latest['tag']}")
        self.update_btn.configure(state="normal")
        self.update_bar.pack(fill="x", padx=24, pady=(10, 0))

    def _start_update(self):
        self.update_btn.configure(state="disabled")
        self.update_var.set("Downloading update...")
        self.updater.download_and_install(on_done=self._update_failed)

    def _update_progress(self, frac):
        self.update_var.set(f"Downloading update... {frac * 100:.0f}%")

    def _update_failed(self):
        self.update_var.set("Update download failed — try again later")
        self.update_btn.configure(state="normal")

    def _on_url_focus(self, _event):
        if self.url_var.get().strip():
            return
        try:
            clip = self.root.clipboard_get().strip()
        except tk.TclError:
            return
        if self.FB_REEL_RE.match(clip):
            self.url_var.set(clip)
            self._validate_url(clip)

    def _on_url_change(self, _event):
        self._validate_url(self.url_var.get().strip())

    def _validate_url(self, url):
        if not url:
            self.validation_var.set("Paste a Facebook Reel URL")
            self.val_dot.configure(text_color=self.TEXT_DIM)
            self.fetch_btn.configure(state="disabled")
            return False
        if self.FB_REEL_RE.match(url):
            self.validation_var.set("Valid Facebook Reel URL")
            self.val_dot.configure(text_color=self.GREEN)
            self.fetch_btn.configure(state="normal")
            return True
        else:
            self.validation_var.set("Not a valid Facebook Reel URL")
            self.val_dot.configure(text_color=self.RED)
            self.fetch_btn.configure(state="disabled")
            return False

    # ── Spinner ─────────────────────────────────────────────────
    def _spin_start(self):
        self._spin_on = True
        self._spin_tick()

    def _spin_stop(self):
        self._spin_on = False
        txt = self.status_var.get()
        for f in self.SPINNER:
            if txt.startswith(f + " "):
                self.status_var.set(txt[2:])
                break

    def _spin_tick(self):
        if not self._spin_on:
            return
        ch = self.SPINNER[self._spin_idx % len(self.SPINNER)]
        txt = self.status_var.get()
        for f in self.SPINNER:
            if txt.startswith(f + " "):
                txt = txt[2:]
                break
        self.status_var.set(f"{ch} {txt}")
        self._spin_idx += 1
        self.root.after(80, self._spin_tick)

    # ── Fetch ───────────────────────────────────────────────────
    def _start_fetch(self):
        url = self.url_var.get().strip()
        if not self._validate_url(url):
            return
        if self.fetching or self.downloading:
            return

        self.fetching = True
        self.fetch_btn.configure(state="disabled")
        self.info_card.pack_forget()
        self.progress_var.set(0)
        self.pct_var.set("0%")
        self.status_label.configure(text_color=self.TEXT_DIM)
        self.status_var.set("Fetching video info...")
        self._spin_start()
        self.fetched_url = url

        threading.Thread(target=self._fetch_info, args=(url,), daemon=True).start()

    def _fetch_info(self, url):
        try:
            opts = {"quiet": True, "no_warnings": True, "skip_download": True}
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)

            formats = info.get("formats", [])
            video_fmts = []
            seen = set()
            for f in formats:
                h = f.get("height")
                if not h:
                    continue
                if f.get("acodec", "none") in ("none",):
                    continue
                if h in seen:
                    continue
                seen.add(h)
                vc = f.get("vcodec", "unknown")
                video_fmts.append({
                    "label": f"{h}p \u2014 {vc.split('.')[0]}",
                    "format_id": f["format_id"],
                    "height": h, "ext": f.get("ext", "mp4"),
                })

            video_fmts.sort(key=lambda x: x["height"], reverse=True)
            best = {"label": "Best Quality (auto)",
                     "format_id": "best[ext=mp4]/best",
                     "height": 99999, "ext": "mp4"}
            quality_list = [best] + video_fmts

            thumb_photo = None
            thumb_url = info.get("thumbnail")
            if thumb_url:
                try:
                    req = urllib.request.Request(thumb_url,
                                                 headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        data = resp.read()
                    img = Image.open(io.BytesIO(data))
                    img = img.resize((180, 100), Image.LANCZOS)
                    thumb_photo = ctk.CTkImage(light_image=img, dark_image=img,
                                                size=(180, 100))
                except Exception:
                    thumb_photo = None

            self.root.after(0, self._show_card, thumb_photo, quality_list)

        except Exception as e:
            self.root.after(0, self._fetch_err, str(e))
        finally:
            self.fetching = False
            self.root.after(0, self._spin_stop)
            self.root.after(0, self.fetch_btn.configure, (), {"state": "normal"})

    def _show_card(self, thumb, qlist):
        self._thumb_photo = thumb
        if thumb:
            self.thumb_label.configure(image=thumb, text="")
        else:
            self.thumb_label.configure(image="", text="No thumbnail",
                                        text_color=self.TEXT_DIM)

        labels = [q["label"] for q in qlist]
        self.quality_menu.configure(values=labels)
        if labels:
            self.quality_var.set(labels[0])

        self.fetched_formats = qlist
        self.download_btn.configure(state="normal")
        self.info_card.pack(fill="x", pady=(0, 12))
        self.status_label.configure(text_color=self.GREEN)
        self.status_var.set("Video info loaded — choose quality and download")
        self._show_notif("Video info loaded successfully", self.GREEN)

    def _fetch_err(self, msg):
        self.status_label.configure(text_color=self.RED)
        self.status_var.set(f"Failed to fetch: {msg[:80]}")
        self._show_notif(f"Error: {msg[:120]}", self.RED)

    # ── Download ────────────────────────────────────────────────
    def _start_download(self):
        if self.downloading or self.fetching:
            return
        if not self.fetched_url or not self.fetched_formats:
            self.status_label.configure(text_color=self.RED)
            self.status_var.set("Fetch a video first")
            self._show_notif("Fetch a video first", self.RED)
            return

        sel = self.quality_var.get()
        if not sel:
            self.status_label.configure(text_color=self.RED)
            self.status_var.set("Select a quality")
            self._show_notif("Select a quality", self.RED)
            return

        fmt = None
        for q in self.fetched_formats:
            if q["label"] == sel:
                fmt = q
                break
        if not fmt:
            fmt = self.fetched_formats[0]

        save_dir = os.path.join(os.path.expanduser("~"), "Downloads")
        os.makedirs(save_dir, exist_ok=True)

        self.downloading = True
        self.download_btn.configure(state="disabled")
        self.fetch_btn.configure(state="disabled")
        self.progress_var.set(0)
        self.pct_var.set("0%")
        self.status_label.configure(text_color=self.TEXT_DIM)
        self.status_var.set("Preparing download...")
        self._spin_start()

        threading.Thread(target=self._download, args=(self.fetched_url, fmt, save_dir),
                         daemon=True).start()

    def _download(self, url, fmt, save_dir):
        try:
            info_opts = {"quiet": True, "no_warnings": True, "skip_download": True}
            with yt_dlp.YoutubeDL(info_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            raw_title = info.get("title") or info.get("fulltitle") or "facebook_reel"
            ext = info.get("ext", "mp4")
            safe = self._sanitize(raw_title)

            def hook(d):
                if d["status"] == "downloading":
                    total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
                    dl = d.get("downloaded_bytes", 0)
                    if total > 0:
                        pct = dl / total
                        self.root.after(0, self.progress_var.set, pct)
                        self.root.after(0, self.pct_var.set, f"{pct*100:.0f}%")
                        spd = d.get("speed")
                        if spd:
                            self.root.after(0, self.status_var.set,
                                            f"Downloading: {safe} ({spd/1024/1024:.1f} MB/s)")
                elif d["status"] == "finished":
                    self.root.after(0, self.progress_var.set, 1.0)
                    self.root.after(0, self.pct_var.set, "100%")
                    self.root.after(0, self.status_var.set, "Finalizing...")

            out_path = os.path.join(save_dir, f"{safe}.%(ext)s")
            dl_opts = {
                "outtmpl": out_path,
                "format": fmt.get("format_id", "best[ext=mp4]/best"),
                "progress_hooks": [hook],
                "quiet": True, "no_warnings": True,
            }

            with yt_dlp.YoutubeDL(dl_opts) as ydl:
                ydl.download([url])

            final = os.path.join(save_dir, f"{safe}.{ext}")
            self.root.after(0, self._spin_stop)
            self.root.after(0, self.status_label.configure,
                            (), {"text_color": self.GREEN})
            self.root.after(0, self.status_var.set, f"Saved: {final}")
            self.root.after(0, self._show_notif, f"Saved: {final}", self.GREEN)

        except Exception as e:
            self.root.after(0, self._spin_stop)
            self.root.after(0, self.status_label.configure,
                            (), {"text_color": self.RED})
            self.root.after(0, self.status_var.set, f"Download failed: {str(e)[:80]}")
            self.root.after(0, self._show_notif, f"Download failed: {str(e)[:120]}", self.RED)
        finally:
            self.downloading = False
            self.root.after(0, self.download_btn.configure, (), {"state": "normal"})
            self.root.after(0, self.fetch_btn.configure, (), {"state": "normal"})
            self.root.after(0, self.progress_var.set, 0)
            self.root.after(0, self.pct_var.set, "0%")

    @staticmethod
    def _fmt_dur(sec):
        m, s = divmod(int(sec), 60)
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"

    @staticmethod
    def _sanitize(name):
        name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '_', name)
        name = name.strip(". ")
        return name[:200] if name else "facebook_reel"


if __name__ == "__main__":
    root = ctk.CTk()
    app = FacebookReelDownloader(root)
    root.mainloop()
