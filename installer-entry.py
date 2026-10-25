"""PyInstaller --windowed entrypoint. Never loads a remote script."""
from installer.gui import main

if __name__ == '__main__':
    main()
