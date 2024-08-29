# .venv\scripts\python.exe -m `
#     nuitka drawing_pack.py `
#     --python-flag=no_docstrings `
#     --include-data-file=.\src\veolia_logo_sm.png=.\src\ `
#     --include-data-file=.\src\veolia_logo.ico=.\src\ `
#     --include-data-file=.\src\pdfgen11x17model.scr=.\src\ `
#     --include-data-file=.\src\pdfgen11x17layout.scr=.\src\ `
#     --plugin-enable=pyside6 `
#     --plugin-enable=pylint-warnings `
#     --onefile `
#     --windows-disable-console `
#     --windows-icon-from-ico=.\src\veolia_logo.ico `
#     --remove-output `
#     --output-dir=dist

.venv\scripts\python.exe -m `
    PyInstaller drawing_pack.py `
    --add-data ".\src\veolia_logo_sm.png;src\" `
    --add-data ".\src\veolia_logo.ico;src\" `
    --add-data ".\src\pdfgen11x17model.scr;src\" `
    --add-data ".\src\pdfgen11x17layout.scr;src\" `
    --icon src\veolia_logo.ico `
    --noconfirm `
    --upx-dir "C:\UPX\upx-3.96-win64"