import json
import os
import queue
import re
import shutil
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from pathlib import Path
from datetime import datetime

import requests

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "output"
DATA = ROOT / "data"
OUT.mkdir(exist_ok=True)
DATA.mkdir(exist_ok=True)

STYLES = [
    "Cinematic Realistic",
    "Animated Facts",
    "Viral 3D",
    "Professional Facts",
    "Real Exoplanet Cinematic Exploration",
]

def find_executable(name, candidates=()):
    found = shutil.which(name)
    if found:
        return found
    for item in candidates:
        if Path(item).is_file():
            return str(Path(item))
    return ""

def find_blender():
    candidates = []
    for version in ("5.0", "4.5", "4.4", "4.3", "4.2", "4.1", "4.0", "3.6"):
        candidates += [
            f"C:/Program Files/Blender Foundation/Blender {version}/blender.exe",
            f"C:/Program Files/Blender Foundation/Blender {version}/blender-launcher.exe",
        ]
    return find_executable("blender", candidates)

def find_ffmpeg():
    return find_executable("ffmpeg", [
        str(ROOT / "ffmpeg" / "bin" / "ffmpeg.exe"),
        str(ROOT / "bin" / "ffmpeg.exe"),
        str(ROOT / "ffmpeg.exe"),
        "C:/ffmpeg/bin/ffmpeg.exe",
    ])

def research_topic(topic):
    url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + requests.utils.quote(topic.replace(" ", "_"))
    try:
        response = requests.get(url, timeout=18, headers={"User-Agent": "YouTubeAutopilotAI/2.0"})
        response.raise_for_status()
        data = response.json()
        extract = data.get("extract", "")
        if not extract:
            raise RuntimeError("No encyclopedia summary was returned.")
        return {
            "title": data.get("title", topic),
            "summary": extract,
            "url": data.get("content_urls", {}).get("desktop", {}).get("page", url),
        }
    except Exception:
        return {
            "title": topic,
            "summary": f"{topic} is the subject of this short educational video. This automated draft needs a human fact-check and additional reliable sources before publication.",
            "url": "https://en.wikipedia.org/",
        }

def discover_exoplanet(preferred=""):
    base = "https://exoplanetarchive.ipac.caltech.edu/TAP/sync"
    query = "select top 150 pl_name,hostname,sy_dist,pl_rade,discoverymethod from pscomppars where default_flag=1"
    try:
        response = requests.get(base, params={"query": query, "format": "json"}, timeout=25)
        response.raise_for_status()
        rows = response.json()
        if preferred:
            matches = [r for r in rows if preferred.lower() in str(r.get("pl_name", "")).lower()]
            if matches:
                return matches[0]
        if rows:
            import random
            return random.choice(rows)
    except Exception:
        pass
    return {
        "pl_name": "TRAPPIST-1 e",
        "hostname": "TRAPPIST-1",
        "sy_dist": 12.43,
        "pl_rade": 0.92,
        "discoverymethod": "Transit",
    }

def make_script(topic, research, style, planet=None):
    if planet:
        name = planet.get("pl_name") or topic
        host = planet.get("hostname") or "its host star"
        distance = planet.get("sy_dist")
        radius = planet.get("pl_rade")
        method = planet.get("discoverymethod") or "astronomical observations"
        distance_text = f"{float(distance):.2f} light-years away" if distance not in (None, "") else "at a measured distance from Earth"
        radius_text = f"about {float(radius):.2f} times Earth's radius" if radius not in (None, "") else "with a measured planetary size"
        return (
            f"Travel with us beyond our Solar System. Today, we are exploring {name}, "
            f"a real exoplanet listed in NASA's Exoplanet Archive. It orbits the star {host}, "
            f"approximately {distance_text}. Its measured radius is {radius_text}. "
            f"Astronomers identified it using the {method.lower()} method. "
            f"We cannot see its surface in this level of detail, so the world you are about to see "
            f"is a scientific-inspired artistic visualization, not a photograph. "
            f"Scientists continue to study distant planets to learn about their atmospheres, "
            f"orbits, and the conditions that may exist there. {name} is one more reminder "
            f"of how many worlds may exist beyond our own."
        )
    summary = research["summary"]
    sentences = re.split(r"(?<=[.!?])\s+", summary)
    useful = " ".join(sentences[:6]).strip()
    return (
        f"Here is something fascinating about {research['title']}. "
        f"{useful} "
        f"Let's explore the key idea, understand why it matters, and look at the details "
        f"from a new perspective. This video is an automatically generated first draft. "
        f"Check the facts and sources before publishing."
    )

