env\scripts\python.exe -m `
    nuitka drawing_pack_gui.py `
    --python-flag=no_docstrings `
    --include-data-file=.\veolia_logo_sm.png=.\ `
    --include-data-file=.\veolia_logo.ico=.\ `
    --include-data-file=.\pdfgen11x17model.scr=.\ `
    --plugin-enable=pyside6 `
    --plugin-enable=pylint-warnings `
    --onefile `
    --windows-disable-console `
    --windows-icon-from-ico=.\veolia_logo.ico `
    --remove-output `
    --output-dir=dist