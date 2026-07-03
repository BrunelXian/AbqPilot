from pathlib import Path

from abqpilot.diagnostics.job_log_parser import parse_job_logs


def test_parser_detects_completion_and_failure_flags(tmp_path):
    sta = tmp_path / "job.sta"
    msg = tmp_path / "job.msg"
    sta.write_text("THE ANALYSIS HAS NOT BEEN COMPLETED\n", encoding="utf-8")
    msg.write_text("***ERROR: TOO MANY ATTEMPTS MADE FOR THIS INCREMENT\n", encoding="utf-8")

    parsed = parse_job_logs({"sta": sta, "msg": msg, "dat": Path("missing.dat"), "log": Path("missing.log")})

    assert parsed["flags"]["analysis_not_completed"] is True
    assert parsed["flags"]["too_many_attempts"] is True
    assert parsed["flags"]["terminal_failure"] is True
    assert parsed["flags"]["convergence_failure"] is True
    assert parsed["important_lines"]["msg_error_lines"]

