import pytest

from rise_scout.domain.scoring.signals import SignalType
from rise_scout.domain.search.models import ListingEventType
from rise_scout.infrastructure.kafka.parsers import (
    ContactChangeParser,
    InteractionParser,
    ListingParser,
)


class TestContactChangeParser:
    def test_parse_create_event(self):
        parser = ContactChangeParser()
        payload = {
            "contact_id": "c-1",
            "event_type": "create",
            "user_ids": ["a-1", "a-2"],
            "organisationalunit_id": "org-1",
            "mls_ids": ["mls-1"],
            "first_name": "Jane",
            "last_name": "Doe",
            "email": "jane@example.com",
            "phone": "555-1234",
            "preferences": {
                "price_min": 200000,
                "price_max": 500000,
                "zip_codes": ["90210"],
            },
            "watched_listings": ["l-1"],
        }

        contact, is_new = parser.parse(payload)

        assert is_new is True
        assert str(contact.contact_id) == "c-1"
        assert len(contact.user_ids) == 2
        assert contact.first_name == "Jane"
        assert contact.email == "jane@example.com"
        assert contact.preferences.price_min == 200000
        assert contact.preferences.zip_codes == ["90210"]
        assert len(contact.watched_listings) == 1

    def test_parse_update_event(self):
        parser = ContactChangeParser()
        payload = {
            "contact_id": "c-1",
            "event_type": "update",
            "user_ids": ["a-1"],
            "first_name": "Jane",
            "last_name": "Smith",
        }

        contact, is_new = parser.parse(payload)

        assert is_new is False
        assert contact.last_name == "Smith"

    def test_parse_minimal_payload(self):
        parser = ContactChangeParser()
        payload = {"contact_id": "c-1"}

        contact, is_new = parser.parse(payload)

        assert str(contact.contact_id) == "c-1"
        assert is_new is False
        assert contact.first_name == ""


class TestInteractionParser:
    def test_parse_listing_view(self):
        parser = InteractionParser()
        payload = {
            "contact_id": "c-1",
            "interaction_type": "listing_view",
            "detail": "Viewed listing l-123",
        }

        contact_id, signal, detail = parser.parse(payload)

        assert str(contact_id) == "c-1"
        assert signal == SignalType.LISTING_VIEW
        assert detail == "Viewed listing l-123"

    def test_parse_all_interaction_types(self):
        parser = InteractionParser()
        for raw_type, expected_signal in InteractionParser.SIGNAL_MAP.items():
            payload = {
                "contact_id": "c-1",
                "interaction_type": raw_type,
            }
            _, signal, _ = parser.parse(payload)
            assert signal == expected_signal

    def test_parse_unknown_type_raises(self):
        parser = InteractionParser()
        payload = {
            "contact_id": "c-1",
            "interaction_type": "unknown_type",
        }

        with pytest.raises(ValueError, match="Unknown interaction type"):
            parser.parse(payload)


class TestListingParser:
    def test_parse_new_listing(self):
        parser = ListingParser()
        payload = {
            "listing_id": "l-1",
            "event_type": "new",
            "mls_id": "mls-1",
            "price": 450000,
            "beds": 3,
            "baths": 2,
            "sqft": 1800,
            "property_type": "single_family",
            "zip_code": "90210",
            "city": "Beverly Hills",
        }

        event = parser.parse(payload)

        assert str(event.listing_id) == "l-1"
        assert event.event_type == ListingEventType.NEW_LISTING
        assert event.price == 450000
        assert event.beds == 3
        assert event.zip_code == "90210"

    def test_parse_price_change(self):
        parser = ListingParser()
        payload = {
            "listing_id": "l-1",
            "event_type": "price_change",
            "mls_id": "mls-1",
            "price": 400000,
            "previous_price": 450000,
        }

        event = parser.parse(payload)

        assert event.event_type == ListingEventType.PRICE_CHANGE
        assert event.previous_price == 450000

    def test_parse_all_event_types(self):
        parser = ListingParser()
        for raw_type, expected_type in ListingParser.EVENT_TYPE_MAP.items():
            payload = {
                "listing_id": "l-1",
                "event_type": raw_type,
                "mls_id": "mls-1",
            }
            event = parser.parse(payload)
            assert event.event_type == expected_type

    def test_parse_unknown_event_type_raises(self):
        parser = ListingParser()
        payload = {
            "listing_id": "l-1",
            "event_type": "demolished",
            "mls_id": "mls-1",
        }

        with pytest.raises(ValueError, match="Unknown listing event type"):
            parser.parse(payload)
