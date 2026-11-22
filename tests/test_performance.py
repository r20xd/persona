"""Guard measurement against apparently successful login pages and unsafe interpretation."""

import pytest

from scripts.verify_performance import summary, validate_read


def test_percentiles_use_nearest_rank_and_count_every_observation():
    result = summary(list(range(1, 21)))
    assert result == {"count": 20, "p50_ms": 10, "p95_ms": 19, "max_ms": 20}
    with pytest.raises(ValueError):
        summary([])


@pytest.mark.parametrize(
    "code,url,body",
    [
        (200, "http://127.0.0.1/login/", "Expected"),
        (200, "http://127.0.0.1/grades/", 'Expected <input name="password">'),
        (200, "http://127.0.0.1/grades/", "Wrong section"),
        (500, "http://127.0.0.1/grades/", "Expected"),
    ],
)
def test_false_login_success_or_wrong_response_is_functional_failure(code, url, body):
    with pytest.raises(RuntimeError, match="Invalid authenticated response"):
        validate_read(code, url, "http://127.0.0.1/grades/", body, "Expected")


def test_runner_failure_is_nonzero_redacted_and_cleanup_attempted(monkeypatch, capsys):
    from scripts import verify_performance

    class FailingRehearsal:
        result = {}
        phase = "test"
        container_created = True
        web = None

        def __init__(self, docker, rounds):
            pass

        def execute(self):
            raise RuntimeError("private-cookie-and-password")

        def cleanup(self):
            self.container_created = False

    monkeypatch.setattr(verify_performance, "Performance", FailingRehearsal)
    monkeypatch.setattr("sys.argv", ["verify_performance"])
    assert verify_performance.main() == 1
    output = capsys.readouterr().out
    assert "private-cookie-and-password" not in output
    assert '"cleanup_complete": true' in output
    assert '"functional_failure": true' in output
