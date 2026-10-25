"""GUI smoke test: runs on Windows desktop or Linux with Xvfb; skips headless CI."""
import unittest

try:
    import tkinter as tk
    from installer.gui import Window
except (ImportError, ModuleNotFoundError):
    tk = None
    Window = None


@unittest.skipIf(tk is None, 'Tkinter not available on this Python installation')
class GuiSmokeTest(unittest.TestCase):
    def test_window_and_navigation(self):
        try:
            root = tk.Tk()
        except tk.TclError:
            self.skipTest('Graphical display unavailable')
        try:
            app = Window(root)
            root.update()
            self.assertEqual(app.page, 0)
            app.show_location()
            root.update()
            self.assertEqual(app.page, 1)
            app.show_intro()
            root.update()
            self.assertEqual(app.page, 0)
        finally:
            root.destroy()


if __name__ == '__main__':
    unittest.main()
