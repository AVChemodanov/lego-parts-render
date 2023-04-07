@echo off

:start

set "workpath=new"
set "render_engine=BLENDER_EEVEE"
set "image_count=1"
set "threads=1"
set "mode=M"

set /p workpath="Enter path to folder with files; Leave blank to process NEW: "
set /p render_engine="Enter render engine; Leave blank for BLENDER_EEVEE or enter CYCLES: "
set /p mode="Enter rendering mode; S for STEREO mode or leave blank for MONO mode: "
set /p image_count="Enter image count for every single part; Leave blank for 1: "
set /p threads="Enter thread count; Leave blank for 1: "


if not exist %workpath%\ (
   echo "Folder %workpath% does not exists"
   goto:start
)


set /a i=0

setlocal ENABLEDELAYEDEXPANSION

for /d %%D in (%workpath%/*) do (
    set /a i=i+1
    if !i! gtr %threads% goto :continue

	start cmd /k blender --background --python render_parts.py -- %workpath%\%%D %image_count% %render_engine% %mode%
)

:continue

endlocal

