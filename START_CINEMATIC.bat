@echo off
title Agent Artifacts - Cinematic Studio
cd /d "%~dp0"
py -3 cinematic_app.py
if errorlevel 1 pause
