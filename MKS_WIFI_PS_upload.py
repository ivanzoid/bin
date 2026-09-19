#! /usr/bin/env python3
#  -*- coding: utf-8 -*-
# author: Victor Shapovalov (@ArtificalSUN), 2022
# PrusaSlicer Thumbnail to TFT Thumbnail converter: @SH1NZ33
# Fix for PrusaSlicer 2.4 and newer: @WashingtonJunior
# encoding fix: @Goodsmileduck
# version: 0.5.0
#
# This script never modifies the sliced file: it reads the G-code to show you
# what is about to print and streams the exact bytes to the printer. Earlier
# versions rewrote the file in place, swapping the slicer's PNG thumbnails for
# MKS TFT ";simage:/;gimage:" previews -- that clobbered the saved G-code (and
# duplicated the print when two thumbnail sizes were configured), so it is gone.
# Consequence: the printer's own screen shows no preview for these uploads.
#
# Portable setup for use as an OrcaSlicer post-processing script:
#   OrcaSlicer is a GUI app, so it runs this via the system python3 (the shebang
#   resolves there, not to your shell's python3). That interpreter usually lacks
#   our deps, and on macOS ships a broken Tk 8.5 that draws a blank window.
#   To stay portable across machines we self-bootstrap: on first run we build a
#   private venv from a python with a modern Tk (>= 8.6), install the deps into
#   it, and re-exec ourselves under that venv. Later runs just re-exec (fast).
#   OrcaSlicer's config stays identical on every machine -- no interpreter path.
#
#   Prerequisite the script CAN'T automate: a python with Tk >= 8.6 must exist.
#     macOS:  brew install python-tk
#     Linux:  the distro python3 usually already qualifies (needs python3-venv)
#   Override the venv location with the MKS_WIFI_VENV env var.
#
#   macOS Local Network privacy: OrcaSlicer is never granted permission to reach
#   LAN devices for a spawned CLI helper (the prompt never fires, and the app
#   never lands in Privacy > Local Network), so the upload fails with "No route
#   to host". A plain fork/detach does NOT help -- macOS attributes the
#   permission to the "responsible process" up the spawn chain. So on macOS we
#   first re-launch through launchd (launchctl asuser), which disclaims that
#   responsibility; the disclaimed process is allowed to reach the LAN.

# --- self-bootstrapping venv (stdlib only above the re-exec) ---------------
import os, sys, subprocess

def _dbg(msg):
    # Dormant unless the flag file exists: `touch ~/.mks_wifi_debug` to enable,
    # then read ~/mks_wifi_debug.log. Used to trace the launchd disclaim path.
    try:
        if not os.path.exists(os.path.expanduser("~/.mks_wifi_debug")):
            return
        with open(os.path.expanduser("~/mks_wifi_debug.log"), "a") as f:
            f.write("[pid=%d ppid=%d uid=%d] %s\n" % (os.getpid(), os.getppid(), os.getuid(), msg))
    except Exception:
        pass

_VENV_DIR = os.environ.get("MKS_WIFI_VENV", os.path.expanduser("~/.venvs/mks-wifi-upload"))
_REQUIREMENTS = ["requests", "regex", "Pillow"]
_BOOTSTRAPPED_ENV = "MKS_WIFI_BOOTSTRAPPED"
_DISCLAIM_ARG = "--mks-disclaimed"
_DISCLAIMED_ENV = "MKS_WIFI_DISCLAIMED"

def _disclaim_from_parent():
    # macOS only: re-launch via launchd so we're no longer attributed to the app
    # that spawned us (OrcaSlicer) for Local Network privacy. See header note.
    _dbg("enter disclaim: platform=%s exe=%s argv=%r disclaimed_env=%r"
         % (sys.platform, sys.executable, sys.argv, os.environ.get(_DISCLAIMED_ENV)))
    if sys.platform != "darwin":
        return
    if os.environ.get(_DISCLAIMED_ENV):
        _dbg("already disclaimed (env flag) -> continuing in-process")
        return  # env flag survives the later venv re-exec, so we only do this once
    if _DISCLAIM_ARG in sys.argv:
        # We're the launchd-relaunched copy: drop the sentinel (so argv[1] is
        # still the gcode path) and record it in env for the venv re-exec.
        _dbg("sentinel present -> this is the disclaimed copy, consuming it")
        sys.argv.remove(_DISCLAIM_ARG)
        os.environ[_DISCLAIMED_ENV] = "1"
        return
    # launchctl asuser does not forward env, so carry the state in argv.
    cmd = ["launchctl", "asuser", str(os.getuid()),
           sys.executable, os.path.realpath(__file__), _DISCLAIM_ARG, *sys.argv[1:]]
    _dbg("re-launching via launchctl: %r" % (cmd,))
    try:
        os.execv("/bin/launchctl", cmd)
    except Exception as e:
        _dbg("execv launchctl FAILED: %r" % (e,))
        raise

def _venv_python(venv_dir):
    sub = "Scripts" if os.name == "nt" else "bin"
    exe = "python.exe" if os.name == "nt" else "python3"
    return os.path.join(venv_dir, sub, exe)

def _tk_at_least_86(python_exe):
    try:
        out = subprocess.check_output(
            [python_exe, "-c", "import tkinter as t; print(t.TkVersion)"],
            stderr=subprocess.DEVNULL, text=True).strip()
        return tuple(int(n) for n in out.split(".")) >= (8, 6)
    except Exception:
        return False

