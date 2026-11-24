
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from pathlib import Path
from datetime import datetime, timezone
import json, os, re, shutil, subprocess, threading, asyncio, queue, textwrap

ROOT=Path(__file__).resolve().parent
DATA=ROOT/"data"; OUT=ROOT/"output"
DATA.mkdir(exist_ok=True); OUT.mkdir(exist_ok=True)
CFG=DATA/"settings.json"
DEFAULT={"openai_key":"","google_json":"","voice":"en-US-GuyNeural","auto":False,"privacy":"public"}
def readcfg():
    try: return {**DEFAULT,**json.loads(CFG.read_text(encoding="utf-8"))}
    except: return DEFAULT.copy()
def savecfg(c): CFG.write_text(json.dumps(c,indent=2),encoding="utf-8")

class App:
 def __init__(self,root):
    self.r=root; self.r.title("Agent Artifacts"); self.r.geometry("1120x760"); self.r.minsize(900,650); self.r.configure(bg="#f6f8fc")
    self.cfg=readcfg(); self.q=queue.Queue(); self.busy=False; self.video=None; self.title="Facts You Should Know"; self.description=""
    self.style(); self.build(); self.poll(); self.log("Welcome. Configure OpenAI and Google OAuth in Settings to enable generation and uploads.")
 def style(self):
    s=ttk.Style(); s.theme_use("clam"); s.configure("TNotebook",background="#f6f8fc",borderwidth=0)
    s.configure("TNotebook.Tab",background="#eef2f7",foreground="#536176",padding=(18,10),font=("Segoe UI",10,"bold"))
    s.map("TNotebook.Tab",background=[("selected","#4559d6")],foreground=[("selected","white")])
    s.configure("TCombobox",fieldbackground="#ffffff",background="#ffffff",foreground="#263248")
    s.configure("Treeview",background="#ffffff",foreground="#263248",fieldbackground="#ffffff",rowheight=30)
    s.configure("Treeview.Heading",background="#e6ebf3",foreground="#263248")
 def label(self,p,t,size=10,color="#536176",bold=False):
    return tk.Label(p,text=t,bg=p.cget("bg"),fg=color,font=("Segoe UI",size,"bold" if bold else "normal"))
 def button(self,p,t,fn,primary=False):
    return tk.Button(p,text=t,command=fn,bg="#3867f5" if primary else "#edf2ff",fg="white" if primary else "#263248",activebackground="#dce6ff",relief="flat",bd=0,padx=14,pady=10,cursor="hand2",font=("Segoe UI",9,"bold"))
 def card(self,p,t):
    f=tk.Frame(p,bg="#ffffff",highlightbackground="#e3e8f0",highlightthickness=1)
    self.label(f,t,10,"#172033",True).pack(anchor="w",padx=14,pady=(12,8)); return f
 def build(self):
    h=tk.Frame(self.r,bg="#f6f8fc"); h.pack(fill="x",padx=24,pady=18)
    self.label(h,"✦",30,"#3867f5",True).pack(side="left")
    x=tk.Frame(h,bg="#f6f8fc"); x.pack(side="left",padx=10)
    self.label(x,"AGENT ARTIFACTS",18,"#172033",True).pack(anchor="w")
    self.label(x,"AI VIDEO INTELLIGENCE  /  CREATOR STUDIO",8,"#778399",True).pack(anchor="w")
    self.status=tk.Label(h,text="● READY",bg="#f6f8fc",fg="#15966b",font=("Segoe UI",9,"bold")); self.status.pack(side="right")
    self.nb=ttk.Notebook(self.r); self.nb.pack(fill="both",expand=True,padx=22,pady=(0,18))
    self.home=tk.Frame(self.nb,bg="#f6f8fc"); self.make=tk.Frame(self.nb,bg="#f6f8fc"); self.settings=tk.Frame(self.nb,bg="#f6f8fc"); self.history=tk.Frame(self.nb,bg="#f6f8fc")
    for tab,name in [(self.home,"Overview"),(self.make,"Create video"),(self.settings,"Settings"),(self.history,"Activity")]: self.nb.add(tab,text="  "+name+"  ")
    self.build_home(); self.build_make(); self.build_settings(); self.build_history()
 def build_home(self):
    self.label(self.home,"Your AI creator command center",18,"#172033",True).pack(anchor="w",padx=12,pady=(20,5))
    self.label(self.home,"Research a topic, write a script, create a narrated video, then publish it to YouTube.",10,"#667085").pack(anchor="w",padx=12,pady=(0,18))
    row=tk.Frame(self.home,bg="#f6f8fc"); row.pack(fill="x",padx=6)
    for head,val,sub in [("CONTENT","FACTS","Curiosity-led educational videos"),("WORKFLOW","4 STAGES","Research · Script · Render · Publish"),("PUBLISH MODE","AUTOMATIC","You choose when to enable it")]:
        c=self.card(row,head); c.pack(side="left",fill="both",expand=True,padx=5)
        self.label(c,val,20,"#172033",True).pack(anchor="w",padx=14)
        self.label(c,sub,8,"#667085").pack(anchor="w",padx=14,pady=(4,14))
    c=self.card(self.home,"QUICK START"); c.pack(fill="x",padx=10,pady=16)
    self.label(c,"1  Configure API keys in Settings.",10).pack(anchor="w",padx=14,pady=4)
    self.label(c,"2  Create and review a facts script.",10).pack(anchor="w",padx=14,pady=4)
    self.label(c,"3  Render an MP4 and publish or schedule it.",10).pack(anchor="w",padx=14,pady=4)
    self.label(c,"The app must remain open while it renders or sends an upload. Scheduled publication is handled by YouTube after a successful scheduled upload.",9,"#667085").pack(anchor="w",padx=14,pady=(8,14))
    self.button(c,"OPEN VIDEO WORKSPACE →",lambda:self.nb.select(self.make),True).pack(anchor="w",padx=14,pady=(0,14))
 def build_make(self):
    left=tk.Frame(self.make,bg="#f6f8fc"); left.pack(side="left",fill="both",expand=True,padx=(6,10),pady=14)
    right=tk.Frame(self.make,bg="#f6f8fc",width=300); right.pack(side="right",fill="y",padx=(0,6),pady=14); right.pack_propagate(False)
    c=self.card(left,"VIDEO BRIEF"); c.pack(fill="x",pady=(0,10))
    self.label(c,"Topic or question",9,"#667085").pack(anchor="w",padx=14)
    self.topic=tk.StringVar(value="Amazing facts about space")
    self.topic_entry=tk.Entry(c,textvariable=self.topic,bg="#f5f7fb",fg="#263248",insertbackground="#263248",relief="flat",font=("Segoe UI",10)); self.topic_entry.pack(fill="x",padx=14,pady=7,ipady=8)
    r=tk.Frame(c,bg="#ffffff"); r.pack(fill="x",padx=14,pady=(0,12))
    self.label(r,"Length").pack(side="left"); self.minutes=tk.StringVar(value="1"); ttk.Combobox(r,textvariable=self.minutes,values=["1","2","3","5"],width=6,state="readonly").pack(side="left",padx=8)
    self.label(r,"Format").pack(side="left",padx=(15,4)); self.res=tk.StringVar(value="1280x720"); ttk.Combobox(r,textvariable=self.res,values=["1280x720","1920x1080","1080x1920"],width=12,state="readonly").pack(side="left")
    sc=self.card(left,"EDITABLE SCRIPT"); sc.pack(fill="both",expand=True)
    self.script=tk.Text(sc,bg="#f5f7fb",fg="#263248",insertbackground="white",relief="flat",font=("Consolas",10),wrap="word",height=17,padx=12,pady=12); self.script.pack(fill="both",expand=True,padx=10,pady=(0,10))
    actions=tk.Frame(left,bg="#f6f8fc"); actions.pack(fill="x",pady=8)
    self.button(actions,"✦ GENERATE SCRIPT",self.generate,True).pack(side="left")
    self.button(actions,"SAVE SCRIPT",self.save_script).pack(side="left",padx=8)
    self.button(actions,"RENDER VIDEO",self.render).pack(side="left")
    c=self.card(right,"PRODUCTION PIPELINE"); c.pack(fill="x",pady=(0,10))
    self.progress=ttk.Progressbar(c,maximum=100); self.progress.pack(fill="x",padx=14,pady=8)
    self.ptext=self.label(c,"Waiting for a topic",9,"#667085"); self.ptext.pack(anchor="w",padx=14,pady=(0,10))
    for t in ["01  Research source notes","02  Generate narration script","03  Create AI voiceover","04  Design fact-card visuals","05  Render MP4","06  Upload to YouTube"]: self.label(c,t,9).pack(anchor="w",padx=14,pady=5)
    c=self.card(right,"PUBLISHING"); c.pack(fill="x",pady=(0,10))
    self.auto=tk.BooleanVar(value=bool(self.cfg["auto"])); tk.Checkbutton(c,text="Auto-publish after rendering",variable=self.auto,bg="#ffffff",fg="#263248",selectcolor="#e6ebf3",activebackground="#ffffff").pack(anchor="w",padx=12,pady=7)
    self.privacy=tk.StringVar(value=self.cfg["privacy"]); ttk.Combobox(c,textvariable=self.privacy,values=["public","unlisted","private"],state="readonly").pack(fill="x",padx=12,pady=(0,10))
    self.button(c,"UPLOAD CURRENT VIDEO",self.upload,True).pack(fill="x",padx=12,pady=(0,8))
    self.button(c,"SCHEDULE CURRENT VIDEO",self.schedule).pack(fill="x",padx=12,pady=(0,12))
    log=self.card(right,"LIVE LOG"); log.pack(fill="both",expand=True)
    self.logbox=tk.Text(log,bg="#f5f7fb",fg="#15966b",height=8,relief="flat",font=("Consolas",8),wrap="word"); self.logbox.pack(fill="both",expand=True,padx=10,pady=(0,10))
 def build_settings(self):
    self.label(self.settings,"Connect your tools",18,"#172033",True).pack(anchor="w",padx=12,pady=(20,5))
    self.label(self.settings,"Credentials are stored locally on this PC. Never share your settings folder.",9,"#667085").pack(anchor="w",padx=12,pady=(0,12))
    c=self.card(self.settings,"AI SCRIPT GENERATION"); c.pack(fill="x",padx=8,pady=6)
    self.label(c,"OpenAI API key",9).pack(anchor="w",padx=14)
    self.openai=tk.StringVar(value=self.cfg["openai_key"]); tk.Entry(c,textvariable=self.openai,show="•",bg="#f5f7fb",fg="white",insertbackground="white",relief="flat").pack(fill="x",padx=14,pady=(5,14),ipady=7)
    c=self.card(self.settings,"YOUTUBE CHANNEL CONNECTION"); c.pack(fill="x",padx=8,pady=6)
    self.label(c,"Google OAuth Desktop client JSON file",9).pack(anchor="w",padx=14)
    row=tk.Frame(c,bg="#ffffff"); row.pack(fill="x",padx=14,pady=(5,14))
    self.google=tk.StringVar(value=self.cfg["google_json"]); tk.Entry(row,textvariable=self.google,bg="#f5f7fb",fg="white",insertbackground="white",relief="flat").pack(side="left",fill="x",expand=True,ipady=7)
    self.button(row,"BROWSE",self.browse).pack(side="left",padx=7)
    self.label(c,"Google Cloud setup: create a project → enable YouTube Data API v3 → configure OAuth consent → create OAuth Client ID (Desktop app) → download JSON → select it above.",9,"#667085").pack(anchor="w",padx=14,pady=(0,12))
    c=self.card(self.settings,"VOICE"); c.pack(fill="x",padx=8,pady=6)
    self.voice=tk.StringVar(value=self.cfg["voice"]); ttk.Combobox(c,textvariable=self.voice,values=["en-US-GuyNeural","en-US-AriaNeural","en-GB-RyanNeural","en-GB-SoniaNeural"],state="readonly",width=28).pack(anchor="w",padx=14,pady=(0,14))
    self.button(self.settings,"SAVE SETTINGS",self.save,True).pack(anchor="w",padx=12,pady=12)
 def build_history(self):
    self.label(self.history,"Production activity",18,"#172033",True).pack(anchor="w",padx=12,pady=18)
    self.tree=ttk.Treeview(self.history,columns=("date","topic","status","file"),show="headings")
    for c,t,w in [("date","Created",150),("topic","Topic",280),("status","Status",130),("file","Output file",450)]: self.tree.heading(c,text=t); self.tree.column(c,width=w)
    self.tree.pack(fill="both",expand=True,padx=12,pady=8); self.refresh_history()
    self.button(self.history,"OPEN OUTPUT FOLDER",lambda:os.startfile(str(OUT)) if os.name=="nt" else None).pack(anchor="w",padx=12,pady=8)
 def log(self,msg): self.q.put(("log",msg))
 def update_progress(self,n,msg): self.q.put(("progress",n,msg))
 def poll(self):
    try:
     while True:
      item=self.q.get_nowait()
      if item[0]=="log": self.logbox.insert("end",f"[{datetime.now():%H:%M:%S}] {item[1]}\n"); self.logbox.see("end")
      elif item[0]=="progress": self.progress["value"]=item[1]; self.ptext.config(text=item[2])
      elif item[0]=="script": self.script.delete("1.0","end"); self.script.insert("1.0",item[1])
      elif item[0]=="history": self.refresh_history()
      elif item[0]=="error": messagebox.showerror("Autopilot AI",item[1])
      elif item[0]=="done": self.busy=False; self.status.config(text="● READY",fg="#15966b")
    except queue.Empty: pass
    self.r.after(150,self.poll)
 def run(self,fn):
    if self.busy: messagebox.showinfo("Busy","A task is already running."); return
    self.busy=True; self.status.config(text="● WORKING",fg="#c27a18")
    def go():
     try: fn()
     except Exception as e: self.log("ERROR: "+str(e)); self.q.put(("error",str(e)))
     finally: self.q.put(("done",None))
    threading.Thread(target=go,daemon=True).start()
 def save(self):
    self.cfg.update(openai_key=self.openai.get().strip(),google_json=self.google.get().strip(),voice=self.voice.get(),auto=self.auto.get(),privacy=self.privacy.get())
    savecfg(self.cfg); self.log("Settings saved locally."); messagebox.showinfo("Saved","Settings saved.")
 def browse(self):
    p=filedialog.askopenfilename(filetypes=[("JSON files","*.json")])
    if p: self.google.set(p)
 def openai_client(self):
    from openai import OpenAI
    key=self.openai.get().strip()
    if not key: raise RuntimeError("Add your OpenAI API key in Settings.")
    return OpenAI(api_key=key)
 def research(self,topic):
    import requests
    api="https://en.wikipedia.org/w/api.php"
    data=requests.get(api,params={"action":"query","list":"search","srsearch":topic,"format":"json","srlimit":4},timeout=25).json()
    sources=[]
    for hit in data.get("query",{}).get("search",[])[:4]:
     title=hit["title"]
     page=requests.get(api,params={"action":"query","prop":"extracts","exintro":1,"explaintext":1,"titles":title,"format":"json"},timeout=25).json()
     pages=page.get("query",{}).get("pages",{})
     extract=next(iter(pages.values())).get("extract","")
     if extract: sources.append((title,"https://en.wikipedia.org/wiki/"+title.replace(" ","_"),extract[:2200]))
    return sources
 def generate(self):
    topic=self.topic.get().strip()
    if not topic: messagebox.showwarning("Topic","Enter a topic first."); return
    def task():
     self.log("Researching source material for "+topic); self.update_progress(12,"Finding background sources")
     src=self.research(topic)
     if not src: raise RuntimeError("No source notes found. Try a different topic.")
     self.update_progress(40,"Writing researched script")
     notes="\n\n".join(f"{a} ({b})\n{c}" for a,b,c in src)
     prompt=f"""Write a compelling factual YouTube script about {topic}, about {self.minutes.get()} minute(s). Use only claims supported by these notes; do not invent dates, quotes or statistics. Begin with a strong hook. Return TITLE: on one line, DESCRIPTION: on one line, then SCRIPT: and spoken narration, then SOURCES: with source URLs. Notes:\n{notes}"""
     response=self.openai_client().chat.completions.create(model="gpt-4o-mini",messages=[{"role":"system","content":"You are a cautious educational fact-checking scriptwriter. Accuracy before drama."},{"role":"user","content":prompt}],temperature=.45)
     self.q.put(("script",response.choices[0].message.content.strip())); self.update_progress(100,"Script ready — review before rendering"); self.log("Script generated. Edit it in the text area before rendering.")
    self.run(task)
 def save_script(self):
    p=filedialog.asksaveasfilename(defaultextension=".txt",filetypes=[("Text","*.txt")],initialdir=str(OUT))
    if p: Path(p).write_text(self.script.get("1.0","end").strip(),encoding="utf-8")
 def parse(self):
    s=self.script.get("1.0","end").strip()
    if not s: raise RuntimeError("Generate or paste a script first.")
    m=re.search(r"(?is)SCRIPT:\s*(.*?)(?:\nSOURCES:|$)",s); narration=m.group(1).strip() if m else s
    mt=re.search(r"(?im)^TITLE:\s*(.+)$",s); md=re.search(r"(?im)^DESCRIPTION:\s*(.+)$",s)
    return narration,mt.group(1).strip() if mt else self.topic.get(),md.group(1).strip() if md else "Interesting facts explained."
 def render(self):
    try: narration,title,desc=self.parse()
    except Exception as e: messagebox.showwarning("Script needed",str(e)); return
    self.save()
    def task():
     if not shutil.which("ffmpeg") or not shutil.which("ffprobe"): raise RuntimeError("Install FFmpeg and add its bin folder to Windows PATH.")
     from PIL import Image,ImageDraw,ImageFont
     import edge_tts
     self.update_progress(10,"Generating AI narration"); self.log("Creating voiceover.")
     async def tts(): await edge_tts.Communicate(narration,self.voice.get()).save(str(OUT/"voice.mp3"))
     asyncio.run(tts())
     probe=subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(OUT/"voice.mp3")],capture_output=True,text=True,check=True)
     duration=float(probe.stdout.strip())
     sentences=re.split(r"(?<=[.!?])\s+",narration); chunks=[]; cur=""
     for s in sentences:
      if len(cur)+len(s)>180 and cur: chunks.append(cur); cur=s
      else: cur=(cur+" "+s).strip()
     if cur: chunks.append(cur)
     chunks=chunks[:18] or [narration]
     w,h=map(int,self.res.get().split("x"))
     fontfile=next((p for p in ["C:/Windows/Fonts/seguisb.ttf","C:/Windows/Fonts/arial.ttf"] if Path(p).exists()),None)
     titlefont=ImageFont.truetype(fontfile,max(26,int(w*.045))) if fontfile else ImageFont.load_default()
     bodyfont=ImageFont.truetype(fontfile,max(20,int(w*.031))) if fontfile else ImageFont.load_default()
     files=[]
     self.update_progress(35,"Designing visual fact cards")
     for i,chunk in enumerate(chunks):
      im=Image.new("RGB",(w,h),(9,17,37)); d=ImageDraw.Draw(im)
      d.rounded_rectangle((int(w*.05),int(h*.07),int(w*.95),int(h*.93)),radius=32,fill=(18,31,60),outline=(80,100,205),width=3)
      d.text((int(w*.10),int(h*.14)),"DID YOU KNOW?",font=titlefont,fill=(130,155,255))
      d.text((int(w*.10),int(h*.25)),f"FACT {i+1:02d}",font=bodyfont,fill=(103,224,184))
      words=chunk.split(); lines=[]; line=""; maxw=int(w*.78)
      for word in words:
       test=(line+" "+word).strip()
       if d.textbbox((0,0),test,font=bodyfont)[2]<=maxw: line=test
       else:
        if line: lines.append(line)
        line=word
      if line: lines.append(line)
      y=int(h*.40)
      for ln in lines[:8]: d.text((int(w*.10),y),ln,font=bodyfont,fill=(245,247,255)); y+=int(h*.06)
      d.text((int(w*.10),int(h*.85)),"YOUTUBE AUTOPILOT AI  •  FACTS",font=bodyfont,fill=(130,147,180))
      p=OUT/f"slide_{i:02d}.png"; im.save(p); files.append(p)
     self.update_progress(65,"Rendering MP4 video")
     each=max(1,duration/len(files)); concat=OUT/"slides.txt"
     with concat.open("w",encoding="utf-8") as f:
      for p in files: f.write(f"file '{p.as_posix()}'\nduration {each:.4f}\n")
      f.write(f"file '{files[-1].as_posix()}'\n")
     out=OUT/f"facts_{datetime.now():%Y%m%d_%H%M%S}.mp4"
     cmd=["ffmpeg","-y","-f","concat","-safe","0","-i",str(concat),"-i",str(OUT/"voice.mp3"),"-vf","fps=30,format=yuv420p","-c:v","libx264","-preset","fast","-crf","22","-c:a","aac","-shortest",str(out)]
     p=subprocess.run(cmd,capture_output=True,text=True)
     if p.returncode: raise RuntimeError("FFmpeg failed: "+p.stderr[-900:])
     self.video=str(out); self.title=title; self.description=desc; self.log("Video rendered: "+str(out)); self.add_history("Rendered",str(out))
     if self.auto.get():
      self.log("Auto-publish is enabled. Upload starting."); self.upload_impl(out,title,desc)
     else: self.log("Auto-publish is off. Review the MP4, then upload when ready.")
     self.update_progress(100,"Video complete")
    self.run(task)
 def youtube(self):
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaFileUpload
    scopes=["https://www.googleapis.com/auth/youtube.upload"]; client=Path(self.google.get().strip())
    if not client.exists(): raise RuntimeError("Choose your Google OAuth Desktop client JSON in Settings.")
    token=DATA/"youtube_token.json"; creds=None
    if token.exists(): creds=Credentials.from_authorized_user_file(str(token),scopes)
    if creds and creds.expired and creds.refresh_token: creds.refresh(Request())
    if not creds or not creds.valid:
     flow=InstalledAppFlow.from_client_secrets_file(str(client),scopes); creds=flow.run_local_server(port=0); token.write_text(creds.to_json(),encoding="utf-8")
    return build("youtube","v3",credentials=creds),MediaFileUpload
 def upload_impl(self,path,title,desc,publish=None):
    service,Media=self.youtube()
    status={"privacyStatus":"private" if publish else self.privacy.get(),"selfDeclaredMadeForKids":False}
    if publish: status["publishAt"]=publish
    body={"snippet":{"title":title[:100],"description":(desc+"\n\nCreated with Agent Artifacts.")[:5000],"categoryId":"27","tags":["facts","education","interesting facts"]},"status":status}
    req=service.videos().insert(part="snippet,status",body=body,media_body=Media(str(path),chunksize=-1,resumable=True))
    response=None
    while response is None:
     stat,response=req.next_chunk()
     if stat: self.log(f"Upload progress: {int(stat.progress()*100)}%")
    url="https://www.youtube.com/watch?v="+response["id"]; self.log("Published/uploaded: "+url); self.add_history("Uploaded",str(path))
 def upload(self):
    if not self.video or not Path(self.video).exists(): messagebox.showwarning("No video","Render a video first."); return
    self.run(lambda:self.upload_impl(self.video,self.title,self.description))
 def schedule(self):
    if not self.video or not Path(self.video).exists(): messagebox.showwarning("No video","Render a video first."); return
    val=simpledialog.askstring("Schedule upload","Future UTC time, e.g. 2026-12-01T15:30:00Z")
    if not val:return
    try:
     dt=datetime.fromisoformat(val.replace("Z","+00:00"))
     if dt.tzinfo is None or dt<=datetime.now(timezone.utc): raise ValueError()
    except: messagebox.showerror("Invalid time","Use a future ISO-8601 timestamp with timezone."); return
    self.run(lambda:self.upload_impl(self.video,self.title,self.description,dt.astimezone(timezone.utc).isoformat().replace("+00:00","Z")))
 def add_history(self,status,path):
    p=DATA/"history.json"
    try: hist=json.loads(p.read_text(encoding="utf-8"))
    except: hist=[]
    hist.insert(0,{"date":datetime.now().strftime("%Y-%m-%d %H:%M"),"topic":self.topic.get(),"status":status,"file":path}); p.write_text(json.dumps(hist[:100],indent=2),encoding="utf-8")
    self.q.put(("history",None))
 def refresh_history(self):
    if not hasattr(self,"tree"): return
    for i in self.tree.get_children(): self.tree.delete(i)
    try: hist=json.loads((DATA/"history.json").read_text(encoding="utf-8"))
    except: hist=[]
    for h in hist: self.tree.insert("","end",values=(h["date"],h["topic"],h["status"],h["file"]))
if __name__=="__main__":
 root=tk.Tk(); App(root); root.mainloop()
