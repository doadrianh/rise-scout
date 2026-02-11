from rise_scout.domain.contact.models import Contact, Preferences, ScoreReason
from rise_scout.domain.shared.events import ContactScored
from rise_scout.domain.shared.types import AgentId, ContactId


def _make_contact(**kwargs):
    defaults = {
        "contact_id": ContactId("c-1"),
        "user_ids": [AgentId("a-1")],
        "first_name": "Jane",
        "last_name": "Doe",
    }
    defaults.update(kwargs)
    return Contact(**defaults)


def _make_reason(signal="listing_view", points=3.0):
    return ScoreReason(signal=signal, points=points, category="engagement", detail="test")


class TestContactModel:
    def test_apply_score_delta_adds_points(self):
        contact = _make_contact()
        reason = _make_reason(points=10.0)
        contact.apply_score_delta(10.0, reason)

        assert contact.score == 10.0
        assert len(contact.score_reasons) == 1
        assert contact.score_reasons[0].signal == "listing_view"

    def test_apply_score_delta_floor_at_zero(self):
        contact = _make_contact(score=5.0)
        reason = _make_reason(points=-10.0)
        contact.apply_score_delta(-10.0, reason)

        assert contact.score == 0.0

    def test_apply_decay(self):
        contact = _make_contact(score=100.0)
        contact.apply_decay(0.95)

        assert contact.score == 95.0

    def test_apply_decay_floor_at_zero(self):
        contact = _make_contact(score=0.0)
        contact.apply_decay(0.95)

        assert contact.score == 0.0

    def test_trim_reasons_caps_at_max(self):
        reasons = [_make_reason(points=float(i)) for i in range(60)]
        contact = _make_contact(score_reasons=reasons)
        contact.trim_reasons(max_reasons=50)

        assert len(contact.score_reasons) == 50
        assert contact.score_reasons[0].points == 0.0  # First reason kept

    def test_multiple_deltas_accumulate(self):
        contact = _make_contact()
        for _i in range(5):
            reason = _make_reason(points=10.0)
            contact.apply_score_delta(10.0, reason)

        assert contact.score == 50.0
        assert len(contact.score_reasons) == 5

    def test_apply_score_delta_emits_contact_scored_event(self):
        contact = _make_contact(user_ids=[AgentId("a-1"), AgentId("a-2")])
        reason = _make_reason(points=5.0)
        contact.apply_score_delta(5.0, reason)

        events = contact.collect_events()
        assert len(events) == 1
        assert isinstance(events[0], ContactScored)
        assert events[0].contact_id == contact.contact_id
        assert set(events[0].agent_ids) == {AgentId("a-1"), AgentId("a-2")}

    def test_collect_events_clears_pending(self):
        contact = _make_contact()
        contact.apply_score_delta(5.0, _make_reason())
        contact.apply_score_delta(3.0, _make_reason())

        events = contact.collect_events()
        assert len(events) == 2

        assert contact.collect_events() == []

    def test_apply_decay_does_not_emit_event(self):
        contact = _make_contact(score=100.0)
        contact.apply_decay(0.95)

        assert contact.collect_events() == []

    def test_display_name(self):
        contact = _make_contact(first_name="Jane", last_name="Doe")
        assert contact.display_name == "Jane Doe"

    def test_display_name_first_only(self):
        contact = _make_contact(first_name="Jane", last_name="")
        assert contact.display_name == "Jane"

    def test_display_name_empty(self):
        contact = _make_contact(first_name="", last_name="")
        assert contact.display_name == ""

    def test_to_embedding_text(self):
        contact = _make_contact(
            first_name="Jane",
            last_name="Doe",
            preferences=Preferences(
                keywords=["pool", "garage"],
                cities=["Seattle"],
                zip_codes=["98101"],
            ),
        )
        text = contact.to_embedding_text()
        assert "Jane" in text
        assert "Doe" in text
        assert "pool garage" in text
        assert "Seattle" in text
        assert "98101" in text

    def test_to_embedding_text_empty_contact(self):
        contact = _make_contact(first_name="", last_name="")
        text = contact.to_embedding_text()
        assert text == ""

    def test_top_score_details(self):
        reasons = [
            ScoreReason(signal="a", points=1.0, category="c", detail="first"),
            ScoreReason(signal="b", points=2.0, category="c", detail="second"),
            ScoreReason(signal="c", points=3.0, category="c", detail="third"),
            ScoreReason(signal="d", points=4.0, category="c", detail="fourth"),
        ]
        contact = _make_contact(score_reasons=reasons)
        assert contact.top_score_details(limit=3) == ["first", "second", "third"]

    def test_top_score_details_fewer_than_limit(self):
        reasons = [ScoreReason(signal="a", points=1.0, category="c", detail="only")]
        contact = _make_contact(score_reasons=reasons)
        assert contact.top_score_details(limit=3) == ["only"]


class TestPreferences:
    def test_is_complete_when_all_required_set(self):
        prefs = Preferences(
            price_min=200000,
            price_max=500000,
            zip_codes=["90210"],
        )
        assert prefs.is_complete is True

    def test_is_incomplete_without_price(self):
        prefs = Preferences(zip_codes=["90210"])
        assert prefs.is_complete is False

    def test_is_incomplete_without_location(self):
        prefs = Preferences(price_min=200000, price_max=500000)
        assert prefs.is_complete is False

    def test_is_complete_with_cities(self):
        prefs = Preferences(
            price_min=200000,
            price_max=500000,
            cities=["Seattle"],
        )
        assert prefs.is_complete is True

    def test_empty_preferences_is_incomplete(self):
        prefs = Preferences()
        assert prefs.is_complete is False
