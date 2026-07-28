#! /usr/bin/env python3
#  -*- coding: utf-8 -*-
# author: Victor Shapovalov (@ArtificalSUN), 2022
# PrusaSlicer Thumbnail to TFT Thumbnail converter: @SH1NZ33
# Fix for PrusaSlicer 2.4 and newer: @WashingtonJunior
# encoding fix: @Goodsmileduck
# version: 0.4.0
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

import requests, io, time
import socket as pysock

import base64
import regex as re # pip install regex
from os.path import exists
from io import BytesIO
from PIL import Image # pip install Pillow

def generate_tft(img):
    width, height = img.size
    if(width == 100):
        res = ';simage:'
    else:
        res = ';;gimage:'
    pixels = img.convert('RGB')
    for y in range(width):
        for x in range(height):
            r, g, b = pixels.getpixel((x,y))
            res += rgb2tft(r, g, b)
        res += '\nM10086 ;'
    return res

def rgb2tft(r, g, b):
    #src: mks-wifi plugin : https://github.com/Jeredian/mks-wifi-plugin/blob/develop/MKSPreview.py
    r = r >> 3
    g = g >> 2
    b = b >> 3
    rgb = (r << 11) | (g << 5) | b
    return '{:02x}'.format(rgb & 0xFF) + '{:02x}'.format(((rgb >> 8) & 0xFF))

def convertPrusaThumb2TFTThumb(PrusaGCodeFileName): #Replace PrusaSlicer's Thumbnails to TFT's Thumbnails
    if not exists(PrusaGCodeFileName):
        return
    
    PrusaGCodeDatas = open(PrusaGCodeFileName).read() # ......................................................................... completly loading gcode file
    
    #regex for parsing datas with grouped part (matched)
    s_pattern = '(?<=(; thumbnail begin )([0-9]+)(x)([0-9]+) ([0-9]+)\n)(.*?)(?=; thumbnail end)'
    pattern = re.compile(s_pattern, re.M|re.I|re.S )
    
    TFTGCodeDatas = ''
    
    for match in pattern.finditer(PrusaGCodeDatas): #............................................................................ get all needed parts
        th_width  = match.group(2)
        th_height = match.group(4)
        th_size   = match.group(5)
        
        try:
            th_datas  = match.group(6) # ........................................................................................ get image datas (base64)
            th_datas = th_datas.replace('; ', '').replace('\n', '') # ........................................................... without carry returns, etc
            stream = BytesIO( base64.b64decode(th_datas) ) # .................................................................... decoding base64
            image = Image.open(stream).convert("RGB") # ......................................................................... for converting into PIL image
            stream.close()
            TFTGCodeDatas += generate_tft(image) # .............................................................................. converts PIL image into TFT GCode
            s_pattern = '; thumbnail begin .*; thumbnail end'
            TFTGCodeDatas = TFTGCodeDatas + '\n' +  re.sub( s_pattern, '', PrusaGCodeDatas, flags = re.M|re.I|re.S ) # .......... removes Prusa GCode and inserts TFTG Code
            fileOut = open(PrusaGCodeFileName, "w") 
            fileOut.write(TFTGCodeDatas)
            fileOut.close()
            
        except:
            pass
    return

try:
    import Tkinter as tk
    import Tkinter.simpledialog as smdg
    import Tkinter.filedialog as fldg
    import Tkinter.messagebox as msbx
except ImportError:
    import tkinter as tk
    import tkinter.simpledialog as smdg
    import tkinter.filedialog as fldg
    import tkinter.messagebox as msbx

try:
    import ttk
    py3 = False
except ImportError:
    import tkinter.ttk as ttk
    py3 = True

def vp_start_gui():
    '''Starting point when module is the main routine.'''
    global val, w, root
    root = tk.Tk()
    top = Main (root)
    gui_init(root, top)
    root.mainloop()

w = None
def create_Main(rt, *args, **kwargs):
    '''Starting point when module is imported by another module.
       Correct form of call: 'create_Main(root, *args, **kwargs)' .'''
    global w, w_win, root
    #rt = root
    root = rt
    w = tk.Toplevel (root)
    top = Main (w)
    gui_init(w, top, *args, **kwargs)
    return (w, top)

def gui_destroy_Main():
    global w
    w.destroy()
    w = None

class Main:
    def __init__(self, top=None):
        '''This class configures and populates the toplevel window.
           top is the toplevel containing window.'''
        _bgcolor = '#d9d9d9'  # X11 color: 'gray85'
        _fgcolor = '#000000'  # X11 color: 'black'
        _compcolor = '#d9d9d9' # X11 color: 'gray85'
        _ana1color = '#d9d9d9' # X11 color: 'gray85'
        _ana2color = '#ececec' # Closest X11 color: 'gray92'
        self.style = ttk.Style()
        if sys.platform == "win32":
            self.style.theme_use('winnative')
        self.style.configure('.',background=_bgcolor)
        self.style.configure('.',foreground=_fgcolor)
        self.style.configure('.',font="TkDefaultFont")
        self.style.map('.',background=
            [('selected', _compcolor), ('active',_ana2color)])

        top.geometry("400x60+630+507")
        top.minsize(400, 60)
        top.maxsize(400, 60)
        top.resizable(0, 0)
        top.title("MKS WIFI Uploader for Prusa Slicer")
        top.configure(background="#d9d9d9")

        # self.btn_Print = ttk.Button(top)
        # self.btn_Print.place(relx=0.2, rely=0.67, height=25, width=100)
        # self.btn_Print.configure(takefocus="")
        # self.btn_Print.configure(text='''Print!''')
        # self.btn_Print.configure(state='disabled')
        # slef.btn_Print

        # self.btm_NoThx = ttk.Button(top)
        # self.btm_NoThx.place(relx=0.55, rely=0.67, height=25, width=100)
        # self.btm_NoThx.configure(takefocus="")
        # self.btm_NoThx.configure(text='''No, thanks!''')
        # self.btm_NoThx.configure(state='disabled')

        self.lbl_UploadStatus = ttk.Label(top)
        self.lbl_UploadStatus.place(relx=0.023, rely=0.05, height=18, width=380)
        self.lbl_UploadStatus.configure(background="#d9d9d9")
        self.lbl_UploadStatus.configure(foreground="#000000")
        self.lbl_UploadStatus.configure(font="TkDefaultFont")
        self.lbl_UploadStatus.configure(relief="flat")
        self.lbl_UploadStatus.configure(anchor='w')
        self.lbl_UploadStatus.configure(justify='left')
        self.lbl_UploadStatus.configure(text='''Upload starting...''')

        self.prg_UploadProgress = ttk.Progressbar(top)
        self.prg_UploadProgress.place(relx=0.03, rely=0.45, relwidth=0.943
                , relheight=0.0, height=22)
        self.prg_UploadProgress.configure(length="420")

