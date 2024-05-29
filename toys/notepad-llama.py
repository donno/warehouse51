"""Very rushed demonstration of Notepad and LLaMA-2-7b-chat.

This is by no means sophisticated, it does not inject itself into the Notepad
process or snoop the key-pressed in Notepad. The approach it taken is:
- Fnd the window handle for an untitled Notepad window
- Finds the edit control - it expects it to be the child of the window
- Queries the text of the control using WM_GETTEXT
- Parses the result for !prompt <prompt-here>!!.
- Queries the locally running llama.cpp server's completion API end-point with
  the given prompt.
- Replaces the prompt line with the result.

llama.cpp was run using:
- server.exe -m models\llama-2-7b-chat-q5_k_m.gguf

Minor improvements to make:
- While waiting for the response back from the prompt, replace the prompt line
  with .....
Fancier improvements to make:
- Track where the cursor is and reapply it after the change.
Known issues:
- Making more changes to the document while it is running the query is not a
  good idea as it will replace it with the text it had last time.
"""
import ctypes
import ctypes.wintypes
import time

import requests

WNDENUMPROC = ctypes.WINFUNCTYPE(
    ctypes.wintypes.BOOL,
    ctypes.wintypes.HWND,
    ctypes.wintypes.LPARAM,
)


def window_name(hwnd: ctypes.wintypes.HWND) -> str:
    length = ctypes.windll.user32.GetWindowTextLengthW(hwnd) + 1
    buffer = ctypes.create_unicode_buffer(length)
    ctypes.windll.user32.GetWindowTextW(hwnd, buffer, length)
    return buffer.value


def open_windows() -> list[ctypes.wintypes.HWND]:
    windows = []

    def on_window(hwnd, parameter):
        name = window_name(hwnd)
        windows.append((hwnd, name))
        return True

    window_callback = WNDENUMPROC(on_window)
    if not ctypes.windll.user32.EnumWindows(window_callback, 51):
        raise ctypes.WinError()
    return windows


def find_new_notepad():
    # This could instead launch notepad.
    notepad = next(
        hwnd for hwnd, name in open_windows() if name.endswith("Untitled - Notepad")
    )
    return notepad


def find_edit(window_handle: ctypes.wintypes.HWND):
    # For notepad in Windows 10, the next window from the "notepad window" is
    # the Edit control.
    GW_CHILD = 5
    return ctypes.windll.user32.GetWindow(window_handle, GW_CHILD)


def read_edit(edit_handle: ctypes.wintypes.HWND):
    """Copy the text of the corresponding handle into a buffer provided by us."""
    WM_GETTEXT = 0x000D
    WM_GETTEXTLENGTH = 0x000E
    length = ctypes.windll.user32.SendMessageW(
        edit_handle,
        WM_GETTEXTLENGTH,
        0,
        0,
    )
    buffer = ctypes.create_unicode_buffer(length + 1)
    ctypes.windll.user32.SendMessageW(
        edit_handle,
        WM_GETTEXT,
        length + 1,
        buffer,
    )
    return buffer.value


def set_text(control: ctypes.wintypes.HWND, text: str):
    """Sets the text of a window including control such as edit control."""
    WM_SETTEXT = 0x000C
    ctypes.windll.user32.SendMessageW(
        control,
        WM_SETTEXT,
        len(text),
        text,
    )


class Watcher:
    """Watch for changes to an untitled Notepad document."""

    def __init__(self):
        self.notepad = find_new_notepad()
        self.edit_control = find_edit(self.notepad)
        self.commands = []

    @property
    def contents(self) -> str:
        return read_edit(self.edit_control)

    def watch_for(self, start: str, end: str, callback):
        """Watch for line with the given start and end.

        If the line occurs the callback is called with contents  between start
        and end.

        This is only relevant for check_for_changes().
        """
        self.commands.append((start, end, callback))

    def check_for_changes(self):
        """Check the contents of the edit control for changes.

        This can be used to poll for changes.
        """
        contents = self.contents
        new_contents = ""
        for line in contents.splitlines():
            for start, end, callback in self.commands:
                if line.startswith(start) and line.endswith(end):
                    window_title = read_edit(self.notepad)
                    set_text(
                        self.notepad,
                        f"(Querying LLaMA) {window_title}",
                    )
                    new_contents += callback(line[len(start) : -len(end)])
                    set_text(self.notepad, window_title)
                    break
            else:
                new_contents += line + "\n"

        if not contents.endswith("\n"):
            new_contents = new_contents[:-1]
        if new_contents != contents:
            set_text(self.edit_control, new_contents)


def handle_prompt(prompt: str):
    """Query llama-cpp's server running on localhost with the given prompt."""
    response = requests.post(
        "http://localhost:8080/completion",
        headers={
            "Content-Type": "application/json",
        },
        json={
            "prompt": prompt,
            "n_predict": 128,
        },
    )
    response.raise_for_status()
    suggestion = response.json()["content"]
    return suggestion


def watch_for_prompt():
    """Watch a notepad window from the prompt then inject the result."""
    watcher = Watcher()
    watcher.watch_for("!prompt ", "!!", handle_prompt)
    while True:
        watcher.check_for_changes()
        time.sleep(2.0)


if __name__ == "__main__":
    watch_for_prompt()
    # print(handle_prompt("Write a poem about a dog"))
