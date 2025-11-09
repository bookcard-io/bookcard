# The MIT License (MIT)

# Copyright (c) 2025 knguyen and others

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
# of the Software, and to permit persons to whom the Software is furnished to do
# so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Tests for metadata service to achieve 100% coverage."""

from __future__ import annotations

import concurrent.futures
import time
from unittest.mock import MagicMock

import pytest

from fundamental.api.schemas import (
    MetadataProviderCompletedEvent,
    MetadataProviderFailedEvent,
    MetadataProviderStartedEvent,
    MetadataSearchEvent,
    MetadataSearchProgressEvent,
)
from fundamental.metadata.base import MetadataProvider, MetadataProviderError
from fundamental.metadata.registry import MetadataProviderRegistry
from fundamental.models.metadata import MetadataRecord, MetadataSourceInfo
from fundamental.services.metadata_service import MetadataService


class MockProvider(MetadataProvider):
    """Mock provider for testing."""

    def __init__(self, provider_id: str, enabled: bool = True) -> None:
        """Initialize mock provider."""
        super().__init__(enabled)
        self._provider_id = provider_id
        self._provider_name = f"Provider {provider_id}"
        self._search_result: list[MetadataRecord] = []
        self._search_exception: Exception | None = None

    def get_source_info(self) -> MetadataSourceInfo:
        """Get source info."""
        return MetadataSourceInfo(
            id=self._provider_id,
            name=self._provider_name,
            description=f"Test provider {self._provider_id}",
            base_url=f"https://{self._provider_id}.com",
        )

    def search(
        self, query: str, locale: str = "en", max_results: int = 10
    ) -> list[MetadataRecord]:
        """Search implementation."""
        if self._search_exception:
            raise self._search_exception
        return self._search_result

    def set_search_result(self, results: list[MetadataRecord]) -> None:
        """Set search result."""
        self._search_result = results

    def set_search_exception(self, exc: Exception) -> None:
        """Set search exception."""
        self._search_exception = exc


@pytest.fixture
def mock_registry() -> MetadataProviderRegistry:
    """Create a mock registry."""
    return MetadataProviderRegistry.__new__(MetadataProviderRegistry)


@pytest.fixture
def provider1() -> MockProvider:
    """Create first test provider."""
    return MockProvider("provider1", enabled=True)


@pytest.fixture
def provider2() -> MockProvider:
    """Create second test provider."""
    return MockProvider("provider2", enabled=True)


@pytest.fixture
def metadata_record1() -> MetadataRecord:
    """Create first test metadata record."""
    return MetadataRecord(
        source_id="provider1",
        external_id="123",
        title="Test Book 1",
        authors=["Author 1"],
        url="https://provider1.com/book/123",
    )


@pytest.fixture
def metadata_record2() -> MetadataRecord:
    """Create second test metadata record."""
    return MetadataRecord(
        source_id="provider2",
        external_id="456",
        title="Test Book 2",
        authors=["Author 2"],
        url="https://provider2.com/book/456",
    )


def test_metadata_service_init_with_registry(
    mock_registry: MetadataProviderRegistry,
) -> None:
    """Test MetadataService __init__ with registry parameter (covers lines 85-86)."""
    service = MetadataService(registry=mock_registry, max_workers=3)
    assert service.registry is mock_registry
    assert service.max_workers == 3


def test_metadata_service_init_without_registry() -> None:
    """Test MetadataService __init__ without registry (uses global)."""
    service = MetadataService(max_workers=5)
    assert service.registry is not None
    assert service.max_workers == 5


def test_handle_provider_success(
    provider1: MockProvider,
    metadata_record1: MetadataRecord,
) -> None:
    """Test _handle_provider_success method (covers lines 131-167)."""
    service = MetadataService()
    all_results: list[MetadataRecord] = []
    provider_start_times: dict[str, float] = {}
    providers_completed = 0
    providers_failed = 0
    total_providers = 2
    request_id = "test-request-123"
    events: list[MetadataSearchEvent] = []

    def _now_ms() -> int:
        return int(time.time() * 1000)

    def _publish(event: MetadataSearchEvent) -> None:
        events.append(event)

    # Set start time
    provider_start_times[provider1.get_source_info().id] = time.monotonic() - 0.1

    result = service._handle_provider_success(
        provider=provider1,
        results=[metadata_record1],
        provider_start_times=provider_start_times,
        providers_completed=providers_completed,
        providers_failed=providers_failed,
        total_providers=total_providers,
        all_results=all_results,
        request_id=request_id,
        _now_ms=_now_ms,
        _publish=_publish,
    )

    assert result == 1
    assert len(all_results) == 1
    assert all_results[0] == metadata_record1
    assert len(events) == 2
    assert isinstance(events[0], MetadataProviderCompletedEvent)
    assert isinstance(events[1], MetadataSearchProgressEvent)


