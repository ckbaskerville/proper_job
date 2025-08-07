import PyInstaller.__main__

PyInstaller.__main__.run([
    'src/main.py',
    '--onefile',
    '--windowed',
    '--name=Proper Job',
    '--icon=src/resources/logo.png',
    '--add-data=src/resources;resources',
    '--collect-all=numpy'
])