def _find_base_python():
    # Prefer an interpreter whose Tk is modern; fall back to whatever runs us.
    candidates = [
        "/opt/homebrew/bin/python3",   # Apple Silicon Homebrew
        "/usr/local/bin/python3",      # Intel Homebrew
        "/Library/Frameworks/Python.framework/Versions/Current/bin/python3",  # python.org
        sys.executable,
    ]
    fallback = None
    for c in candidates:
        if c and os.path.exists(c):
            if _tk_at_least_86(c):
                return c
            fallback = fallback or c
    return fallback or sys.executable

def _bootstrap():
    if os.environ.get(_BOOTSTRAPPED_ENV):
        return  # already re-exec'd into the venv
    venv_py = _venv_python(_VENV_DIR)
    if not os.path.exists(venv_py):
        subprocess.check_call([_find_base_python(), "-m", "venv", _VENV_DIR])
    try:  # install deps only if any are missing
        subprocess.check_call([venv_py, "-c", "import requests, regex, PIL"],
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        subprocess.check_call([venv_py, "-m", "pip", "install", *_REQUIREMENTS])
    os.environ[_BOOTSTRAPPED_ENV] = "1"
    # Re-exec unless we're already running inside the venv. Use sys.prefix, not
    # the executable path: a venv's python is a symlink to the base python, so
    # comparing realpath(executable) would wrongly think we're already in it.
    if os.path.realpath(sys.prefix) != os.path.realpath(_VENV_DIR):
        os.execve(venv_py, [venv_py, os.path.realpath(__file__), *sys.argv[1:]], os.environ)

_disclaim_from_parent()  # macOS: escape OrcaSlicer's Local Network restriction
_bootstrap()
# --- end self-bootstrapping venv -------------------------------------------

import time
import base64
import socket as pysock

import requests
import regex as re  # pip install regex
from io import BytesIO
from PIL import Image, ImageTk  # pip install Pillow

try:
    import tkinter as tk
    import tkinter.font as tkfont
    import tkinter.filedialog as fldg
except ImportError:  # py2 fallback kept from the original script
    import Tkinter as tk
    import tkFont as tkfont
    import tkFileDialog as fldg


# ===========================================================================
# G-code introspection: embedded preview + slicer metadata
# ===========================================================================

# Slicers write the previews at the top and (PrusaSlicer) the stats/config at
# the very bottom, so we sniff both ends instead of loading a 200 MB print.
_HEAD_BYTES = 4 * 1024 * 1024
_TAIL_BYTES = 512 * 1024

# "; thumbnail begin 300x300 12345" ... "; thumbnail end". OrcaSlicer also
# emits thumbnail_JPG / thumbnail_QOI blocks; we read whatever Pillow opens.
_THUMB_RE = re.compile(
    r'^;[ \t]*thumbnail(?:_(?P<fmt>[A-Za-z0-9]+))?[ \t]+begin[ \t]+'
    r'(?P<w>\d+)[xX](?P<h>\d+)[ \t]+(?P<size>\d+)[ \t]*$'
    r'(?P<data>.*?)'
    r'^;[ \t]*thumbnail(?:_[A-Za-z0-9]+)?[ \t]+end[ \t]*$',
    re.M | re.S)

_KV_RE = re.compile(r'^;[ \t]*(?P<key>[^;=:]{1,80}?)[ \t]*[=:][ \t]*(?P<val>.*?)[ \t]*$')
_GENERATED_RE = re.compile(r'^;[ \t]*generated by[ \t]+(?P<who>.+?)(?:[ \t]+on[ \t].*)?$', re.M | re.I)


def _read_ends(path):
    """Return (head_text, tail_text) so we can parse both metadata blocks."""
    size = os.path.getsize(path)
    with open(path, 'rb') as f:
        head = f.read(_HEAD_BYTES)
        if size > _HEAD_BYTES + _TAIL_BYTES:
            f.seek(-_TAIL_BYTES, os.SEEK_END)
            tail = f.read()
        else:
            tail = b''
    dec = lambda b: b.decode('utf-8', 'ignore')
    return dec(head), dec(tail)


def _parse_kv(text, into):
    """Harvest `; key = value` / `; key: value` comment pairs (first wins)."""
    in_thumb = False
    for line in text.splitlines():
        if not line.startswith(';'):
            continue
        low = line.lower()
        if 'thumbnail' in low and ' begin ' in low:
            in_thumb = True
            continue
        if in_thumb:
            if 'thumbnail' in low and ' end' in low:
                in_thumb = False
            continue
        if len(line) > 400:
            continue  # base64 leftovers / huge config blobs
        # OrcaSlicer packs several pairs on one line:
        #   "; model printing time: 30m; total estimated time: 35m"
        parts = line.split(';') if ('=' not in line) else [line.lstrip(';')]
        for part in parts:
            part = part.strip()
            if not part:
                continue
            m = _KV_RE.match(';' + part)
            if not m:
                continue
            key = m.group('key').strip().lower()
            val = m.group('val').strip()
            if key and val and key not in into:
                into[key] = val


def _pick(meta, *keys):
    for k in keys:
        v = meta.get(k)
        if v:
            return v
    return None


def _nums(val):
    """Numbers out of "1.75" / "0.4,0.4" / "215,0,0,0" style values."""
    if not val:
        return []
    out = []
    for tok in re.split(r'[,\s]+', val):
        try:
            out.append(float(tok))
        except ValueError:
            pass
    return out


def _first_num(val):
    n = _nums(val)
    return n[0] if n else None


def _sum_num(val):
    n = _nums(val)
    return sum(n) if n else None


def _uniq_words(val):
    """"PLA;PETG" / "PLA,PLA" -> "PLA / PETG" (multi-material headers)."""
    if not val:
        return None
    seen = []
    for tok in re.split(r'[;,]', val):
        tok = tok.strip()
        if tok and tok not in seen:
            seen.append(tok)
    return ' / '.join(seen) if seen else None


def _fmt_duration(text):
    """Normalize "2h 11m 34s" / "7894" / "0d 2h 11m" into "2h 11m"."""
    if not text:
        return None
    text = text.strip()
    secs = None
    m = re.findall(r'(\d+(?:\.\d+)?)\s*([dhms])', text, re.I)
    if m:
        mult = {'d': 86400, 'h': 3600, 'm': 60, 's': 1}
        secs = sum(float(v) * mult[u.lower()] for v, u in m)
    elif re.fullmatch(r'\d+(\.\d+)?', text):
        secs = float(text)
    if secs is None:
        return text
    return _fmt_secs(secs)


def _fmt_secs(secs):
    secs = int(round(secs))
    d, rem = divmod(secs, 86400)
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    if d:
        return "%dd %dh" % (d, h)
    if h:
        return "%dh %02dm" % (h, m)
    if m:
        return "%dm %02ds" % (m, s)
    return "%ds" % s


def _fmt_bytes(n):
    if n is None:
        return "-"
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return ("%d %s" % (n, unit)) if unit == "B" else ("%.1f %s" % (n, unit))
        n /= 1024.0


def extract_preview(text, box):
    """Largest embedded thumbnail as a PIL image, scaled to fit `box` px."""
    best = None
    for m in _THUMB_RE.finditer(text):
        try:
            w, h = int(m.group('w')), int(m.group('h'))
        except (TypeError, ValueError):
            continue
        if best is None or w * h > best[0]:
            best = (w * h, m.group('data'))
    if best is None:
        return None
    payload = ''.join(ln.lstrip(';').strip() for ln in best[1].splitlines())
    try:
        img = Image.open(BytesIO(base64.b64decode(payload)))
        img.load()
    except Exception as e:
        print("preview decode failed: %r" % (e,), file=sys.stderr)
        return None
    if img.mode not in ("RGB", "RGBA"):
        img = img.convert("RGBA")
    scale = min(box / img.width, box / img.height)
    if scale < 1 or scale > 1.001:
        img = img.resize((max(1, int(img.width * scale)),
                          max(1, int(img.height * scale))), Image.LANCZOS)
    return img


def read_gcode_info(path, preview_box):
    """Preview image + the display-ready facts we can dig out of the G-code."""
    info = {"preview": None, "rows": [], "time": None, "filament": None,
            "layers": None, "preheat": (None, None), "raw": {}}
    try:
        head, tail = _read_ends(path)
    except OSError as e:
        print("cannot read %s: %r" % (path, e), file=sys.stderr)
        return info

    info["preview"] = extract_preview(head, preview_box)

    meta = {}
    _parse_kv(head, meta)
    _parse_kv(tail, meta)
    info["raw"] = meta

    # --- headline numbers ---------------------------------------------------
    info["time"] = _fmt_duration(_pick(
        meta,
        'estimated printing time (normal mode)', 'estimated printing time',
        'total estimated time', 'model printing time', 'estimated_time',
        'print_time', 'time'))

    grams = _sum_num(_pick(meta, 'total filament used [g]', 'filament used [g]',
                           'filament_weight_total', 'filament used [grams]'))
    millis = _sum_num(_pick(meta, 'total filament length [mm]', 'filament used [mm]'))
    if grams:
        info["filament"] = "%.1f g" % grams
    elif millis:
        info["filament"] = "%.2f m" % (millis / 1000.0)

    layers = _first_num(_pick(meta, 'total layer number', 'total_layer_count',
                              'layer count', 'total layers'))
    if layers:
        info["layers"] = "%d" % int(layers)

    # --- detail rows (only the ones this slicer actually wrote) -------------
    rows = []

    lh = _first_num(meta.get('layer_height'))
    flh = _first_num(meta.get('first_layer_height'))
    if lh:
        rows.append(("Layer height", "%.2f mm" % lh + (" (first %.2f)" % flh if flh and abs(flh - lh) > 1e-6 else "")))

    nozzle = _uniq_words(meta.get('nozzle_diameter'))
    if nozzle:
        rows.append(("Nozzle", "%s mm" % nozzle))

    ftype = _uniq_words(_pick(meta, 'filament_type', 'filament type'))
    fname = _uniq_words(_pick(meta, 'filament_settings_id', 'filament_name'))
    if ftype or fname:
        if ftype and fname and ftype.lower() not in fname.lower():
            rows.append(("Material", "%s - %s" % (ftype, fname)))
        else:
            rows.append(("Material", (fname or ftype).strip('"')))

    hot = _first_num(_pick(meta, 'first_layer_temperature',
                           'nozzle_temperature_initial_layer',
                           'nozzle_temperature', 'temperature'))
    bed = _first_num(_pick(meta, 'first_layer_bed_temperature',
                           'bed_temperature_initial_layer',
                           'hot_plate_temp_initial_layer',
                           'bed_temperature', 'hot_plate_temp'))
    if hot or bed:
        rows.append(("Temps", "%s / %s" % ("%d C" % hot if hot else "-",
                                           "%d C" % bed if bed else "-")))
    # What the preheat will send: first-layer targets, so the print's M190/M109
    # return immediately instead of waiting out a cold bed.
    info["preheat"] = (int(hot) if hot else None, int(bed) if bed else None)

    speed = _first_num(_pick(meta, 'max_print_speed', 'outer_wall_speed', 'perimeter_speed'))
    if speed:
        rows.append(("Speed", "%d mm/s" % speed))

    fill = _pick(meta, 'fill_density', 'sparse_infill_density')
    if fill:
        rows.append(("Infill", fill if '%' in fill else fill + " %"))

    maxz = _first_num(_pick(meta, 'max_z_height', 'max_layer_z'))
    if maxz:
        rows.append(("Height", "%.1f mm" % maxz))

    printer = _pick(meta, 'printer_model', 'printer_settings_id', 'printer_notes')
    if printer:
        rows.append(("Printer", printer.strip('"')[:32]))

    cost = _first_num(_pick(meta, 'total filament cost', 'filament cost'))
    if cost:
        rows.append(("Cost", "%.2f" % cost))

    gen = _GENERATED_RE.search(head) or _GENERATED_RE.search(tail)
    if gen:
        rows.append(("Sliced by", gen.group('who').strip()[:32]))

    info["rows"] = rows
    return info


# ===========================================================================
# UI
# ===========================================================================

class Theme:
    bg      = "#14161b"
    panel   = "#1c1f27"
    panel2  = "#232734"
    border  = "#2e3342"
    text    = "#e9ebf1"
    muted   = "#8b93a7"
    dim     = "#5d6578"
    accent  = "#5b9cf8"
    ok      = "#3ecf8e"
    err     = "#ff6b6b"
    warn    = "#f5a524"


PREVIEW_BOX = 244
WIN_W = 780        # height is measured from the content, see Uploader._fit
PAD = 20


def _pick_font(root, *names):
    have = {f.lower() for f in tkfont.families(root)}
    for n in names:
        if n.lower() in have:
            return n
    return "TkDefaultFont"


def _round_rect(cv, x0, y0, x1, y1, r, **kw):
    """Rounded rectangle as a smoothed polygon (no themed-widget fights)."""
    r = min(r, (x1 - x0) / 2.0, (y1 - y0) / 2.0)
    pts = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1,
           x1 - r, y1, x0 + r, y1, x0, y1, x0, y1 - r, x0, y0 + r, x0, y0]
    return cv.create_polygon(pts, smooth=True, **kw)


