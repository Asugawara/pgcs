from unittest.mock import patch

import pytest
from prompt_toolkit.input.ansi_escape_sequences import REVERSE_ANSI_SEQUENCES
from prompt_toolkit.input.defaults import create_pipe_input
from prompt_toolkit.keys import Keys
from prompt_toolkit.output import DummyOutput

from pgcs.custom_select import custom_select


@patch("pgcs.custom_select.gfs")
def test_custom_select(mock_gfs):
    mock_gfs.isfile.return_value = False
    mock_gfs.ls.return_value = []
    with create_pipe_input() as pipe_input:
        pipe_input.send_text(REVERSE_ANSI_SEQUENCES[Keys.Enter])
        selected = custom_select([], input=pipe_input, output=DummyOutput())
        assert selected == ""

        pipe_input.send_text(REVERSE_ANSI_SEQUENCES[Keys.Enter])
        selected = custom_select(
            ["a", "b", "c"], input=pipe_input, output=DummyOutput()
        )
        assert selected == "a"

        pipe_input.send_text(REVERSE_ANSI_SEQUENCES[Keys.Enter])
        with pytest.raises(TypeError) as e:
            selected = custom_select([1, 2, 3], input=pipe_input, output=DummyOutput())


@patch("pgcs.custom_select.gfs")
def test_custom_select_move_cursor(mock_gfs):
    mock_gfs.isfile.return_value = False
    mock_gfs.ls.return_value = []
    with create_pipe_input() as pipe_input:
        pipe_input.send_text(REVERSE_ANSI_SEQUENCES[Keys.Enter])
        selected = custom_select(
            ["a", "b", "c"], input=pipe_input, output=DummyOutput()
        )
        assert selected == "a"

        pipe_input.send_text(
            "".join(
                (REVERSE_ANSI_SEQUENCES[Keys.Down], REVERSE_ANSI_SEQUENCES[Keys.Enter])
            )
        )
        selected = custom_select(
            ["a", "b", "c"], input=pipe_input, output=DummyOutput()
        )
        assert selected == "b"

        pipe_input.send_text(
            "".join(
                (
                    REVERSE_ANSI_SEQUENCES[Keys.Down] * 2,
                    REVERSE_ANSI_SEQUENCES[Keys.Enter],
                )
            )
        )
        selected = custom_select(
            ["a", "b", "c"], input=pipe_input, output=DummyOutput()
        )
        assert selected == "c"

        pipe_input.send_text(
            "".join(
                (
                    REVERSE_ANSI_SEQUENCES[Keys.Down] * 3,
                    REVERSE_ANSI_SEQUENCES[Keys.Enter],
                )
            )
        )
        selected = custom_select(
            ["a", "b", "c"], input=pipe_input, output=DummyOutput()
        )
        assert selected == "a"

        pipe_input.send_text(
            "".join(
                (REVERSE_ANSI_SEQUENCES[Keys.Up], REVERSE_ANSI_SEQUENCES[Keys.Enter])
            )
        )
        selected = custom_select(
            ["a", "b", "c"], input=pipe_input, output=DummyOutput()
        )
        assert selected == "c"

        pipe_input.send_text(
            "".join(
                (
                    REVERSE_ANSI_SEQUENCES[Keys.Up] * 2,
                    REVERSE_ANSI_SEQUENCES[Keys.Enter],
                )
            )
        )
        selected = custom_select(
            ["a", "b", "c"], input=pipe_input, output=DummyOutput()
        )
        assert selected == "b"

        pipe_input.send_text(
            "".join(
                (
                    REVERSE_ANSI_SEQUENCES[Keys.Up] * 3,
                    REVERSE_ANSI_SEQUENCES[Keys.Enter],
                )
            )
        )
        selected = custom_select(
            ["a", "b", "c"], input=pipe_input, output=DummyOutput()
        )
        assert selected == "a"


@patch("pgcs.custom_select.gfs")
def test_custom_select_using_filter(mock_gfs):
    mock_gfs.isfile.return_value = False
    mock_gfs.ls.return_value = []
    with create_pipe_input() as pipe_input, patch(
        "prompt_toolkit.widgets.TextArea.text", "a"
    ):
        pipe_input.send_text("".join((REVERSE_ANSI_SEQUENCES[Keys.Enter])))
        selected = custom_select(
            ["a", "b", "c", "aa"], input=pipe_input, output=DummyOutput()
        )
        assert selected == "a"

        pipe_input.send_text(
            "".join(
                (REVERSE_ANSI_SEQUENCES[Keys.Down], REVERSE_ANSI_SEQUENCES[Keys.Enter])
            )
        )
        selected = custom_select(
            ["a", "b", "c", "aa"], input=pipe_input, output=DummyOutput()
        )
        assert selected == "aa"

    # no hit
    with create_pipe_input() as pipe_input, patch(
        "prompt_toolkit.widgets.TextArea.text", "z"
    ):
        pipe_input.send_text("".join((REVERSE_ANSI_SEQUENCES[Keys.Enter])))
        selected = custom_select(
            ["a", "b", "c", "aa"], input=pipe_input, output=DummyOutput()
        )
        assert selected == ""

        pipe_input.send_text(
            "".join(
                (REVERSE_ANSI_SEQUENCES[Keys.Down], REVERSE_ANSI_SEQUENCES[Keys.Enter])
            )
        )
        selected = custom_select(
            ["a", "b", "c", "aa"], input=pipe_input, output=DummyOutput()
        )
        assert selected == ""