class CancelledError(Exception):
    def __init__(self, msg):
        self.msg = msg
        Exception.__init__(self, msg)

    def __str__(self):
        return self.msg

    __repr__ = __str__

class BufferReader(io.BytesIO):
    def __init__(self, buf=b'', callback=None, cb_args=(), cb_kwargs={}):
        self._callback = callback
        self._cb_args = cb_args
        self._cb_kwargs = cb_kwargs
        self._progress = 0
        self._len = len(buf)
        io.BytesIO.__init__(self, buf)

    def __len__(self):
        return self._len

    def read(self, n=-1):
        chunk = io.BytesIO.read(self, n)
        self._progress += int(len(chunk))
        self._cb_kwargs.update({
            'size'    : self._len,
            'progress': self._progress
        })
        if self._callback:
            try:
                self._callback(*self._cb_args, **self._cb_kwargs)
            except: # catches exception from the callback
                raise CancelledError('The upload was cancelled.')
        return chunk

def upload_progress(size, progress):
    if size > 0:
        prog_perc = progress*100/size
        top.prg_UploadProgress['value'] = int(prog_perc)
        top.lbl_UploadStatus['text'] = "Uploading {0} / {1} bytes ({2:.2f}%)".format(progress, size, prog_perc)
        root.update()


def gui_init(top, gui, *args, **kwargs):
    global w, top_level, root
    w = gui
    top_level = top
    root = top

def gui_destroy_window():
    # Function which closes the window.
    global top_level
    top_level.destroy()
    top_level = None

def startJob(ip_addr, sd_name):
    global top
    socket = pysock.socket(pysock.AF_INET, pysock.SOCK_STREAM)
    try:
        socket.connect((ip_addr, 8080))
    except Exception as e:
        print(e)
        raise(e)
    socket.send(("M23 %s" %sd_name + "\r\n").encode())
    socket.send(("M24" + "\r\n").encode())
    try:
        socket.shutdown(pysock.SHUT_RDWR)
        socket.close()
    except Exception as e:
        print(e)
        raise(e)
    top.lbl_UploadStatus['text'] = "Print job started!"
    top.prg_UploadProgress['value'] = int(100)
    root.update()

def startTransfer():
    global ip_addr, localfile, sd_name
    root.update() # force initial paint (macOS aqua won't draw the window before the blocking work below)
    convertPrusaThumb2TFTThumb(localfile) # converting Prusa Thumbs into TFT Thumbs
    with open(localfile, 'r', encoding="utf-8") as f:
        gcode = f.read()
    body_buffer = BufferReader(gcode.encode(), upload_progress)
    # timeout=(connect, read): fail fast if the printer is unreachable or stops
    # responding, so OrcaSlicer reports an error instead of hanging forever.
    _dbg("uploading to %s (uid=%d) file=%s" % (ip_addr, os.getuid(), sd_name))
    try:
        r = requests.post("http://{:s}/upload?X-Filename={:s}".format(ip_addr, sd_name), data=body_buffer, headers={'Content-Type': 'application/octet-stream', 'Connection' : 'keep-alive'}, timeout=(10, 60))
        _dbg("upload OK: status=%s" % (getattr(r, "status_code", "?"),))
    except requests.exceptions.RequestException as e:
        _dbg("upload FAILED: %r" % (e,))
        top.lbl_UploadStatus['text'] = "Upload failed: {0}".format(e)
        root.update()
        print("Upload to {0} failed: {1}".format(ip_addr, e), file=sys.stderr)
        time.sleep(3)
        root.destroy()
        sys.exit(1)
    top.lbl_UploadStatus['text'] = "Done!"
    root.update()
    if mode == "always":
        time.sleep(3)
        startJob(ip_addr, sd_name)
    elif mode=="never": pass
    else:
        printUploaded = msbx.askyesno("Start print job?", "Print uploaded file?")
        if printUploaded: startJob(ip_addr, sd_name)
    time.sleep(3)
    root.destroy()
    try: exit()
    except SystemExit as e: pass

root = tk.Tk()
top = Main(root)
gui_init(root, top)

mode = "always"
ip_addr = "10.0.0.55"

try:
    localfile = sys.argv[1]
except IndexError:
    localfile = fldg.askopenfilename()

sd_name = os.path.split(localfile)[1] #temporary filename, PrusaSlicer >= 2.4

env_slicer_pp_output_name = os.getenv('SLIC3R_PP_OUTPUT_NAME') #final output filename, PrusaSlicer >= 2.4

if env_slicer_pp_output_name:
    sd_name = os.path.split(env_slicer_pp_output_name)[1]

root.after(10, startTransfer)
root.mainloop()
