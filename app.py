            chunks = chunks[:20] or [narration]
            w, h = map(int, resolution.split("x"))
            slides = []
            for i, chunk in enumerate(chunks):
                slides.append(self.make_slide(chunk, i, len(chunks), w, h, style, title))
                path = OUT / f"slide_{i:03d}.png"; slides[-1].save(path)
                self.update_progress(25 + int(35*(i+1)/len(chunks)), f"Designing visual {i+1}/{len(chunks)}")
            self.update_progress(65, "Rendering MP4 video")
            each = max(1.0, duration / len(chunks))
            concat = OUT / "slides.txt"
            with concat.open("w", encoding="utf-8") as f:
                for i in range(len(chunks)):
                    p = (OUT / f"slide_{i:03d}.png").as_posix().replace("'", "'\\''")
                    f.write(f"file '{p}'\nduration {each:.4f}\n")
                p = (OUT / f"slide_{len(chunks)-1:03d}.png").as_posix().replace("'", "'\\''")
                f.write(f"file '{p}'\n")
            output = OUT / f"youtube_video_{datetime.now():%Y%m%d_%H%M%S}.mp4"
            cmd = [ffmpeg, "-y", "-f", "concat", "-safe", "0", "-i", str(concat),
                   "-i", str(OUT / "voice.mp3"), "-vf", "fps=30,format=yuv420p",
                   "-c:v", "libx264", "-preset", "fast", "-crf", "21",
                   "-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(output)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode: raise RuntimeError("FFmpeg failed:\n" + result.stderr[-1800:])
            self.video, self.title, self.description = str(output), title, desc
            self.log(f"Rendered {style} video: {output}"); self.add_history("Rendered", str(output))
            if auto:
                self.log("Auto-publish is enabled; uploading.")
                self.upload_impl(output, title, desc)
            else: self.log("Render complete. Preview the MP4 before uploading.")
            self.update_progress(100, "Video completed successfully")
        self.run(task)

    # Google OAuth and YouTube upload
    def youtube(self):
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
        scopes = ["https://www.googleapis.com/auth/youtube.upload"]
        client = Path(self.google.get().strip())
        if not client.is_file():
            raise RuntimeError("Select your Google OAuth Desktop client JSON in Settings.")
        token = DATA / "youtube_token.json"
        creds = None
        if token.exists():
            try: creds = Credentials.from_authorized_user_file(str(token), scopes)
            except Exception: token.unlink(missing_ok=True)
        if creds and creds.expired and creds.refresh_token: creds.refresh(Request())
        if not creds or not creds.valid:
            flow = InstalledAppFlow.from_client_secrets_file(str(client), scopes)
            creds = flow.run_local_server(port=0, open_browser=True)
            token.write_text(creds.to_json(), encoding="utf-8")
        return build("youtube", "v3", credentials=creds), MediaFileUpload

    def upload_impl(self, path, title, desc, publish_at=None):
        service, Media = self.youtube()
        status = {"privacyStatus": "private" if publish_at else self.privacy.get(),
                  "selfDeclaredMadeForKids": False}
        if publish_at: status["publishAt"] = publish_at
        body = {"snippet": {"title": title[:100],
                            "description": (desc + "\n\nCreated with YouTube Autopilot AI.")[:5000],
                            "categoryId": "27", "tags": ["facts", "education", "interesting facts"]},
                "status": status}
        req = service.videos().insert(part="snippet,status", body=body,
                                      media_body=Media(str(path), chunksize=8*1024*1024, resumable=True))
        response = None
        while response is None:
            progress, response = req.next_chunk()
            if progress: self.log(f"YouTube upload: {int(progress.progress()*100)}%")
        url = "https://www.youtube.com/watch?v=" + response["id"]
        self.log("YouTube upload completed: " + url)
        self.add_history("Uploaded / Scheduled", str(path))

    def upload(self):
        if not self.video or not Path(self.video).is_file():
            messagebox.showwarning("No video", "Render a video first."); return
        p, t, d = self.video, self.title, self.description
        self.run(lambda: self.upload_impl(p, t, d))

    def schedule(self):
        if not self.video or not Path(self.video).is_file():
            messagebox.showwarning("No video", "Render a video first."); return
        value = simpledialog.askstring("Schedule upload", "Future UTC time, e.g. 2026-12-01T15:30:00Z")
        if not value: return
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if dt.tzinfo is None or dt <= datetime.now(timezone.utc): raise ValueError()
        except Exception:
            messagebox.showerror("Invalid time", "Enter a future ISO-8601 date/time with timezone."); return
        when = dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")
        p, t, d = self.video, self.title, self.description
        self.run(lambda: self.upload_impl(p, t, d, when))

    # Activity history
    def add_history(self, status, path):
        file = DATA / "history.json"
        try: history = json.loads(file.read_text(encoding="utf-8"))
        except Exception: history = []
        history.insert(0, {"date": datetime.now().strftime("%Y-%m-%d %H:%M"),
                           "topic": self.topic.get(), "status": status, "file": str(path)})
        file.write_text(json.dumps(history[:100], indent=2), encoding="utf-8")
        self.q.put(("history", None))

    def refresh_history(self):
        if not hasattr(self, "tree"): return
        for item in self.tree.get_children(): self.tree.delete(item)
        try: history = json.loads((DATA / "history.json").read_text(encoding="utf-8"))
        except Exception: history = []
        for item in history:
            self.tree.insert("", "end", values=(item.get("date", ""), item.get("topic", ""),
                             item.get("status", ""), item.get("file", "")))


if __name__ == "__main__":
    root = tk.Tk()
    App(root)
    root.mainloop()
