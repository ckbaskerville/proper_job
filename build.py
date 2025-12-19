import PyInstaller.__main__
import shutil
import os

PyInstaller.__main__.run([
    'src/main.py',
    '--onefile',
    '--clean',
    '--noconsole',
    '--noconfirm',
    '--windowed',
    '--name=Proper Job',
    '--icon=src/resources/logo.png',
    '--collect-all=numpy'
])

if os.path.exists('dist/resources'):
    # Move resources to dist folder
    shutil.copytree('src/resources', 'dist/resources')

