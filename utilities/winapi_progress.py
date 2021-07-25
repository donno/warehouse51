"""Creates a progress dialog using the Windows API."""

# TODO: Add support for having a message (label)
# TODO: Add support for making it cancellable.

import win32api
import win32con
import win32gui
import commctrl

class ProgressDialog:
    """Create a dialog using the Windows API that can be used to show the
    progress of an operation.

    The following sample as used in the implementation of this:
    https://docs.microsoft.com/en-us/windows/win32/controls/create-progress-bar-controls

    Usage
    -----
        progress = ProgressDialog(title='My Application Name')
        progress.set_iterator_count(100)

        for i in range(100):
            # Perform the work here:
            progress.step()

        progress.complete()
    """

    def __init__(self, title):
        self.window_handle = self._create_window(title)
        self.progress = self._create_progress(self.window_handle)

    def set_iterator_count(self, count):
        """Set the iterator count. This dictates how many times self.step()
        will be called. This also resets the progress back to having made no
        progress."""""

        def MAKELPARAM(p, p_2):
            return ((p_2 << 16) | (p & 0xFFFF))

        win32gui.SendMessage(
            self.progress, commctrl.PBM_SETRANGE, 0, MAKELPARAM(0, count))
        win32gui.SendMessage(
            self.progress, commctrl.PBM_SETSTEP, 1, 0)

    def step(self):
        """Step the progress indicator forward."""
        win32gui.SendMessage(self.progress, commctrl.PBM_STEPIT, 0, 0)
        win32gui.PumpWaitingMessages()

    def complete(self):
        """Flag the progress as being complete - closes the dialog."""
        win32gui.DestroyWindow(self.window_handle)
        win32gui.PumpMessages()

    @classmethod
    def _create_window(cls, title):
        def _on_destroy(hwnd, msg, wparam, lparam):
            win32gui.PostQuitMessage(0)
            return True

        def _on_resized(hwnd, msg, wparam, lparam):
            l,t,r,b = win32gui.GetClientRect(hwnd)
            progress = win32gui.FindWindowEx(
                hwnd, None, commctrl.PROGRESS_CLASS, "")
            win32gui.SetWindowPos(progress, None, l, t, r, b, 0)
            return True

        win32gui.InitCommonControls()

        # Set-up the top most window for holding the progress indicator.
        instance = win32api.GetModuleHandle(None)
        className = 'MyWndClass'
        message_map = {
            win32con.WM_DESTROY: _on_destroy,
            win32con.WM_EXITSIZEMOVE: _on_resized,
        }
        wc = win32gui.WNDCLASS()
        wc.style = win32con.CS_HREDRAW | win32con.CS_VREDRAW
        wc.lpfnWndProc = message_map
        wc.lpszClassName = className
        win32gui.RegisterClass(wc)

        main_window = win32gui.CreateWindow(
            className,
            title,
            win32con.WS_OVERLAPPED | win32con.WS_CAPTION |
                win32con.WS_SYSMENU | win32con.WS_THICKFRAME |
                win32con.WS_VISIBLE,
            win32con.CW_USEDEFAULT,
            win32con.CW_USEDEFAULT,
            400,
            100,
            0,
            0,
            instance,
            None
        )

        return main_window

    @classmethod
    def _create_progress(self, window_handle):
        instance = win32api.GetModuleHandle(None)
        l,t,r,b = win32gui.GetClientRect(window_handle)
        progress = win32gui.CreateWindowEx(
            0, commctrl.PROGRESS_CLASS, '',
            win32con.WS_CHILD | win32con.WS_VISIBLE,
            l, t, r, b, window_handle, None, instance, None)
        if not progress:
            raise ValueError('Failed to create progress bar.')

        return progress


if __name__ == '__main__':
    progress = ProgressDialog(title='Example')
    progress.set_iterator_count(100)
    for _ in range(100):
        win32api.Sleep(100)
        progress.step()
    progress.complete()