class CinematicApp:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Autopilot AI — Cinematic Studio")
        self.root.geometry("900x680")
        self.root.minsize(780, 590)
        self.root.configure(bg="#0b1020")
        self.events = queue.Queue()
        self.blender = tk.StringVar(value=find_blender())
        self.topic = tk.StringVar(value="TRAPPIST-1 e")
        self.style = tk.StringVar(value=STYLES[4])
        self.resolution = tk.StringVar(value="1280x720")
        self.voice = tk.StringVar(value="en-US-GuyNeural")
        self.status = tk.StringVar(value="Ready — select a style and enter a topic.")
        self._build()
        self.root.after(150, self._poll)

    def _build(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground="#151e33", background="#151e33", foreground="#f4f7ff")
        style.configure("TProgressbar", troughcolor="#1a2540", background="#59d5c7")
        header = tk.Frame(self.root, bg="#0b1020")
        header.pack(fill="x", padx=28, pady=(22, 8))
        tk.Label(header, text="CINEMATIC STUDIO", bg="#0b1020", fg="#61dfd0",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w")
        tk.Label(header, text="Turn a topic into a moving 3D video",
                 bg="#0b1020", fg="#f4f7ff", font=("Segoe UI", 23, "bold")).pack(anchor="w", pady=(5, 2))
        tk.Label(header, text="Free local rendering with Blender + FFmpeg + Edge neural narration",
                 bg="#0b1020", fg="#9ba9c3", font=("Segoe UI", 10)).pack(anchor="w")

        panel = tk.Frame(self.root, bg="#111a2d", highlightbackground="#263653", highlightthickness=1)
        panel.pack(fill="x", padx=28, pady=16)
        panel.columnconfigure(1, weight=1)
        self._label(panel, "VIDEO TOPIC", 0)
        tk.Entry(panel, textvariable=self.topic, bg="#17243b", fg="#f4f7ff", insertbackground="white",
                 relief="flat", font=("Segoe UI", 11)).grid(row=0, column=1, sticky="ew", padx=(0, 18), pady=12, ipady=8)
        self._label(panel, "VIDEO STYLE", 1)
        ttk.Combobox(panel, textvariable=self.style, values=STYLES, state="readonly",
                     font=("Segoe UI", 10)).grid(row=1, column=1, sticky="ew", padx=(0, 18), pady=8, ipady=5)
        self._label(panel, "RESOLUTION", 2)
        ttk.Combobox(panel, textvariable=self.resolution, values=["1280x720", "1920x1080"],
                     state="readonly", font=("Segoe UI", 10)).grid(row=2, column=1, sticky="w", padx=(0, 18), pady=8, ipady=5)
        self._label(panel, "NARRATION VOICE", 3)
        ttk.Combobox(panel, textvariable=self.voice,
                     values=["en-US-GuyNeural", "en-US-JennyNeural", "en-GB-RyanNeural", "en-GB-SoniaNeural"],
                     state="readonly", font=("Segoe UI", 10)).grid(row=3, column=1, sticky="w", padx=(0, 18), pady=8, ipady=5)
        self._label(panel, "BLENDER EXE", 4)
        tk.Entry(panel, textvariable=self.blender, bg="#17243b", fg="#f4f7ff", insertbackground="white",
                 relief="flat", font=("Segoe UI", 9)).grid(row=4, column=1, sticky="ew", padx=(0, 8), pady=10, ipady=7)
        tk.Button(panel, text="Browse", command=self._browse_blender, bg="#263653", fg="white",
                  relief="flat", padx=14).grid(row=4, column=2, padx=(0, 18), pady=8)

        actions = tk.Frame(self.root, bg="#0b1020")
        actions.pack(fill="x", padx=28, pady=(0, 12))
        tk.Button(actions, text="GENERATE 3D VIDEO", command=self.generate,
                  bg="#55d6c8", fg="#07131e", activebackground="#83f0e3",
                  font=("Segoe UI", 11, "bold"), relief="flat", padx=22, pady=13).pack(side="left")
        tk.Button(actions, text="Open Output Folder", command=self.open_output,
                  bg="#1c2942", fg="#f4f7ff", relief="flat", padx=16, pady=13).pack(side="left", padx=10)

        self.progress = ttk.Progressbar(self.root, mode="indeterminate")
        self.progress.pack(fill="x", padx=28, pady=(4, 6))
        tk.Label(self.root, textvariable=self.status, bg="#0b1020", fg="#9ba9c3",
                 font=("Segoe UI", 9)).pack(anchor="w", padx=28)
        logbox = tk.Frame(self.root, bg="#111a2d", highlightbackground="#263653", highlightthickness=1)
        logbox.pack(fill="both", expand=True, padx=28, pady=14)
        tk.Label(logbox, text="GENERATION LOG", bg="#111a2d", fg="#61dfd0",
                 font=("Segoe UI", 9, "bold")).pack(anchor="w", padx=14, pady=(12, 6))
        self.log = tk.Text(logbox, bg="#0d1526", fg="#d6e0f0", insertbackground="white",
                           relief="flat", wrap="word", font=("Consolas", 9), height=12)
        self.log.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.log.insert("end", "Ready. A rendered 3D video requires Blender and FFmpeg installed.\n")
        footer = "8 GB RAM mode: Eevee renderer, 720p default, low samples. Rendering can take time."
        tk.Label(self.root, text=footer, bg="#0b1020", fg="#71819d",
                 font=("Segoe UI", 8)).pack(anchor="w", padx=28, pady=(0, 12))

    def _label(self, parent, text, row):
        tk.Label(parent, text=text, bg="#111a2d", fg="#9ba9c3",
                 font=("Segoe UI", 8, "bold")).grid(row=row, column=0, sticky="w", padx=18, pady=10)

    def _browse_blender(self):
        path = filedialog.askopenfilename(title="Select blender.exe",
                                          filetypes=[("Blender", "blender.exe"), ("All files", "*.*")])
        if path:
            self.blender.set(path)

    def write_log(self, message):
        self.events.put(("log", message))

    def generate(self):
        topic = self.topic.get().strip()
        blender = self.blender.get().strip()
        ffmpeg = find_ffmpeg()
        if not topic:
            messagebox.showwarning("Topic needed", "Enter a video topic first.")
            return
        if not blender or not Path(blender).is_file():
            messagebox.showerror("Blender not found", "Install Blender, then browse to blender.exe.")
            return
        if not ffmpeg:
            messagebox.showerror("FFmpeg not found", "Install FFmpeg and add its bin folder to Windows PATH.")
            return
        self.progress.start(12)
        self.status.set("Generating — keep this window open.")
        threading.Thread(target=self._worker, args=(topic, self.style.get(), blender, ffmpeg,
                            self.resolution.get(), self.voice.get()), daemon=True).start()

    def _worker(self, topic, style, blender, ffmpeg, resolution, voice):
        try:
            self.write_log("Researching topic...")
            planet = None
            if style == STYLES[4]:
                planet = discover_exoplanet(topic if topic.lower() not in ("random exoplanet", "exoplanet", "space") else "")
                topic = planet.get("pl_name") or topic
                research = {"title": topic, "summary": "A confirmed exoplanet from NASA's Exoplanet Archive.",
                            "url": "https://exoplanetarchive.ipac.caltech.edu/"}
                self.write_log(f"Selected confirmed exoplanet: {topic} — host star {planet.get('hostname')}")
            else:
                research = research_topic(topic)
                self.write_log(f"Research source: {research['url']}")
            script = make_script(topic, research, style, planet)
            (OUT / "last_script.txt").write_text(script, encoding="utf-8")
            self.write_log("Preparing free neural narration...")
            import asyncio
            import edge_tts
            audio_path = OUT / "narration.mp3"
            asyncio.run(edge_tts.Communicate(script, voice).save(str(audio_path)))
            config = {
                "topic": topic, "style": style, "resolution": resolution,
                "output": str(OUT / "blender_scene.mp4"),
                "planet": planet,
            }
            config_path = OUT / "scene_config.json"
            config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")
            scene_script = ROOT / "blender_scene.py"
            if not scene_script.is_file():
                raise RuntimeError("blender_scene.py is missing. Re-download the complete project.")
            self.write_log("Launching Blender in background. This is real 3D rendering; it may take a while...")
            command = [blender, "--background", "--python", str(scene_script), "--", str(config_path)]
            result = subprocess.run(command, capture_output=True, text=True, cwd=str(ROOT))
            if result.returncode:
                raise RuntimeError("Blender failed:\n" + (result.stderr or result.stdout)[-5000:])
            scene_video = OUT / "blender_scene.mp4"
            final_video = OUT / ("YouTube_" + datetime.now().strftime("%Y%m%d_%H%M%S") + ".mp4")
            self.write_log("Combining rendered 3D scene with narration...")
            mux = [ffmpeg, "-y", "-i", str(scene_video), "-i", str(audio_path),
                   "-map", "0:v:0", "-map", "1:a:0", "-c:v", "copy", "-c:a", "aac",
                   "-b:a", "160k", "-shortest", "-movflags", "+faststart", str(final_video)]
            joined = subprocess.run(mux, capture_output=True, text=True)
            if joined.returncode:
                raise RuntimeError("FFmpeg audio mux failed:\n" + joined.stderr[-2500:])
            self.write_log("SUCCESS — " + str(final_video))
            self.events.put(("done", str(final_video)))
        except Exception as exc:
            self.events.put(("error", str(exc)))

    def _poll(self):
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "log":
                    self.log.insert("end", payload + "\n")
                    self.log.see("end")
                elif kind == "done":
                    self.progress.stop()
                    self.status.set("Video completed.")
                    self.log.insert("end", "Open the output folder to play your MP4.\n")
                    self.log.see("end")
                    messagebox.showinfo("Video ready", "Your video was rendered:\n" + payload)
                elif kind == "error":
                    self.progress.stop()
                    self.status.set("Generation failed — see log.")
                    self.log.insert("end", "\nERROR: " + payload + "\n")
                    self.log.see("end")
                    messagebox.showerror("Generation failed", payload[-2500:])
        except queue.Empty:
            pass
        self.root.after(150, self._poll)

    def open_output(self):
        os.startfile(str(OUT))

if __name__ == "__main__":
    root = tk.Tk()
    app = CinematicApp(root)
    root.mainloop()
