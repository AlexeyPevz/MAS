from pathlib import Path

from tools.prompt_io import write_prompt, read_prompt


def test_write_and_read_prompt(tmp_path):
    file_path = tmp_path / "prompts" / "test.md"
    write_prompt(file_path, ["hello"])
    assert file_path.exists()
    assert read_prompt(file_path) == "hello\n"
