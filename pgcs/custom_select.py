import os
import re
from functools import lru_cache, partial
from typing import Any, Dict, List, Tuple

import gcsfs
from prompt_toolkit.application import Application
from prompt_toolkit.clipboard import ClipboardData
from prompt_toolkit.clipboard.pyperclip import PyperclipClipboard
from prompt_toolkit.filters import IsDone
from prompt_toolkit.formatted_text import AnyFormattedText
from prompt_toolkit.formatted_text.utils import to_plain_text
from prompt_toolkit.key_binding import (
    KeyBindings,
    KeyBindingsBase,
    KeyPressEvent,
    merge_key_bindings,
)
from prompt_toolkit.keys import Keys
from prompt_toolkit.layout.containers import (
    ConditionalContainer,
    HSplit,
    VSplit,
    Window,
)
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.layout import Layout
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import TextArea

from pgcs.file_system.base import Entry
from pgcs.file_system.entries import Bucket, Directory, File
from pgcs.preferences import PREF_FILE_PATH, GCSPref
from pgcs.utils import error_handler

pref = GCSPref.read() if PREF_FILE_PATH.exists() else GCSPref()
gfs = gcsfs.GCSFileSystem()

ITEM_CLASS = "class:item"
SELECTED_CLASS = "class:selected"


class CustomFormattedTextControl(FormattedTextControl):
    def __init__(
        self,
        text: AnyFormattedText,
        choices: Dict[str, Entry],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super(CustomFormattedTextControl, self).__init__(
            self._convert_callable_text(text), *args, **kwargs
        )
        self.pointed_at = 0
        self._choices = choices

    @property
    def choice_count(self) -> int:
        return len(self._fragments) if self._fragments is not None else 0

    def _convert_callable_text(self, text: AnyFormattedText) -> AnyFormattedText:
        if callable(text):

            def wrapper() -> List[Tuple[str, Any]]:
                choices = []
                for i, (style, item) in enumerate(text()):
                    if i == self.pointed_at:
                        choices.append((SELECTED_CLASS, item))
                    else:
                        choices.append((style, item))
                return choices

            return wrapper
        return text

    def move_cursor_up(self) -> None:
        self.pointed_at -= 1
        self.pointed_at %= self.choice_count if self.choice_count > 0 else 1

    def move_cursor_down(self) -> None:
        self.pointed_at += 1
        self.pointed_at %= self.choice_count if self.choice_count > 0 else 1

    def get_pointed_at(self) -> AnyFormattedText:
        self.pointed_at = max(0, min(self.pointed_at, self.choice_count - 1))
        return self._fragments[self.pointed_at][1] if self._fragments else None

    def get_key_bindings(self) -> KeyBindingsBase:
        bindings = KeyBindings()

        @bindings.add(Keys.ControlC, eager=True)
        def _(event: KeyPressEvent) -> None:
            event.app.exit(exception=KeyboardInterrupt, style="class:aborting")

        @bindings.add(Keys.Up)
        def _(event: KeyPressEvent) -> None:
            self.move_cursor_up()

        @bindings.add(Keys.Down)
        def _(event: KeyPressEvent) -> None:
            self.move_cursor_down()

        @bindings.add(Keys.Right)
        def _(event: KeyPressEvent) -> None:
            entry = to_plain_text(self.get_pointed_at()).strip()
            if entry:
                event.app.exit(result=entry)

        @bindings.add(Keys.Left)
        def _(event: KeyPressEvent) -> None:
            entry = to_plain_text(self.get_pointed_at()).strip()
            if entry:
                event.app.exit(result="left")

        @bindings.add(Keys.ControlP)
        def _(event: KeyPressEvent) -> None:
            entry_name = to_plain_text(self.get_pointed_at()).strip()
            entry = self._choices[entry_name]
            if entry:
                event.app.clipboard.set_data(ClipboardData(entry.path()))

        @bindings.add(Keys.ControlD)
        def _(event: KeyPressEvent) -> None:
            entry_name = to_plain_text(self.get_pointed_at()).strip()
            entry = self._choices[entry_name]
            if entry:
                gfs.download(
                    entry.path(), ".", recursive=isinstance(entry, (Bucket, Directory))
                )

        @bindings.add(Keys.ControlR)
        def _(event: KeyPressEvent) -> None:
            entry_name = to_plain_text(self.get_pointed_at()).strip()
            entry = self._choices[entry_name]
            if entry and isinstance(entry, (Directory, Bucket)):
                entry.load(force=True)

        @bindings.add(Keys.Enter)
        def _(event: KeyPressEvent) -> None:
            content = self.get_pointed_at()
            event.app.exit(result=content)

        return (
            bindings
            if self.key_bindings is None
            else merge_key_bindings([bindings, self.key_bindings])
        )


def custom_select(
    choices: Dict[str, Entry], max_preview_height: int = 10, **kwargs: Any
) -> str:
    print(choices)
    text_area = TextArea(prompt="QUERY> ", multiline=False)

    def filter_candidates(choices: List[str]) -> List[Tuple[str, str]]:
        input_text = text_area.text
        return [
            (ITEM_CLASS, "".join((item, "\n")))
            for item in choices
            if re.search(input_text, item, flags=re.I if pref.ignore_case else 0)
        ]

    control = CustomFormattedTextControl(
        partial(filter_candidates, choices), choices, focusable=True
    )

    candidates_display = ConditionalContainer(Window(control), ~IsDone())

    def get_entry_info() -> str:
        entry_name = to_plain_text(control.get_pointed_at()).strip()
        entry = choices.get(entry_name)
        if entry is None:
            return ""
        content = ""
        if isinstance(entry, File):
            content = "\n".join(entry.stat())
        elif isinstance(entry, (Directory, Bucket)):
            content = "\n".join(map(os.path.basename, entry.ls()[:10]))
        return content

    preview_control = FormattedTextControl(get_entry_info, focusable=False)
    preview_display = ConditionalContainer(
        Window(
            preview_control,
            height=min(len(choices), max_preview_height),
            wrap_lines=True,
            ignore_content_width=True,
        ),
        ~IsDone(),
    )
    app: Application[AnyFormattedText] = Application(
        layout=Layout(
            HSplit([text_area, VSplit([candidates_display, preview_display])])
        ),
        key_bindings=control.get_key_bindings(),
        style=Style([("item", ""), ("selected", "underline bg:#d980ff #ffffff")]),
        erase_when_done=True,
        clipboard=PyperclipClipboard(),
        mouse_support=True,
        **kwargs,
    )
    return to_plain_text(app.run()).strip()


@error_handler
def traverse_gcs(choices: Dict[str, Entry]) -> File:
    result = custom_select(choices)
    if result == "left":
        entry = list(choices.values())[0]
        if isinstance(entry, Bucket):
            return traverse_gcs(entry.root)  # type: ignore
        elif isinstance(entry, Directory):
            parent = entry.parent
            if isinstance(parent, Bucket):
                return traverse_gcs(parent.root)  # type: ignore
            return traverse_gcs(parent.parent.children)  # type: ignore
        elif isinstance(entry, File):
            return traverse_gcs(entry.parent.parent.children)  # type: ignore
        else:
            raise NotImplementedError

    entry = choices[result]
    if isinstance(entry, File):
        return entry
    elif isinstance(entry, (Directory, Bucket)):
        entry.load()
    return traverse_gcs(entry.children)  # type: ignore
