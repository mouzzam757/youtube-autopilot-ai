YOUTUBE AUTOPILOT AI — CINEMATIC ENGINE ADD-ON
==============================================

This adds a separate 3D video generator without deleting your existing app.py.

NEW FILES
- cinematic_app.py: desktop interface and generation workflow
- blender_scene.py: procedural Blender scene and camera animation
- START_CINEMATIC.bat: launches the new interface

REQUIREMENTS
1. Python 3.10 or newer
2. Blender 4.2 LTS or newer (free): https://www.blender.org/download/
3. FFmpeg (free): https://ffmpeg.org/download.html
4. Python packages: requests and edge-tts

INSTALL
1. Open Command Prompt in this project folder.
2. Run: py -3 -m pip install requests edge-tts
3. Install Blender and FFmpeg.
4. Add FFmpeg's bin folder to Windows PATH, or put ffmpeg.exe in this folder's ffmpeg\bin folder.
5. Double-click START_CINEMATIC.bat.
6. If Blender is not detected automatically, browse to blender.exe in the app.

HOW TO USE
1. Enter a topic.
2. Choose one of the five video styles.
3. Keep 1280x720 selected on an 8 GB RAM computer.
4. Click GENERATE 3D VIDEO.
5. Wait for Blender to render. The finished MP4 is saved in output.

THE FIVE STYLES
- Cinematic Realistic
- Animated Facts
- Viral 3D
- Professional Facts
- Real Exoplanet Cinematic Exploration

IMPORTANT LIMITATIONS
- This is a first procedural 3D renderer. It creates moving Blender scenes, not a slideshow.
- It does not generate photorealistic AI video footage. That requires a capable local generative video model or a paid hosted video-generation service.
- The four general styles currently use a shared procedural planet/world scene with different visual treatments. The fifth style retrieves a confirmed exoplanet record from NASA's Exoplanet Archive and labels the scene as an artistic visualization.
- The generated exoplanet surface is not an actual photograph or a scientifically established surface reconstruction.
- The script uses Wikipedia summary text as a starting point for general topics. Verify claims and add trusted sources before publishing.
- Edge TTS requires an internet connection. Its service availability and terms may change.
- Blender renders on the local PC. 8 GB RAM is a tight limit. Start at 720p; rendering can be slow. Close other applications.
- YouTube upload is still handled by the existing app.py. This add-on currently renders the MP4 but does not auto-upload it.