def test_handle_provider_failure_metadata_error(
    provider1: MockProvider,
) -> None:
    """Test _handle_provider_failure with MetadataProviderError (covers lines 209-223)."""
    service = MetadataService()
    all_results: list[MetadataRecord] = []
    providers_completed = 0
    providers_failed = 0
    total_providers = 2
    request_id = "test-request-123"
    events: list[MetadataSearchEvent] = []

    def _now_ms() -> int:
        return int(time.time() * 1000)

    def _publish(event: MetadataSearchEvent) -> None:
        events.append(event)

    error = MetadataProviderError("Provider error")
    result = service._handle_provider_failure(
        provider=provider1,
        error=error,
        providers_completed=providers_completed,
        providers_failed=providers_failed,
        total_providers=total_providers,
        all_results=all_results,
        request_id=request_id,
        _now_ms=_now_ms,
        _publish=_publish,
    )

    assert result == 1
    assert len(events) == 2
    assert isinstance(events[0], MetadataProviderFailedEvent)
    assert isinstance(events[1], MetadataSearchProgressEvent)


def test_handle_provider_failure_unexpected_error(
    provider1: MockProvider,
) -> None:
    """Test _handle_provider_failure with unexpected error (covers lines 216-222)."""
    service = MetadataService()
    all_results: list[MetadataRecord] = []
    providers_completed = 0
    providers_failed = 0
    total_providers = 2
    request_id = "test-request-123"
    events: list[MetadataSearchEvent] = []

    def _now_ms() -> int:
        return int(time.time() * 1000)

    def _publish(event: MetadataSearchEvent) -> None:
        events.append(event)

    error = ValueError("Unexpected error")
    result = service._handle_provider_failure(
        provider=provider1,
        error=error,
        providers_completed=providers_completed,
        providers_failed=providers_failed,
        total_providers=total_providers,
        all_results=all_results,
        request_id=request_id,
        _now_ms=_now_ms,
        _publish=_publish,
    )

    assert result == 1
    assert len(events) == 2
    assert isinstance(events[0], MetadataProviderFailedEvent)
    assert isinstance(events[1], MetadataSearchProgressEvent)


def test_initialize_providers_with_ids(
    mock_registry: MetadataProviderRegistry,
    provider1: MockProvider,
    provider2: MockProvider,
) -> None:
    """Test _initialize_providers with provider_ids (covers lines 264-269)."""
    mock_registry._providers = {
        "provider1": type(provider1),
        "provider2": type(provider2),
    }
    mock_registry.get_provider = MagicMock(  # type: ignore[assignment]
        side_effect=lambda pid: provider1
        if pid == "provider1"
        else provider2
        if pid == "provider2"
        else None
    )

    service = MetadataService(registry=mock_registry)
    providers = service._initialize_providers(["provider1", "provider2"])

    assert len(providers) == 2
    assert providers[0].get_source_info().id == "provider1"
    assert providers[1].get_source_info().id == "provider2"


def test_initialize_providers_without_ids(
    mock_registry: MetadataProviderRegistry,
    provider1: MockProvider,
    provider2: MockProvider,
) -> None:
    """Test _initialize_providers without provider_ids (covers lines 270-272)."""
    mock_registry.get_enabled_providers = MagicMock(  # type: ignore[assignment]
        return_value=iter([provider1, provider2])
    )

    service = MetadataService(registry=mock_registry)
    providers = service._initialize_providers(None)

    assert len(providers) == 2


