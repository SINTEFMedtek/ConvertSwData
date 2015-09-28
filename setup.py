# -*- coding: utf-8 -*-

#coding=utf-8
import sys
from cx_Freeze import setup, Executable

includes = ["atexit"] 
include_files = ["convertData.ui"]


# GUI applications require a different base on Windows (the default is for a
# console application).
base = None
if sys.platform == "win32":
    base = "Win32GUI"

buildOptions = dict(
    compressed=True,
    copy_dependent_files=True,
    include_msvcr=True,
    append_script_to_exe=True,
    optimize=2,
    include_files=include_files,
    includes=includes
)

executables = [
    Executable(
        script='main_qt.py',
        targetName='ConvertData.exe',
        base=base
    )
]

setup(
    name="ConvertData",
    version="0.1",
    description="Converts data",
    options=dict(build_exe=buildOptions),
    executables=executables
)