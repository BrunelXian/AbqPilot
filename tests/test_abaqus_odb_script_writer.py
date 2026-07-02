from abqpilot.odb.abaqus_odb_script_writer import build_odb_metrics_script, write_odb_metrics_script


def test_generated_odb_script_contains_open_odb(tmp_path):
    script_path = tmp_path / "extract.py"
    write_odb_metrics_script(script_path, tmp_path / "contract.json", tmp_path / "metrics.json")
    assert "open" + "Odb" in script_path.read_text(encoding="utf-8")


def test_generated_odb_script_does_not_contain_solver_submit(tmp_path):
    script = build_odb_metrics_script(tmp_path / "contract.json", tmp_path / "metrics.json")
    assert "sub" + "mit(" not in script


def test_generated_odb_script_does_not_contain_wait_for_completion(tmp_path):
    script = build_odb_metrics_script(tmp_path / "contract.json", tmp_path / "metrics.json")
    assert "wait" + "ForCompletion" not in script


def test_generated_odb_script_does_not_contain_write_input(tmp_path):
    script = build_odb_metrics_script(tmp_path / "contract.json", tmp_path / "metrics.json")
    assert "write" + "Input" not in script


def test_script_generation_does_not_execute_odb_access(tmp_path):
    script = build_odb_metrics_script(tmp_path / "contract.json", tmp_path / "metrics.json")
    assert "from odbAccess import " + "open" + "Odb" in script
    assert (tmp_path / "metrics.json").exists() is False
