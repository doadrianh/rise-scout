import fakeredis
import pytest

from rise_scout.domain.shared.types import AgentId
from rise_scout.infrastructure.redis.debouncer import EventDebouncer
from rise_scout.infrastructure.redis.refresh_flags import RefreshFlagStore


@pytest.fixture
def redis_client():
    return fakeredis.FakeRedis()


@pytest.mark.integration
class TestRefreshFlagStore:
    def test_flag_and_pop_agents(self, redis_client):
        store = RefreshFlagStore(redis_client)

        store.flag_agents([AgentId("a-1"), AgentId("a-2")])
        store.flag_agents([AgentId("a-2"), AgentId("a-3")])

        popped = store.pop_flagged_agents()
        agent_strs = {str(a) for a in popped}

        assert agent_strs == {"a-1", "a-2", "a-3"}  # SET deduplicates a-2

    def test_pop_empty_returns_empty(self, redis_client):
        store = RefreshFlagStore(redis_client)
        assert store.pop_flagged_agents() == []

    def test_pop_clears_flags(self, redis_client):
        store = RefreshFlagStore(redis_client)
        store.flag_agents([AgentId("a-1")])

        store.pop_flagged_agents()
        second_pop = store.pop_flagged_agents()

        assert second_pop == []


@pytest.mark.integration
class TestEventDebouncer:
    def test_first_call_passes(self, redis_client):
        debouncer = EventDebouncer(redis_client)
        assert debouncer.should_process("event-1", ttl_seconds=60) is True

    def test_duplicate_call_skips(self, redis_client):
        debouncer = EventDebouncer(redis_client)
        assert debouncer.should_process("event-1", ttl_seconds=60) is True
        assert debouncer.should_process("event-1", ttl_seconds=60) is False

    def test_different_keys_independent(self, redis_client):
        debouncer = EventDebouncer(redis_client)
        assert debouncer.should_process("event-1", ttl_seconds=60) is True
        assert debouncer.should_process("event-2", ttl_seconds=60) is True
