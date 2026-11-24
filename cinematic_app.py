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
    BG = "#F7F9FC"
    WHITE = "#FFFFFF"
    INK = "#182230"
    MUTED = "#7B8798"
    BLUE = "#3478F6"
    PALE_BLUE = "#EDF4FF"
    LINE = "#E7ECF3"
    GREEN = "#15966B"

    def __init__(self, root):
        self.root = root
        self.root.title("Agent Artifacts")
        self.root.geometry("1380x880")
        self.root.minsize(1080, 720)
        self.root.configure(bg=self.BG)
        self.events = queue.Queue()
        self.blender = tk.StringVar(value=find_blender())
        self.topic = tk.StringVar(value="TRAPPIST-1 e")
        self.style = tk.StringVar(value=STYLES[4])
        self.resolution = tk.StringVar(value="1280x720")
        self.voice = tk.StringVar(value="en-US-GuyNeural")
        self.status = tk.StringVar(value="Ready to create")
        self._build()
        self.root.after(150, self._poll)

    def _build(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TCombobox", fieldbackground=self.WHITE, background=self.WHITE,
                        foreground=self.INK, bordercolor=self.LINE, padding=8)
        style.map("TCombobox", fieldbackground=[("readonly", self.WHITE)])
        style.configure("TProgressbar", troughcolor="#EAF0F7", background=self.BLUE,
                        bordercolor="#EAF0F7", lightcolor=self.BLUE, darkcolor=self.BLUE)
        style.configure("Treeview", background=self.WHITE, fieldbackground=self.WHITE,
                        foreground=self.INK, rowheight=34, borderwidth=0)
        style.configure("Treeview.Heading", background="#F3F6FA", foreground=self.MUTED,
                        font=("Segoe UI", 9, "bold"), relief="flat")

        shell = tk.Frame(self.root, bg=self.BG)
        shell.pack(fill="both", expand=True)

        self.sidebar = tk.Frame(shell, bg=self.WHITE, width=224,
                                highlightbackground=self.LINE, highlightthickness=1)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        brand = tk.Frame(self.sidebar, bg=self.WHITE)
        brand.pack(fill="x", padx=22, pady=(26, 30))
        tk.Label(brand, text="✦", bg=self.WHITE, fg=self.BLUE,
                 font=("Segoe UI Symbol", 25, "bold")).pack(side="left")
        brand_text = tk.Frame(brand, bg=self.WHITE)
        brand_text.pack(side="left", padx=9)
        tk.Label(brand_text, text="AGENT", bg=self.WHITE, fg=self.INK,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w")
        tk.Label(brand_text, text="ARTIFACTS", bg=self.WHITE, fg=self.BLUE,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w")

        tk.Label(self.sidebar, text="WORKSPACE", bg=self.WHITE, fg="#A0AABA",
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=22, pady=(0, 9))
        self.nav_buttons = {}
        for key, label, glyph in [
            ("Create", "Create video", "✧"),
            ("Projects", "Projects", "▣"),
            ("Templates", "Templates", "▤"),
        ]:
            self._nav_button(key, label, glyph)

        tk.Label(self.sidebar, text="PREFERENCES", bg=self.WHITE, fg="#A0AABA",
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=22, pady=(26, 9))
        self._nav_button("Settings", "Settings", "⚙")
        self._nav_button("About", "About", "ⓘ")

        side_bottom = tk.Frame(self.sidebar, bg="#F7F9FC",
                               highlightbackground=self.LINE, highlightthickness=1)
        side_bottom.pack(side="bottom", fill="x", padx=14, pady=16)
        tk.Label(side_bottom, text="LOCAL CREATOR STUDIO", bg="#F7F9FC",
                 fg=self.MUTED, font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=12, pady=(12, 3))
        tk.Label(side_bottom, text="Your projects stay on this PC.",
                 bg="#F7F9FC", fg=self.INK, font=("Segoe UI", 8)).pack(anchor="w", padx=12, pady=(0, 12))

        main = tk.Frame(shell, bg=self.BG)
        main.pack(side="left", fill="both", expand=True)
        top = tk.Frame(main, bg=self.WHITE, height=74,
                       highlightbackground=self.LINE, highlightthickness=1)
        top.pack(fill="x")
        top.pack_propagate(False)
        self.page_title = tk.Label(top, text="Create video", bg=self.WHITE, fg=self.INK,
                                   font=("Segoe UI", 16, "bold"))
        self.page_title.pack(side="left", padx=28)
        right_top = tk.Frame(top, bg=self.WHITE)
        right_top.pack(side="right", padx=28)
        tk.Label(right_top, text="●", bg=self.WHITE, fg=self.GREEN,
                 font=("Segoe UI", 10)).pack(side="left")
        tk.Label(right_top, textvariable=self.status, bg=self.WHITE, fg=self.MUTED,
                 font=("Segoe UI", 9)).pack(side="left", padx=(6, 0))

        self.content = tk.Frame(main, bg=self.BG)
        self.content.pack(fill="both", expand=True, padx=26, pady=22)
        self.pages = {}
        self._build_create_page()
        self._build_projects_page()
        self._build_templates_page()
        self._build_settings_page()
        self._build_about_page()
        self._show_page("Create")

    def _nav_button(self, key, label, glyph):
        b = tk.Button(self.sidebar, text=f"  {glyph}    {label}", anchor="w",
                      command=lambda k=key: self._show_page(k),
                      bg=self.WHITE, fg=self.MUTED, activebackground=self.PALE_BLUE,
                      activeforeground=self.BLUE, relief="flat", bd=0,
                      font=("Segoe UI", 10), padx=15, pady=12, cursor="hand2")
        b.pack(fill="x", padx=12, pady=2)
        self.nav_buttons[key] = b

    def _show_page(self, key):
        for page in self.pages.values():
            page.pack_forget()
        self.pages[key].pack(fill="both", expand=True)
        self.page_title.config(text={"Create": "Create video", "Projects": "Your projects",
                                     "Templates": "Creative templates", "Settings": "Settings",
                                     "About": "About Agent Artifacts"}[key])
        for name, button in self.nav_buttons.items():
            selected = name == key
            button.configure(bg=self.PALE_BLUE if selected else self.WHITE,
                             fg=self.BLUE if selected else self.MUTED,
                             font=("Segoe UI", 10, "bold" if selected else "normal"))

    def _card(self, parent, title=None, subtitle=None):
        frame = tk.Frame(parent, bg=self.WHITE, highlightbackground=self.LINE,
                         highlightthickness=1, bd=0)
        if title:
            head = tk.Frame(frame, bg=self.WHITE)
            head.pack(fill="x", padx=18, pady=(16, 4))
            tk.Label(head, text=title, bg=self.WHITE, fg=self.INK,
                     font=("Segoe UI", 10, "bold")).pack(anchor="w")
            if subtitle:
                tk.Label(frame, text=subtitle, bg=self.WHITE, fg=self.MUTED,
                         font=("Segoe UI", 8)).pack(anchor="w", padx=18, pady=(0, 10))
        return frame

    def _field_label(self, parent, text):
        tk.Label(parent, text=text.upper(), bg=self.WHITE, fg=self.MUTED,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=18, pady=(10, 5))

    def _build_create_page(self):
        page = tk.Frame(self.content, bg=self.BG)
        self.pages["Create"] = page
        intro = tk.Frame(page, bg=self.BG)
        intro.pack(fill="x", pady=(0, 16))
        tk.Label(intro, text="Bring your next idea to life.", bg=self.BG, fg=self.INK,
                 font=("Segoe UI", 21, "bold")).pack(anchor="w")
        tk.Label(intro, text="Choose a visual direction, set your video details, and create a cinematic scene.",
                 bg=self.BG, fg=self.MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 0))

        style_card = self._card(page, "CHOOSE YOUR VIDEO STYLE",
                                "Pick the visual treatment for your generated video.")
        style_card.pack(fill="x", pady=(0, 14))
        choices = tk.Frame(style_card, bg=self.WHITE)
        choices.pack(fill="x", padx=14, pady=(2, 14))
        self.style_buttons = {}
        for i, name in enumerate(STYLES):
            short = ["Cinematic\nRealistic", "Animated\nFacts", "Viral\n3D", "Professional\nFacts",
                     "Exoplanet\nExploration"][i]
            b = tk.Button(choices, text="✧\n" + short, command=lambda n=name: self._select_style(n),
                          bg=self.PALE_BLUE if self.style.get() == name else "#F8FAFD",
                          fg=self.BLUE if self.style.get() == name else self.INK,
                          activebackground=self.PALE_BLUE, activeforeground=self.BLUE,
                          relief="flat", bd=0, highlightthickness=1,
                          highlightbackground=self.BLUE if self.style.get() == name else self.LINE,
                          font=("Segoe UI", 9, "bold"), padx=8, pady=12, cursor="hand2")
            b.pack(side="left", fill="x", expand=True, padx=4)
            self.style_buttons[name] = b

        work = tk.Frame(page, bg=self.BG)
        work.pack(fill="both", expand=True)
        left = tk.Frame(work, bg=self.BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 14))
        right = tk.Frame(work, bg=self.BG, width=390)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        brief = self._card(left, "VIDEO DETAILS", "Tell Agent Artifacts what you want to create.")
        brief.pack(fill="x", pady=(0, 12))
        self._field_label(brief, "Video topic")
        tk.Entry(brief, textvariable=self.topic, bg="#F7F9FC", fg=self.INK,
                 insertbackground=self.INK, relief="flat", font=("Segoe UI", 11),
                 highlightthickness=1, highlightbackground=self.LINE,
                 highlightcolor=self.BLUE).pack(fill="x", padx=18, ipady=10)
        row = tk.Frame(brief, bg=self.WHITE)
        row.pack(fill="x", padx=18, pady=(8, 16))
        col1 = tk.Frame(row, bg=self.WHITE)
        col1.pack(side="left", fill="x", expand=True, padx=(0, 8))
        col2 = tk.Frame(row, bg=self.WHITE)
        col2.pack(side="left", fill="x", expand=True, padx=(8, 0))
        self._field_label(col1, "Resolution")
        ttk.Combobox(col1, textvariable=self.resolution, values=["1280x720", "1920x1080"],
                      state="readonly").pack(fill="x")
        self._field_label(col2, "Narration voice")
        ttk.Combobox(col2, textvariable=self.voice,
                     values=["en-US-GuyNeural", "en-US-JennyNeural", "en-GB-RyanNeural", "en-GB-SoniaNeural"],
                     state="readonly").pack(fill="x")

        blender_card = self._card(left, "RENDER ENGINE", "Blender is used to build the 3D scene locally.")
        blender_card.pack(fill="x")
        self._field_label(blender_card, "Blender executable")
        brow = tk.Frame(blender_card, bg=self.WHITE)
        brow.pack(fill="x", padx=18, pady=(0, 16))
        tk.Entry(brow, textvariable=self.blender, bg="#F7F9FC", fg=self.INK,
                 insertbackground=self.INK, relief="flat", font=("Segoe UI", 9),
                 highlightthickness=1, highlightbackground=self.LINE).pack(side="left", fill="x", expand=True, ipady=8)
        tk.Button(brow, text="Browse", command=self._browse_blender, bg=self.PALE_BLUE,
                  fg=self.BLUE, activebackground="#DCEAFF", relief="flat", bd=0,
                  font=("Segoe UI", 9, "bold"), padx=14, pady=8,
                  cursor="hand2").pack(side="left", padx=(8, 0))

        preview = self._card(right, "3D SCENE PREVIEW", "A visual workspace for your selected scene.")
        preview.pack(fill="both", expand=True, pady=(0, 12))
        canvas_wrap = tk.Frame(preview, bg="#101827")
        canvas_wrap.pack(fill="both", expand=True, padx=14, pady=(4, 12))
        self.preview_canvas = tk.Canvas(canvas_wrap, bg="#101827", height=235,
                                        highlightthickness=0, bd=0)
        self.preview_canvas.pack(fill="both", expand=True)
        self._draw_preview()
        tk.Label(preview, text="PREVIEW PLACEHOLDER  •  FINAL SCENE IS RENDERED BY BLENDER",
                 bg=self.WHITE, fg=self.MUTED, font=("Segoe UI", 7, "bold")).pack(anchor="center", pady=(0, 12))

        pipeline = self._card(right, "GENERATION PROGRESS", "Keep this window open while Blender renders.")
        pipeline.pack(fill="x", pady=(0, 12))
        self.progress = ttk.Progressbar(pipeline, mode="indeterminate")
        self.progress.pack(fill="x", padx=16, pady=(8, 6))
        tk.Label(pipeline, textvariable=self.status, bg=self.WHITE, fg=self.MUTED,
                 font=("Segoe UI", 8)).pack(anchor="w", padx=16, pady=(0, 10))

        actions = tk.Frame(right, bg=self.BG)
        actions.pack(fill="x")
        tk.Button(actions, text="✦   GENERATE 3D VIDEO", command=self.generate,
                  bg=self.BLUE, fg=self.WHITE, activebackground="#2563D9",
                  activeforeground=self.WHITE, relief="flat", bd=0,
                  font=("Segoe UI", 10, "bold"), padx=16, pady=14,
                  cursor="hand2").pack(fill="x")
        tk.Button(actions, text="OPEN OUTPUT FOLDER", command=self.open_output,
                  bg=self.WHITE, fg=self.INK, activebackground=self.PALE_BLUE,
                  relief="flat", bd=0, font=("Segoe UI", 9, "bold"),
                  padx=12, pady=11, cursor="hand2").pack(fill="x", pady=(8, 0))

        activity = self._card(page, "RECENT ACTIVITY", "Live messages from your video-generation process.")
        activity.pack(fill="x", pady=(12, 0))
        self.log = tk.Text(activity, bg="#F8FAFD", fg="#526174", insertbackground=self.INK,
                           relief="flat", wrap="word", font=("Consolas", 8), height=4,
                           padx=10, pady=8)
        self.log.pack(fill="x", padx=14, pady=(4, 14))
        self.log.insert("end", "Ready. Choose a style and enter a topic to begin.\n")

    def _draw_preview(self):
        c = self.preview_canvas
        c.delete("all")
        c.update_idletasks()
        w = max(c.winfo_width(), 330)
        h = max(c.winfo_height(), 220)
        c.create_oval(w*.23, h*.10, w*.78, h*.94, fill="#172C50", outline="")
        c.create_oval(w*.30, h*.16, w*.72, h*.82, fill="#315B9B", outline="")
        c.create_oval(w*.37, h*.22, w*.68, h*.70, fill="#6F9BE0", outline="")
        c.create_oval(w*.40, h*.23, w*.52, h*.38, fill="#A9C8F5", outline="")
        c.create_oval(w*.15, h*.10, w*.18, h*.13, fill="#FFFFFF", outline="")
        c.create_oval(w*.83, h*.24, w*.85, h*.27, fill="#FFFFFF", outline="")
        c.create_oval(w*.20, h*.72, w*.22, h*.75, fill="#DDEAFF", outline="")
        c.create_text(w/2, h*.91, text="YOUR 3D WORLD STARTS HERE",
                      fill="#DCE8FA", font=("Segoe UI", 8, "bold"))

    def _select_style(self, name):
        self.style.set(name)
        for label, button in self.style_buttons.items():
            selected = label == name
            button.configure(bg=self.PALE_BLUE if selected else "#F8FAFD",
                             fg=self.BLUE if selected else self.INK,
                             highlightbackground=self.BLUE if selected else self.LINE)

    def _build_projects_page(self):
        page = tk.Frame(self.content, bg=self.BG)
        self.pages["Projects"] = page
        tk.Label(page, text="Your generated videos", bg=self.BG, fg=self.INK,
                 font=("Segoe UI", 20, "bold")).pack(anchor="w")
        tk.Label(page, text="Rendered MP4 files saved in your local output folder.",
                 bg=self.BG, fg=self.MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 18))
        card = self._card(page, "OUTPUT LIBRARY")
        card.pack(fill="both", expand=True)
        self.project_list = tk.Listbox(card, bg=self.WHITE, fg=self.INK, relief="flat",
                                       font=("Segoe UI", 10), selectbackground=self.PALE_BLUE,
                                       selectforeground=self.BLUE, activestyle="none")
        self.project_list.pack(fill="both", expand=True, padx=16, pady=14)
        self._refresh_projects()
        tk.Button(page, text="OPEN OUTPUT FOLDER", command=self.open_output,
                  bg=self.BLUE, fg=self.WHITE, relief="flat", bd=0,
                  font=("Segoe UI", 9, "bold"), padx=16, pady=11).pack(anchor="w", pady=12)

    def _refresh_projects(self):
        if not hasattr(self, "project_list"):
            return
        self.project_list.delete(0, "end")
        for file in sorted(OUT.glob("*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True):
            self.project_list.insert("end", f"  {file.name}     •     {file.stat().st_size // (1024*1024)} MB")

    def _build_templates_page(self):
        page = tk.Frame(self.content, bg=self.BG)
        self.pages["Templates"] = page
        tk.Label(page, text="Start with a creative direction", bg=self.BG, fg=self.INK,
                 font=("Segoe UI", 20, "bold")).pack(anchor="w")
        tk.Label(page, text="Choose a template to apply it to the Create video workspace.",
                 bg=self.BG, fg=self.MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 18))
        for name, desc in [
            ("Cinematic Realistic", "Atmospheric, realistic-inspired 3D scenes."),
            ("Animated Facts", "Bright educational visuals and animated storytelling."),
            ("Viral 3D", "Fast-paced 3D visual direction for short-form ideas."),
            ("Professional Facts", "Clean, polished visuals for informative videos."),
            ("Real Exoplanet Cinematic Exploration", "Science-inspired journeys through confirmed exoplanets."),
        ]:
            card = self._card(page, name, desc)
            card.pack(fill="x", pady=5)
            tk.Button(card, text="USE TEMPLATE", command=lambda n=name: self._use_template(n),
                      bg=self.PALE_BLUE, fg=self.BLUE, relief="flat", bd=0,
                      font=("Segoe UI", 8, "bold"), padx=12, pady=8).pack(anchor="e", padx=16, pady=(0, 12))

    def _use_template(self, name):
        self._select_style(name)
        self._show_page("Create")

    def _build_settings_page(self):
        page = tk.Frame(self.content, bg=self.BG)
        self.pages["Settings"] = page
        tk.Label(page, text="Studio settings", bg=self.BG, fg=self.INK,
                 font=("Segoe UI", 20, "bold")).pack(anchor="w")
        tk.Label(page, text="Configure the local tools used to create your videos.",
                 bg=self.BG, fg=self.MUTED, font=("Segoe UI", 9)).pack(anchor="w", pady=(4, 18))
        card = self._card(page, "BLENDER")
        card.pack(fill="x", pady=6)
        tk.Label(card, text="Blender executable path", bg=self.WHITE, fg=self.MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w", padx=18, pady=(10, 5))
        row = tk.Frame(card, bg=self.WHITE)
        row.pack(fill="x", padx=18, pady=(0, 16))
        tk.Entry(row, textvariable=self.blender, bg="#F7F9FC", fg=self.INK,
                 relief="flat", font=("Segoe UI", 9)).pack(side="left", fill="x", expand=True, ipady=8)
        tk.Button(row, text="Browse", command=self._browse_blender, bg=self.PALE_BLUE,
                  fg=self.BLUE, relief="flat", bd=0, padx=14, pady=8).pack(side="left", padx=8)
        card2 = self._card(page, "RENDERING")
        card2.pack(fill="x", pady=6)
        tk.Label(card2, text="Recommended for an 8 GB RAM PC: start with 1280 × 720. Actual render time depends on scene complexity and frame count.",
                 bg=self.WHITE, fg=self.MUTED, wraplength=760, justify="left",
                 font=("Segoe UI", 9)).pack(anchor="w", padx=18, pady=16)

    def _build_about_page(self):
        page = tk.Frame(self.content, bg=self.BG)
        self.pages["About"] = page
        card = self._card(page, "AGENT ARTIFACTS",
                          "An AI-assisted desktop workspace for researching ideas and creating narrated 3D videos.")
        card.pack(fill="x", pady=8)
        tk.Label(card, text="Agent Artifacts combines topic research, narration, Blender scene generation, and FFmpeg video assembly. The generated visuals are 3D artistic scenes and should be reviewed for factual accuracy before publishing.",
                 bg=self.WHITE, fg=self.MUTED, wraplength=850, justify="left",
                 font=("Segoe UI", 10)).pack(anchor="w", padx=18, pady=(4, 18))
        tk.Label(page, text="Built for local Windows desktop use.", bg=self.BG, fg=self.MUTED,
                 font=("Segoe UI", 9)).pack(anchor="w", pady=10)

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
            if not scene_video.is_file():
                alternatives = sorted(OUT.glob("blender_scene*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
                if alternatives:
                    scene_video = alternatives[0]
                else:
                    blender_log = (result.stdout or "") + "\n" + (result.stderr or "")
                    raise RuntimeError("Blender returned successfully but did not create the expected MP4:\n"
                                       + str(scene_video) + "\n\nBlender output:\n" + blender_log[-6000:])
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
                    self._refresh_projects()
                    messagebox.showinfo("Video ready", "Your video was rendered:\n" + payload)
                elif kind == "error":
                    self.progress.stop()
                    self.status.set("Generation failed — see activity log.")
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
