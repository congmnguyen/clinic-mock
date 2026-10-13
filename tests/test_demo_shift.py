"""Demo deployments only: fixtures written for one week follow the calendar (store.demo_shift)."""

from datetime import date, timedelta

import pytest

from clinic_mock import store


@pytest.fixture()
def anchored(monkeypatch):
    monkeypatch.setattr(store, "DEMO_ANCHOR", "2026-10-12")  # a Monday
    yield
    monkeypatch.undo()
    store.seed_default()


@pytest.mark.usefixtures("anchored")
@pytest.mark.parametrize(
    ("today", "days"),
    [
        ("2026-10-01", 0),  # before the anchor: as written
        ("2026-10-12", 0),
        ("2026-10-18", 0),  # the same week, up to its Sunday
        ("2026-10-19", 7),  # the next Monday: one week on
        ("2026-10-28", 14),
    ],
)
def test_fixtures_move_by_whole_weeks_from_the_anchor(today, days):
    assert store.demo_shift(date.fromisoformat(today)) == timedelta(days=days)


def test_without_an_anchor_nothing_moves(monkeypatch):
    monkeypatch.setattr(store, "DEMO_ANCHOR", None)
    assert store.demo_shift(date(2027, 1, 1)) == timedelta(0)
    store.seed_default()
    assert store.db.appointments["apt_00417"].starts_at == "2026-10-14T15:30:00+07:00"


@pytest.mark.usefixtures("anchored")
def test_a_seed_in_a_later_week_moves_slots_and_appointments(monkeypatch):
    monkeypatch.setenv("MOCK_DEMO_TODAY", "2026-10-21")
    store.seed_default()
    appointment = store.db.appointments["apt_00417"]
    assert appointment.starts_at == "2026-10-21T15:30:00+07:00"
    assert appointment.ends_at == "2026-10-21T16:00:00+07:00"
    slot = store.db.slots["slot_91d2"]
    assert (slot.start_time, slot.end_time) == (
        "2026-10-21T15:00:00+07:00",
        "2026-10-21T15:30:00+07:00",
    )
    # Per-tenant fixtures are left as they are.
    assert any(s.start_time == "2026-09-15T09:00:00Z" for s in store.db.slots.values())


@pytest.mark.usefixtures("anchored")
def test_a_reset_moves_them_from_the_written_times_not_again(monkeypatch, client):
    monkeypatch.setenv("MOCK_DEMO_TODAY", "2026-10-21")
    headers = {"Authorization": "Bearer sk_test_a"}
    for _ in range(2):
        assert client.post("/_harness/reset", headers=headers).status_code == 200
    assert store.db.appointments["apt_00417"].starts_at == "2026-10-21T15:30:00+07:00"
