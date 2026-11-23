YOUTUBE AUTOPILOT AI — WINDOWS
==============================

FEATURES
- Topic research using Wikipedia's public API.
- OpenAI-powered facts script generation grounded in retrieved source notes.
- Editable script before rendering.
- Microsoft Edge neural voice narration.
- Designed fact-card slide video rendered as MP4 using FFmpeg.
- YouTube upload and scheduled publication using the official YouTube Data API.
- Local activity history.

INSTALL
1. Install Python 3.10+ from https://www.python.org/downloads/ and check "Add Python to PATH".
2. Install FFmpeg from https://ffmpeg.org/download.html and add its bin folder to Windows PATH.
3. Double-click INSTALL.bat.
4. Double-click START.bat.

OPENAI SETUP
- Create an API key on the OpenAI developer platform and paste it in Settings.
- API usage is billed separately; a ChatGPT subscription does not include API credits.

YOUTUBE SETUP
1. Go to https://console.cloud.google.com/
2. Create/select a project and enable YouTube Data API v3.
3. Configure OAuth consent screen. If in testing, add your Google account as a test user.
4. Create OAuth Client ID with application type Desktop app.
5. Download the JSON and choose it in Settings.
6. On first upload, sign in to Google and approve the YouTube upload permission.

USE
- Create video -> enter a topic -> Generate Script -> review/edit -> Render Video.
- Auto-publish is enabled by default. Turn it off to review the rendered MP4 first.
- Use Upload Current Video or Schedule Current Video for manual publishing.
- Scheduled uploads use YouTube's private + publishAt workflow. The timestamp must be a future ISO-8601 time with timezone, e.g. 2026-12-01T15:30:00Z.

LIMITATIONS / SAFETY
- This desktop app must be open to generate/render/upload. Once a scheduled upload has been accepted by YouTube, YouTube handles the publication time.
- The current renderer makes narrated fact-card/slideshow videos, not AI-generated cinematic footage.
- Research uses Wikipedia summaries as starting source notes, not exhaustive fact-checking. Review claims and source links before publishing.
- OpenAI API, YouTube API quotas, Google OAuth verification, channel eligibility and service terms apply.
- Credentials are stored locally in data/settings.json and data/youtube_token.json. Keep this folder private.
- Avoid copyrighted music or footage unless you have rights to use them.
