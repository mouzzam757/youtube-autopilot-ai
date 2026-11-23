YOUTUBE AUTOPILOT AI — PORTABLE WINDOWS BUILD
================================================

You asked for a version that does NOT require Python or FFmpeg to be installed on the PC that runs the app.

This package includes the app source and a Windows cloud-build workflow. GitHub Actions builds a single standalone EXE that bundles the Python runtime, Python dependencies, FFmpeg and FFprobe.

I cannot compile a native Windows EXE in this workspace. The included GitHub Actions workflow performs that build on a Windows machine for you.

GET THE PORTABLE EXE
1. Sign in to GitHub and create a NEW repository, e.g. youtube-autopilot-ai.
2. Upload the contents of this ZIP into the repository. Keep the hidden .github folder.
3. Open the repository's Actions tab.
4. Select "Build YouTube Autopilot AI for Windows".
5. Click "Run workflow" if it did not start automatically.
6. Wait for the workflow to finish with a green check.
7. Open the completed run and download the artifact named:
   YouTube-Autopilot-AI-Windows-Portable
8. Extract the artifact and run YouTube-Autopilot-AI.exe.

The target Windows PC does NOT need separate Python or FFmpeg installation.

APP SETUP
- Add your OpenAI API key in Settings.
- Add your Google OAuth Desktop client JSON.
- Internet is still required for AI scripts, research, voice synthesis and YouTube uploads.
- OpenAI API usage, Google OAuth requirements and YouTube API quotas apply.
- The app creates data and output folders next to the EXE. Keep API keys and token files private.

CURRENT VIDEO ENGINE
Creates narrated fact-card slideshow videos with voiceover and MP4 export. It does not yet create cinematic AI footage. Review factual claims and sources before automatic publication.
