"""
Minimal TTL cache.

Homepage: https://github.com/andruskutt/simple-ttl-cache

License: MIT
"""

import bisect
import functools
import threading
import time
from collections.abc import Hashable
from typing import Any, Callable, Dict, List, NamedTuple, Optional, Tuple, TypeVar, cast


__all__ = ['Cache', 'ttl_cache']

# time to live in seconds
_DEFAULT_TTL = 3600
_ARG_SEPARATOR = object()

F = TypeVar('F', bound=Callable[..., Any])


class CacheInfo(NamedTuple):
    hits: int
    misses: int
    currsize: int


class CacheEntry:
    __slots__ = ('key', 'value', 'valid_until')

    def __init__(self, key: Hashable, value: Any, valid_until: float) -> None:
        self.key = key
        self.value = value
        self.valid_until = valid_until

    def __lt__(self, other: 'CacheEntry') -> bool:
        return self.valid_until < other.valid_until


class Cache:
    def __init__(self, default_ttl: int = _DEFAULT_TTL) -> None:
        if default_ttl <= 0:
            raise ValueError(f'Invalid default time to live {default_ttl}')

        self.default_ttl = default_ttl
        self._lock = threading.Lock()
        self.timer = time.monotonic
        self.cache_clear()

    def get(self, key: Hashable) -> Any:
        self._validate_key(key)
        now = self.timer()

        with self._lock:
            self._remove_expired_entries(now)

            result = self._cache.get(key)
            if result is not None:
                self.hits += 1
                return result.value

            self.misses += 1

    def put(self, key: Hashable, value: Any, ttl: Optional[int] = None) -> bool:
        self._validate_key(key)
        self._validate_value(value)
        now = self.timer()

        with self._lock:
            self._remove_expired_entries(now)

            result = self._cache.get(key)
            if result is None:
                self._set_value(key, value, self._valid_until(now, ttl))
                return True

        return False

    def evict(self, key: Hashable) -> None:
        self._validate_key(key)

        with self._lock:
            try:
                cache_entry = self._cache.pop(key)
                self._lru.remove(cache_entry)
            except KeyError:
                pass

    def cache_clear(self) -> None:
        with self._lock:
            self._cache: Dict[Any, CacheEntry] = {}
            self._lru: List[CacheEntry] = []
            self.hits = 0
            self.misses = 0

    def cache_info(self) -> CacheInfo:
        with self._lock:
            return CacheInfo(self.hits, self.misses, len(self._cache))

    def _validate_key(self, key: Hashable) -> None:
        if key is None:
            raise ValueError('Key cannot be None')

    def _validate_value(self, value: Any) -> None:
        if value is None:
            raise ValueError('Value cannot be None')

    def _valid_until(self, start: float, ttl: Optional[int]) -> float:
        if ttl is None:
            ttl = self.default_ttl
        elif ttl <= 0:
            raise ValueError(f'Invalid time to live {ttl}')

        return start + ttl

    def _set_value(self, key: Hashable, value: Any, valid_until: float) -> None:
        cache_entry = CacheEntry(key, value, valid_until)
        self._cache[key] = cache_entry

        # update self._lru, keeping it sorted by valid_until
        bisect.insort_right(self._lru, cache_entry)

    def _remove_expired_entries(self, time: float) -> None:
        pos = 0  # noqa: SIM113
        for e in self._lru:
            if e.valid_until > time:
                break

            self._cache.pop(e.key)
            pos += 1

        if pos > 0:
            self._lru = self._lru[pos:]


def _key_factory(args: Tuple[Hashable, ...], kwargs: Dict[str, Hashable]) -> Hashable:
    if not kwargs and len(args) == 1:
        return args[0]
    return (*args, _ARG_SEPARATOR, *kwargs.items())


def ttl_cache(
        producer: Optional[F] = None,
        *,
        ttl: Optional[int] = None,
        key_factory: Callable[[Tuple[Hashable, ...], Dict[str, Hashable]], Hashable] = _key_factory) -> F:
    if producer is None:
        return functools.partial(ttl_cache, ttl=ttl, key_factory=key_factory)

    cache = Cache(default_ttl=ttl if ttl is not None else _DEFAULT_TTL)
    dogpile_lock: Dict[Hashable, threading.Event] = {}

    @functools.wraps(producer)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        key = key_factory(args, kwargs)

        cache._validate_key(key)
        produce_in_progress = True
        now = cache.timer()

        with cache._lock:
            cache._remove_expired_entries(now)

            result = cache._cache.get(key)
            if result is not None:
                cache.hits += 1
                return result.value

            producer_event = dogpile_lock.get(key)
            if producer_event is None:
                dogpile_lock[key] = producer_event = threading.Event()
                produce_in_progress = False

        if not produce_in_progress:
            result = producer(*args, **kwargs)

            with cache._lock:
                cache._set_value(key, result, cache._valid_until(now, ttl))
                cache.misses += 1

                del dogpile_lock[key]
                producer_event.set()
        else:
            producer_event.wait()

            with cache._lock:
                result = cache._cache.get(key)
                if result is not None:
                    cache.hits += 1
                    return result.value

        return result

    wrapper.cache_info = cache.cache_info
    wrapper.cache_clear = cache.cache_clear
    wrapper.evict = cache.evict

    return cast(F, wrapper)
