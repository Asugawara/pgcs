import os
import re
from functools import partial
from typing import Any, List, Tuple

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

from pgcs.preferences import PREF_FILE_PATH, GCSPref
from pgcs.utils import error_handler

pref = GCSPref.parse_file(PREF_FILE_PATH) if PREF_FILE_PATH.exists() else GCSPref()
gfs = gcsfs.GCSFileSystem(os.getenv("PROJECT_ID", pref.default_project_id))

ITEM_CLASS = "class:item"
SELECTED_CLASS = "class:selected"


class CustomFormattedTextControl(FormattedTextControl):
    def __init__(self, text: AnyFormattedText, *args: Any, **kwargs: Any) -> None:
        super(CustomFormattedTextControl, self).__init__(
            self._convert_callable_text(text), *args, **kwargs
        )
        self.pointed_at = 0

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
                event.app.exit(result=os.path.dirname(os.path.dirname(entry)))

        @bindings.add(Keys.ControlP)
        def _(event: KeyPressEvent) -> None:
            entry = to_plain_text(self.get_pointed_at()).strip()
            if entry:
                event.app.clipboard.set_data(ClipboardData(f"gs://{entry}"))

        @bindings.add(Keys.ControlD)
        def _(event: KeyPressEvent) -> None:
            entry = to_plain_text(self.get_pointed_at()).strip()
            if entry and gfs.exists(entry):
                gfs.download(entry, ".", recursive=gfs.isdir(entry))

        @bindings.add(Keys.Enter)
        def _(event: KeyPressEvent) -> None:
            content = self.get_pointed_at()
            event.app.exit(result=content)

        return (
            bindings
            if self.key_bindings is None
            else merge_key_bindings([bindings, self.key_bindings])
        )


@error_handler
def custom_select(
    choices: List[str], max_preview_height: int = 10, **kwargs: Any
) -> str:
    text_area = TextArea(prompt="QUERY> ", multiline=False)

    def filter_candidates(choices: List[str]) -> List[Tuple[str, str]]:
        input_text = text_area.text
        return [
            (ITEM_CLASS, "".join((item, "\n")))
            for item in choices
            if re.search(input_text, item, flags=re.I if pref.ignore_case else 0)
        ]

    control = CustomFormattedTextControl(
        partial(filter_candidates, choices), focusable=True
    )

    candidates_display = ConditionalContainer(Window(control), ~IsDone())

    def get_entry_info() -> str:
        entry = to_plain_text(control.get_pointed_at()).strip()
        if not entry:
            return ""
        if gfs.isfile(entry):
            content: str = gfs.read_block(entry, 0, 50, delimiter=b"\n").decode("utf-8")
            file_stats = gfs.stat(entry)
            file_createdat = f"created_at: {file_stats['timeCreated']}"
            file_updatedat = f"updated_at: {file_stats['updated']}"
            content = "\n".join((file_createdat, file_updatedat, content))
        else:
            content = "\n".join(map(os.path.basename, gfs.ls(entry)[:10]))
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


def traverse_gcs(choices: List[str]) -> str:
    entry: str = custom_select(choices)
    if not entry:
        return traverse_gcs(gfs.buckets)
    if gfs.isfile(entry):
        return entry
    return traverse_gcs(gfs.ls(entry))
