import PyInstaller.__main__
import shutil

PyInstaller.__main__.run([
    'src/main.py',
    '--onefile',
    '--clean',
    '--windowed',
    '--name=Proper Job',
    '--icon=src/resources/logo.png',
    '--collect-all=numpy'
])

# Move resources to dist folder
shutil.copytree('src/resources', 'dist/resources', dirs_exist_ok=True)

