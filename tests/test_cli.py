import json
from click.testing import CliRunner
from regsolver_cli.cli import main

def test_parse_creates_json(tmp_path):
    runner = CliRunner()
    sample = tmp_path / "sample.txt"
    sample.write_text("line1\nline2\nline3\n")
    result = runner.invoke(main, ["parse", str(sample), "--format", "json", "--show"])
    assert result.exit_code == 0
    out = sample.with_suffix(".parsed.json")
    data = json.loads(out.read_text())
    assert data["lines"] == 3
    assert "size_bytes" in data
