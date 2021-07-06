for %%f in (*.py) do (
    blender -b --python "%%~nf.py"
    PAUSE
)