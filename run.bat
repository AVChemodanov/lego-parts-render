@echo off

:start

set "workpath=new"

set /p workpath="Enter path to folder with files; Leave blank to process NEW: "
set /p image_count="Enter image count for every single part: "

if not exist %workpath%\ (
   echo "Folder %workpath% does not exists"
   goto:start
)

for /d %%D in (%workpath%/*) do (
	echo %%D
	start cmd /k blender --background --python render_parts.py -- %workpath% %image_count% rem %render_engine%

)
 