def test_start_provider_searches(
    provider1: MockProvider,
    provider2: MockProvider,
) -> None:
    """Test _start_provider_searches (covers lines 314-340)."""
    service = MetadataService()
    providers = [provider1, provider2]
    query = "test query"
    locale = "en"
    max_results_per_provider = 10
    provider_start_times: dict[str, float] = {}
    request_id = "test-request-123"
    events: list[MetadataSearchEvent] = []

    def _now_ms() -> int:
        return int(time.time() * 1000)

    def _publish(event: MetadataSearchEvent) -> None:
        events.append(event)

    executor = concurrent.futures.ThreadPoolExecutor(max_workers=2)

    try:
        future_to_provider = service._start_provider_searches(
            providers=providers,
            query=query,
            locale=locale,
            max_results_per_provider=max_results_per_provider,
            provider_start_times=provider_start_times,
            request_id=request_id,
            _now_ms=_now_ms,
            _publish=_publish,
            executor=executor,
        )

        assert len(future_to_provider) == 2
        assert len(events) == 2
        assert all(isinstance(e, MetadataProviderStartedEvent) for e in events)
        assert len(provider_start_times) == 2
    finally:
        executor.shutdown(wait=True)


def test_search_empty_query() -> None:
    """Test search with empty query (covers lines 374-375)."""
    service = MetadataService()
    result = service.search("")
    assert result == []

    result = service.search("   ")
    assert result == []


def test_search_no_providers(mock_registry: MetadataProviderRegistry) -> None:
    """Test search with no providers available (covers lines 378-381)."""
    mock_registry.get_enabled_providers = MagicMock(return_value=iter([]))  # type: ignore[assignment]

    service = MetadataService(registry=mock_registry)
    result = service.search("test query")

    assert result == []


def test_search_success(
    mock_registry: MetadataProviderRegistry,
    provider1: MockProvider,
    provider2: MockProvider,
    metadata_record1: MetadataRecord,
    metadata_record2: MetadataRecord,
) -> None:
    """Test search success (covers lines 374-485)."""
    provider1.set_search_result([metadata_record1])
    provider2.set_search_result([metadata_record2])
    mock_registry.get_enabled_providers = MagicMock(  # type: ignore[assignment]
        return_value=iter([provider1, provider2])
    )

    service = MetadataService(registry=mock_registry, max_workers=2)
    events: list[MetadataSearchEvent] = []

    def event_callback(event: MetadataSearchEvent) -> None:
        events.append(event)

    result = service.search(
        query="test query",
        locale="en",
        max_results_per_provider=10,
        provider_ids=None,
        request_id="test-request",
        event_callback=event_callback,
    )

    assert len(result) == 2
    assert any(r.title == "Test Book 1" for r in result)
    assert any(r.title == "Test Book 2" for r in result)
    # Should have started, provider started events, progress events, completed event
    assert len(events) >= 4


def test_search_with_provider_ids(
    mock_registry: MetadataProviderRegistry,
    provider1: MockProvider,
    metadata_record1: MetadataRecord,
) -> None:
    """Test search with specific provider IDs."""
    provider1.set_search_result([metadata_record1])
    mock_registry.get_provider = MagicMock(  # type: ignore[assignment]
        side_effect=lambda pid: provider1 if pid == "provider1" else None
    )

    service = MetadataService(registry=mock_registry, max_workers=1)
    result = service.search(
        query="test query",
        provider_ids=["provider1"],
    )

    assert len(result) == 1
    assert result[0].title == "Test Book 1"


def test_search_with_provider_failure(
    mock_registry: MetadataProviderRegistry,
    provider1: MockProvider,
    provider2: MockProvider,
    metadata_record1: MetadataRecord,
) -> None:
    """Test search with one provider failing (covers error handling in search)."""
    provider1.set_search_result([metadata_record1])
    provider2.set_search_exception(MetadataProviderError("Provider error"))
    mock_registry.get_enabled_providers = MagicMock(  # type: ignore[assignment]
        return_value=iter([provider1, provider2])
    )

    service = MetadataService(registry=mock_registry, max_workers=2)
    events: list[MetadataSearchEvent] = []

    def event_callback(event: MetadataSearchEvent) -> None:
        events.append(event)

    result = service.search(
        query="test query",
        event_callback=event_callback,
    )

    # Should still return results from successful provider
    assert len(result) == 1
    assert result[0].title == "Test Book 1"
    # Should have failure events
    failure_events = [e for e in events if isinstance(e, MetadataProviderFailedEvent)]
    assert len(failure_events) == 1


