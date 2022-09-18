"""Tests for simple_ttl_cache."""

import copy

import pytest

from simple_ttl_cache import Cache, _key_factory, ttl_cache


def test_cache():
    cache = Cache()
    assert cache.get('missing-key') is None

    key = 'string'
    value = {'a': 1, 'b': '2', 'c': True, 'd': [1, '2', True]}

    cache.put(key, value)
    assert cache.get(key) == value

    changed_value = copy.copy(value)
    changed_value['a'] = 2

    cache.put(key, changed_value)
    assert cache.get(key) == changed_value

    cache.cache_clear()
    with pytest.raises(ValueError):
        cache.put(key, value, ttl=-1)


def test_cache_evict():
    cache = Cache()
    key = 'string'
    value = 'value'

    cache.put(key, value)
    assert cache.get(key) == value

    cache.evict(key)
    assert cache.get(key) is None

    cache.evict('missing-key')


def test_cache_init():
    with pytest.raises(ValueError):
        Cache(default_ttl=-1)


def test_cache_parameters():
    cache = Cache()
    key = 'string'
    value = {'a': 1, 'b': '2', 'c': True, 'd': [1, '2', True]}

    with pytest.raises(ValueError):
        cache.get(None)

    with pytest.raises(ValueError):
        cache.put(None, value)

    with pytest.raises(ValueError):
        cache.put(key, None)


def test_cache_clear():
    cache = Cache()
    cache.cache_clear()


def test_cache_info():
    cache = Cache()
    cache.cache_info()


def test_cache_ttl():
    cache = Cache()
    items = (
        ('k1', 'v1', 10),
        ('k2', 'v2', 20),
        ('k3', 'v3', 30),
        ('k4', 'v4', 20),
        ('k5', 'v5', 10),
    )

    for key, value, ttl in items:
        cache.put(key, value, ttl)

    items = [r.key for r in cache._lru]
    assert items == ['k1', 'k5', 'k2', 'k4', 'k3']


def test_ttl_cache_decorator():
    @ttl_cache
    def expensive_calculation(some_id: int) -> int:
        return some_id + 42

    assert expensive_calculation(0) == 42
    stats = expensive_calculation.cache_info()
    assert stats.hits == 0
    assert stats.misses == 1

    assert expensive_calculation(0) == 42
    stats = expensive_calculation.cache_info()
    assert stats.hits == 1
    assert stats.misses == 1

    expensive_calculation.evict(0)
    assert expensive_calculation(0) == 42
    stats = expensive_calculation.cache_info()
    assert stats.hits == 1
    assert stats.misses == 2

    assert expensive_calculation(1) == 43
    stats = expensive_calculation.cache_info()
    assert stats.hits == 1
    assert stats.misses == 3

    expensive_calculation.cache_clear()
    stats = expensive_calculation.cache_info()
    assert stats.hits == 0
    assert stats.misses == 0


def test_ttl_cache_decorator_with_key_factory():
    @ttl_cache(key_factory=lambda args, kwargs: args)
    def expensive_calculation(some_id: int) -> int:
        return some_id + 42

    assert expensive_calculation(0) == 42
    stats = expensive_calculation.cache_info()
    assert stats.hits == 0
    assert stats.misses == 1

    assert expensive_calculation(0) == 42
    stats = expensive_calculation.cache_info()
    assert stats.hits == 1
    assert stats.misses == 1


def test_cache_key_factory():
    assert _key_factory((1,), {}) == 1
    key = _key_factory((1,), {'a': 'b'})
    assert len(key) == 3
    assert key[0] == 1
    assert key[2] == ('a', 'b')
