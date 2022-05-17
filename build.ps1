.venv\scripts\python.exe -m `
    nuitka drawing_pack.py `
    --python-flag=no_docstrings `
    --include-data-file=.\src\veolia_logo_sm.png=.\src\ `
    --include-data-file=.\src\veolia_logo.ico=.\src\ `
    --include-data-file=.\src\pdfgen11x17model.scr=.\src\ `
    --include-data-file=.\src\pdfgen11x17layout.scr=.\src\ `
    --plugin-enable=pyside6 `
    --plugin-enable=pylint-warnings `
    --onefile `
    --windows-disable-console `
    --windows-icon-from-ico=.\src\veolia_logo.ico `
    --remove-output `
    --output-dir=dist