def test_search_event_callback_error(
    mock_registry: MetadataProviderRegistry,
    provider1: MockProvider,
    metadata_record1: MetadataRecord,
) -> None:
    """Test search with event callback raising error (covers lines 391-398)."""
    provider1.set_search_result([metadata_record1])
    mock_registry.get_enabled_providers = MagicMock(return_value=iter([provider1]))  # type: ignore[assignment]

    service = MetadataService(registry=mock_registry, max_workers=1)

    def event_callback(event: MetadataSearchEvent) -> None:
        raise RuntimeError("Callback error")

    # Should not raise, just log
    result = service.search(
        query="test query",
        event_callback=event_callback,
    )

    assert len(result) == 1


def test_search_provider_metadata_error(
    provider1: MockProvider,
) -> None:
    """Test _search_provider with MetadataProviderError (covers lines 512-516)."""
    service = MetadataService()
    provider1.set_search_exception(MetadataProviderError("Provider error"))

    with pytest.raises(MetadataProviderError):
        service._search_provider(provider1, "test", "en", 10)


def test_search_provider_unexpected_error(
    provider1: MockProvider,
) -> None:
    """Test _search_provider with unexpected error (covers lines 517-521)."""
    service = MetadataService()
    provider1.set_search_exception(RuntimeError("Unexpected error"))

    with pytest.raises(MetadataProviderError) as exc_info:
        service._search_provider(provider1, "test", "en", 10)

    assert "Unexpected error" in str(exc_info.value)


def test_search_provider_os_error(
    provider1: MockProvider,
) -> None:
    """Test _search_provider with OSError (covers lines 517-521)."""
    service = MetadataService()
    provider1.set_search_exception(OSError("OS error"))

    with pytest.raises(MetadataProviderError) as exc_info:
        service._search_provider(provider1, "test", "en", 10)

    assert "Unexpected error" in str(exc_info.value)


def test_search_provider_value_error(
    provider1: MockProvider,
) -> None:
    """Test _search_provider with ValueError (covers lines 517-521)."""
    service = MetadataService()
    provider1.set_search_exception(ValueError("Value error"))

    with pytest.raises(MetadataProviderError) as exc_info:
        service._search_provider(provider1, "test", "en", 10)

    assert "Unexpected error" in str(exc_info.value)


def test_search_provider_type_error(
    provider1: MockProvider,
) -> None:
    """Test _search_provider with TypeError (covers lines 517-521)."""
    service = MetadataService()
    provider1.set_search_exception(TypeError("Type error"))

    with pytest.raises(MetadataProviderError) as exc_info:
        service._search_provider(provider1, "test", "en", 10)

    assert "Unexpected error" in str(exc_info.value)


def test_list_providers(
    mock_registry: MetadataProviderRegistry,
    provider1: MockProvider,
    provider2: MockProvider,
) -> None:
    """Test list_providers (covers lines 531-532)."""
    mock_registry.get_all_providers = MagicMock(  # type: ignore[assignment]
        return_value=iter([provider1, provider2])
    )

    service = MetadataService(registry=mock_registry)
    providers = service.list_providers()

    assert len(providers) == 2
    assert providers[0].id == "provider1"
    assert providers[1].id == "provider2"


def test_get_provider_found(
    mock_registry: MetadataProviderRegistry,
    provider1: MockProvider,
) -> None:
    """Test get_provider when provider is found (covers lines 547-550)."""
    mock_registry.get_provider = MagicMock(return_value=provider1)  # type: ignore[assignment]

    service = MetadataService(registry=mock_registry)
    info = service.get_provider("provider1")

    assert info is not None
    assert info.id == "provider1"


def test_get_provider_not_found(
    mock_registry: MetadataProviderRegistry,
) -> None:
    """Test get_provider when provider is not found (covers lines 547-550)."""
    mock_registry.get_provider = MagicMock(return_value=None)  # type: ignore[assignment]

    service = MetadataService(registry=mock_registry)
    info = service.get_provider("nonexistent")

    assert info is None