class Uploader:
    """The whole window. Fixed size, hand-drawn widgets, no ttk theming."""

    def __init__(self, root, info, filename, ip_addr):
        self.root = root
        self.info = info
        self._preview_ref = None
        self._answer = tk.IntVar(value=-1)

        ui = _pick_font(root, "Inter", "SF Pro Text", "Segoe UI", "Ubuntu",
                        "DejaVu Sans", "Helvetica Neue")
        mono = _pick_font(root, "JetBrains Mono", "SF Mono", "Menlo",
                          "Cascadia Mono", "Consolas", "DejaVu Sans Mono")
        self.f_title = (ui, 15, "bold")
        self.f_sub   = (ui, 10)
        self.f_lbl   = (ui, 8, "bold")
        self.f_val   = (ui, 11, "bold")
        self.f_body  = (ui, 10)
        self.f_mono  = (mono, 9)
        self.f_big   = (ui, 17, "bold")

        root.title("MKS WiFi Upload")
        root.configure(background=Theme.bg)
        root.resizable(0, 0)

        self._pos = None
        self._build_header(filename, ip_addr)
        self._build_footer()
        self._build_body()
        self._fill_details()
        self._fit()

    # -- layout ------------------------------------------------------------

    def _fit(self):
        """Size the window to the content it ended up with.

        Row heights depend on whichever font the machine had, and rows get
        added at runtime, so the height is measured rather than declared --
        a fixed one either clipped the footer or left dead space. Position is
        chosen once, so a later regrow does not make the window jump.
        """
        self.root.update_idletasks()
        h = self.root.winfo_reqheight()
        if self._pos is None:
            sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
            self._pos = (max(0, (sw - WIN_W) // 2), max(0, (sh - h) // 3))
        self.root.minsize(WIN_W, h)      # min == max keeps it non-resizable
        self.root.maxsize(WIN_W, h)
        self.root.geometry("%dx%d+%d+%d" % (WIN_W, h, self._pos[0], self._pos[1]))

    DET_GAP = 12   # tiles -> details card
    DET_PAD = 11   # details card inner padding, top and bottom

    def _label(self, parent, text, font, fg, bg, **kw):
        return tk.Label(parent, text=text, font=font, fg=fg, bg=bg,
                        anchor=kw.pop('anchor', 'w'), justify='left', **kw)

    def _card(self, parent, **kw):
        return tk.Frame(parent, bg=Theme.panel, highlightthickness=1,
                        highlightbackground=Theme.border,
                        highlightcolor=Theme.border, **kw)

    def _build_header(self, filename, ip_addr):
        bar = tk.Frame(self.root, bg=Theme.bg)
        bar.pack(fill='x', padx=PAD, pady=(16, 12))

        left = tk.Frame(bar, bg=Theme.bg)
        left.pack(side='left', fill='x', expand=True)
        self._label(left, filename, self.f_title, Theme.text, Theme.bg).pack(anchor='w')
        self.lbl_sub = self._label(left, "Preparing upload...", self.f_sub,
                                   Theme.muted, Theme.bg)
        self.lbl_sub.pack(anchor='w', pady=(2, 0))

        right = tk.Frame(bar, bg=Theme.bg)
        right.pack(side='right')
        self.dot = tk.Canvas(right, width=10, height=10, bg=Theme.bg,
                             highlightthickness=0)
        self.dot.pack(side='left', padx=(0, 7), pady=(6, 0))
        self._dot_id = self.dot.create_oval(1, 1, 9, 9, fill=Theme.warn, outline="")
        self._label(right, ip_addr, self.f_mono, Theme.muted, Theme.bg).pack(
            side='left', pady=(5, 0))

    def _build_body(self):
        body = tk.Frame(self.root, bg=Theme.bg)
        body.pack(fill='both', expand=True, padx=PAD)

        # --- preview card ---
        card = self._card(body, width=PREVIEW_BOX + 16, height=PREVIEW_BOX + 16)
        card.pack(side='left', anchor='n')
        card.pack_propagate(False)
        img = self.info.get("preview")
        if img is not None:
            flat = Image.new("RGB", img.size, self._rgb(Theme.panel))
            flat.paste(img, (0, 0), img if img.mode == "RGBA" else None)
            self._preview_ref = ImageTk.PhotoImage(flat)
            tk.Label(card, image=self._preview_ref, bg=Theme.panel,
                     bd=0).pack(expand=True)
        else:
            ph = tk.Frame(card, bg=Theme.panel)
            ph.pack(expand=True)
            self._label(ph, "no preview", self.f_body, Theme.dim, Theme.panel,
                        anchor='center').pack()
            self._label(ph, "enable thumbnails in the slicer", (self.f_sub[0], 8),
                        Theme.dim, Theme.panel, anchor='center').pack(pady=(4, 0))

        # --- stats column ---
        right = tk.Frame(body, bg=Theme.bg)
        right.pack(side='left', fill='both', expand=True, padx=(16, 0))

        tiles = tk.Frame(right, bg=Theme.bg)
        tiles.pack(fill='x')
        self.tile_time = self._tile(tiles, "PRINT TIME", self.info["time"], 0)
        self.tile_fil  = self._tile(tiles, "FILAMENT", self.info["filament"], 1)
        self.tile_lay  = self._tile(tiles, "LAYERS", self.info["layers"], 2)
        for c in range(3):
            tiles.grid_columnconfigure(c, weight=1, uniform="tile")

        det = self._card(right)
        det.pack(fill='both', expand=True, pady=(self.DET_GAP, 0))
        self._det = tk.Frame(det, bg=Theme.panel)
        self._det.pack(fill='both', expand=True, padx=14, pady=self.DET_PAD)
        self._det_rows = 0
        self._det_empty = None
        self._det.grid_columnconfigure(1, weight=1)

    def _fill_details(self):
        for k, v in self.info["rows"]:
            self.add_detail(k, v)
        if not self._det_rows:
            self._det_empty = self._label(self._det, "no slicer metadata found",
                                          self.f_body, Theme.dim, Theme.panel)
            self._det_empty.grid(row=0, column=0, columnspan=2, sticky='w')

    def add_detail(self, key, value):
        """Append a row to the details card (also used for runtime facts)."""
        if self._det_empty is not None:
            self._det_empty.destroy()
            self._det_empty = None
        self._label(self._det, key, self.f_body, Theme.muted, Theme.panel).grid(
            row=self._det_rows, column=0, sticky='w', pady=1)
        self._label(self._det, value, self.f_body, Theme.text, Theme.panel).grid(
            row=self._det_rows, column=1, sticky='e', pady=1)
        self._det_rows += 1
        if self._pos is not None:   # added after the first fit -- grow to suit
            self._fit()

    def _tile(self, parent, title, value, col):
        card = self._card(parent)
        card.grid(row=0, column=col, sticky='nsew', padx=(0 if col == 0 else 8, 0))
        pad = tk.Frame(card, bg=Theme.panel)
        pad.pack(fill='both', expand=True, padx=12, pady=9)
        self._label(pad, title, self.f_lbl, Theme.dim, Theme.panel).pack(anchor='w')
        val = self._label(pad, value or "-", self.f_big,
                          Theme.text if value else Theme.dim, Theme.panel)
        val.pack(anchor='w', pady=(3, 0))
        return val

    def _build_footer(self):
        foot = tk.Frame(self.root, bg=Theme.bg)
        foot.pack(side='bottom', fill='x', padx=PAD, pady=(14, 16))

        top = tk.Frame(foot, bg=Theme.bg)
        top.pack(fill='x')
        self.lbl_status = self._label(top, "Starting...", self.f_body,
                                      Theme.text, Theme.bg)
        self.lbl_status.pack(side='left')
        self.lbl_pct = self._label(top, "0%", self.f_mono, Theme.muted, Theme.bg,
                                   anchor='e')
        self.lbl_pct.pack(side='right')

        self.bar_w = WIN_W - 2 * PAD
        self.bar = tk.Canvas(foot, width=self.bar_w, height=8, bg=Theme.bg,
                             highlightthickness=0)
        self.bar.pack(fill='x', pady=(8, 7))
        _round_rect(self.bar, 0, 0, self.bar_w, 8, 4, fill=Theme.panel2, outline="")
        self._bar_fill = None

        self.lbl_detail = self._label(foot, "", self.f_mono, Theme.dim, Theme.bg)
        self.lbl_detail.pack(side='left')

        self.btns = tk.Frame(foot, bg=Theme.bg)  # packed on demand

    # -- helpers -----------------------------------------------------------

    @staticmethod
    def _rgb(hexcolor):
        h = hexcolor.lstrip('#')
        return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

    def set_tile(self, which, value):
        tile = {"time": self.tile_time, "filament": self.tile_fil,
                "layers": self.tile_lay}[which]
        tile.configure(text=value or "-", fg=Theme.text if value else Theme.dim)

    def set_subtitle(self, text):
        self.lbl_sub.configure(text=text)

    def set_dot(self, color):
        self.dot.itemconfigure(self._dot_id, fill=color)

    def set_status(self, text, color=None, detail=None):
        self.lbl_status.configure(text=text, fg=color or Theme.text)
        if detail is not None:
            self.lbl_detail.configure(text=detail)
        self.root.update()

    def set_progress(self, frac, color=None):
        frac = max(0.0, min(1.0, frac))
        self.lbl_pct.configure(text="%d%%" % int(frac * 100))
        if self._bar_fill is not None:
            self.bar.delete(self._bar_fill)
            self._bar_fill = None
        w = frac * self.bar_w
        if w >= 1:
            self._bar_fill = _round_rect(self.bar, 0, 0, max(w, 8), 8, 4,
                                         fill=color or Theme.accent, outline="")

    def ask(self, question, yes="Start print", no="Not now"):
        """Inline yes/no row; returns True/False once the user picks."""
        self.set_status(question, Theme.warn)
        for child in self.btns.winfo_children():
            child.destroy()
        self._button(self.btns, no, Theme.muted, Theme.panel2,
                     lambda: self._answer.set(0)).pack(side='right')
        self._button(self.btns, yes, "#0d1117", Theme.accent,
                     lambda: self._answer.set(1)).pack(side='right', padx=(0, 8))
        self.btns.pack(side='right')
        self._fit()
        self._answer.set(-1)
        self.root.wait_variable(self._answer)
        self.btns.pack_forget()
        self._fit()
        return self._answer.get() == 1

    def _button(self, parent, text, fg, bg, cmd):
        b = tk.Label(parent, text=text, font=self.f_body, fg=fg, bg=bg,
                     padx=14, pady=5, cursor="hand2")
        b.bind("<Button-1>", lambda _e: cmd())
        b.bind("<Enter>", lambda _e: b.configure(bg=self._lighten(bg, 0.14)))
        b.bind("<Leave>", lambda _e: b.configure(bg=bg))
        return b

    @staticmethod
    def _lighten(hexcolor, amount):
        r, g, b = Uploader._rgb(hexcolor)
        mix = lambda c: int(c + (255 - c) * amount)
        return "#%02x%02x%02x" % (mix(r), mix(g), mix(b))

    def wait(self, seconds, label=None):
        """Sleep while still pumping the event loop, so the window repaints."""
        end = time.time() + seconds
        last = None
        while True:
            left = end - time.time()
            if left <= 0:
                break
            if label:
                n = int(left) + 1
                if n != last:
                    self.lbl_detail.configure(text=label % n)
                    last = n
            try:
                self.root.update()
            except tk.TclError:
                return
            time.sleep(0.03)


# ===========================================================================
# Upload plumbing
# ===========================================================================

def _short_err(e):
    """urllib3 wraps errors in three layers of repr; show the useful bit."""
    if isinstance(e, requests.exceptions.ConnectTimeout):
        return "no answer from %s (connect timed out)" % ip_addr
    if isinstance(e, requests.exceptions.ReadTimeout):
        return "%s stopped responding mid-upload" % ip_addr
    if isinstance(e, requests.exceptions.ConnectionError):
        return "cannot reach %s - is the printer on the network?" % ip_addr
    msg = str(e).strip().replace("\n", " ")
    return msg[:100] + "..." if len(msg) > 100 else msg


_LAYER_TOKEN = b";LAYER_CHANGE"


class GcodeUpload:
    """The request body: the file itself, byte for byte.

    Streams straight off disk so a 300 MB print never lands in RAM, reports
    progress as requests drains it, and -- since we are touching every byte
    anyway -- counts layers for the slicers that write no total.
    `__len__` matters: without it requests falls back to chunked encoding,
    where the old buffered body always sent a Content-Length. Keep it so the
    request on the wire stays the one the printer has been accepting.
    """

    def __init__(self, path, callback=None):
        self._f = open(path, "rb")
        self._len = os.fstat(self._f.fileno()).st_size
        self._callback = callback
        self._progress = 0
        self._carry = b""
        self.layers = 0

    def __len__(self):
        return self._len

    def read(self, n=-1):
        chunk = self._f.read(n)
        if chunk:
            self._progress += len(chunk)
            self._count_layers(chunk)
        if self._callback:
            self._callback(self._len, self._progress)
        return chunk

    def _count_layers(self, chunk):
        # Carry the last len(token)-1 bytes so a token split across two reads
        # is still seen. The carry is too short to hold a whole token, so
        # nothing gets counted twice.
        buf = self._carry + chunk
        self.layers += buf.count(_LAYER_TOKEN)
        self._carry = buf[-(len(_LAYER_TOKEN) - 1):]

    def close(self):
        self._f.close()


_last_paint = [0.0]
_upload_start = [0.0]


def upload_progress(size, progress):
    if size <= 0:
        return
    now = time.time()
    done = progress >= size
    if not done and now - _last_paint[0] < 0.05:
        return  # ~20 fps: repainting per 8 KB chunk throttles the transfer
    _last_paint[0] = now

    elapsed = max(1e-3, now - _upload_start[0])
    rate = progress / elapsed
    eta = (size - progress) / rate if rate > 0 else 0
    ui.set_progress(progress / float(size))
    ui.set_status("Uploading to printer", Theme.text,
                  "%s / %s   %s/s   %s left" % (
                      _fmt_bytes(progress), _fmt_bytes(size),
                      _fmt_bytes(rate), _fmt_secs(eta)))


def send_gcode(ip_addr, *commands):
    """Push M-codes at the WiFi module's raw G-code port. Raises on failure."""
    host = ip_addr.split(":")[0]  # the HTTP port never applies here
    socket = pysock.socket(pysock.AF_INET, pysock.SOCK_STREAM)
    socket.settimeout(10)
    try:
        socket.connect((host, 8080))
        for cmd in commands:
            socket.send((cmd + "\r\n").encode())
        socket.shutdown(pysock.SHUT_RDWR)
    finally:
        socket.close()
    _dbg("sent to %s:8080: %r" % (host, commands))


def printer_status(ip_addr):
    """Ask the WiFi module what the printer is doing (MKS M997).

    Returns 'PRINTING', 'PAUSE' or 'IDLE'; None when the module says nothing
    we recognise. None is deliberately NOT treated as idle -- firmware
    revisions differ, and guessing wrong means changing the temperature of
    somebody else's running print. The raw reply goes to the debug log
    (`touch ~/.mks_wifi_debug`) so an unrecognised one can be taught here.
    """
    host = ip_addr.split(":")[0]
    socket = pysock.socket(pysock.AF_INET, pysock.SOCK_STREAM)
    socket.settimeout(5)
    reply = ""
    try:
        socket.connect((host, 8080))
        socket.send(b"M997\r\n")
        for _ in range(3):  # the module may echo before it answers
            data = socket.recv(512)
            if not data:
                break
            reply += data.decode("ascii", "ignore")
            if any(k in reply.upper() for k in ("PRINTING", "PAUSE", "IDLE")):
                break
    except Exception as e:
        _dbg("M997 status query failed: %r" % (e,))
        return None
    finally:
        socket.close()
    _dbg("M997 reply: %r" % (reply,))
    up = reply.upper()
    for state in ("PRINTING", "PAUSE", "IDLE"):
        if state in up:
            return state
    return None


def preheat(ip_addr, hot, bed):
    """Start the heaters before the upload so they ramp while it transfers.

    M104/M140 set a target and return; M109/M190 would block the printer
    until it is reached, which would stall everything behind it.
    """
    cmds = []
    if bed:
        cmds.append("M140 S%d" % bed)   # bed first: it is the slow one
    if hot:
        cmds.append("M104 S%d" % hot)
    if not cmds:
        return False
    try:
        send_gcode(ip_addr, *cmds)
    except Exception as e:
        # Not fatal -- the print still works, it just starts cold.
        _dbg("preheat FAILED: %r" % (e,))
        print("Preheat on %s failed: %r" % (ip_addr, e), file=sys.stderr)
        return False
    return True


def cooldown(ip_addr):
    """Undo a preheat we are not going to use, so nothing sits hot unattended."""
    try:
        send_gcode(ip_addr, "M104 S0", "M140 S0")
    except Exception as e:
        _dbg("cooldown FAILED: %r" % (e,))
        print("Could not cool down %s: %r" % (ip_addr, e), file=sys.stderr)


def startJob(ip_addr, sd_name):
    ui.set_status("Starting print job...", Theme.text, "M23 / M24 -> %s:8080" % ip_addr)
    try:
        send_gcode(ip_addr, "M23 %s" % sd_name, "M24")
    except Exception as e:
        _dbg("startJob FAILED: %r" % (e,))
        ui.set_dot(Theme.err)
        ui.set_status("Could not start the job", Theme.err, _short_err(e))
        print("Starting job on %s failed: %r" % (ip_addr, e), file=sys.stderr)
        return False
    ui.set_dot(Theme.ok)
    ui.set_status("Printing", Theme.ok, "%s is now printing %s" % (ip_addr, sd_name))
    ui.set_progress(1.0, Theme.ok)
    return True


def startTransfer():
    ui.set_dot(Theme.warn)
    try:
        body = GcodeUpload(localfile, upload_progress)
    except OSError as e:
        ui.set_dot(Theme.err)
        ui.set_status("Cannot read the G-code", Theme.err, _short_err(e))
        print("Cannot read {0}: {1}".format(localfile, e), file=sys.stderr)
        ui.wait(6)
        root.destroy()
        sys.exit(1)

    total = len(body)
    if not info["layers"]:
        ui.set_tile("layers", "...")  # counted from the stream, filled in below
    ui.set_subtitle("%s  -  %s" % (_fmt_bytes(total), sd_name))

    # Start the heaters now so they ramp while the file transfers. Only on a
    # printer that positively reports itself idle: M104/M140 take effect
    # immediately, so firing them at a running print would wreck it.
    hot, bed = info["preheat"]
    state = printer_status(ip_addr) if PREHEAT and (hot or bed) else None
    preheated = False
    if state == "IDLE":
        ui.set_status("Preheating %s..." % ip_addr, Theme.text,
                      "M140 S%s / M104 S%s" % (bed or "-", hot or "-"))
        preheated = preheat(ip_addr, hot, bed)
        ui.add_detail("Preheat", "%s / %s C" % (hot or "-", bed or "-")
                                 if preheated else "failed, see stderr")
    elif state:
        _dbg("skipping preheat: printer is %s" % state)
        ui.add_detail("Preheat", "skipped, printer %s" % state.lower())
    elif PREHEAT and (hot or bed):
        ui.add_detail("Preheat", "skipped, no status from printer")

    ui.set_status("Connecting to %s..." % ip_addr)
    _upload_start[0] = time.time()
    _dbg("uploading to %s (uid=%d) file=%s" % (ip_addr, os.getuid(), sd_name))
    # timeout=(connect, read): fail fast if the printer is unreachable or stops
    # responding, so OrcaSlicer reports an error instead of hanging forever.
    try:
        r = requests.post(
            "http://{:s}/upload?X-Filename={:s}".format(ip_addr, sd_name),
            data=body,
            headers={'Content-Type': 'application/octet-stream',
                     'Connection': 'keep-alive'},
            timeout=(10, 60))
        _dbg("upload OK: status=%s" % (getattr(r, "status_code", "?"),))
    except (requests.exceptions.RequestException, OSError) as e:
        _dbg("upload FAILED: %r" % (e,))
        ui.set_dot(Theme.err)
        ui.set_progress(1.0, Theme.err)
        ui.set_status("Upload failed", Theme.err, _short_err(e))
        print("Upload to {0} failed: {1}".format(ip_addr, e), file=sys.stderr)
        body.close()
        if preheated:
            cooldown(ip_addr)
        ui.wait(6)
        root.destroy()
        sys.exit(1)

    body.close()
    took = time.time() - _upload_start[0]
    if not info["layers"]:  # PrusaSlicer writes no total; we counted the stream
        ui.set_tile("layers", "%d" % body.layers if body.layers else None)
    ui.set_progress(1.0, Theme.ok)
    ui.set_dot(Theme.ok)
    ui.set_status("Uploaded", Theme.ok,
                  "%s in %s (%s/s)" % (_fmt_bytes(total), _fmt_secs(took),
                                       _fmt_bytes(total / max(took, 1e-3))))

    if state in ("PRINTING", "PAUSE"):
        # Positive evidence the printer is busy: do not hijack it with M23/M24.
        ui.set_dot(Theme.warn)
        ui.set_status("Uploaded - printer is busy", Theme.warn,
                      "%s reports %s; start %s from the panel when it is free"
                      % (ip_addr, state.lower(), sd_name))
    elif mode == "always":
        ui.wait(2)
        startJob(ip_addr, sd_name)
    elif mode == "never":
        if preheated:
            cooldown(ip_addr)
    elif ui.ask("Start the print job now?"):
        startJob(ip_addr, sd_name)
    elif preheated:
        cooldown(ip_addr)
        ui.set_status("Uploaded, heaters off", Theme.ok,
                      "start %s from the printer whenever you like" % sd_name)

    ui.wait(4, "closing in %ds")
    root.destroy()


# ===========================================================================
# Entry point
# ===========================================================================

mode = "always"
ip_addr = "10.0.0.55"
PREHEAT = True  # set the G-code's first-layer temps while the file uploads

root = tk.Tk()
root.withdraw()  # keep the empty frame off-screen until the UI is populated

try:
    localfile = sys.argv[1]
except IndexError:
    localfile = fldg.askopenfilename(title="G-code to upload")
    if not localfile:
        sys.exit(0)

sd_name = os.path.split(localfile)[1]  # temporary filename, PrusaSlicer >= 2.4

env_slicer_pp_output_name = os.getenv('SLIC3R_PP_OUTPUT_NAME')  # final name, PS >= 2.4
if env_slicer_pp_output_name:
    sd_name = os.path.split(env_slicer_pp_output_name)[1]

# Read the previews/metadata BEFORE the TFT conversion strips the PNG blocks.
info = read_gcode_info(localfile, PREVIEW_BOX)

ui = Uploader(root, info, sd_name, ip_addr)
root.deiconify()
root.after(30, startTransfer)
root.mainloop()
