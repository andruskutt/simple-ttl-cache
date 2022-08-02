# Simple TTL cache for multithreaded application

## Usage

Usual get, put and evict methods.

Using decorator:

```python
from simple_ttl_cache import ttl_cache


@ttl_cache
def expensive_calculation(id: int) -> str
    return str(id)
```

## Installation

```shell
$ pip install simple_ttl_cache
```
