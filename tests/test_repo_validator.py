from tools import repo_validator as rv


def test_validate_repo_success(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    (repo / "README.md").write_text("hi\n")
    (repo / "compose.yml").write_text("version: '3'\n")
    assert rv.validate_repository(repo)


def test_validate_repo_missing_files(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / ".git").mkdir()
    assert not rv.validate_repository(repo)
