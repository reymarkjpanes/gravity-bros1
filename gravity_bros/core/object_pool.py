from typing import TypeVar, Generic, Callable

T = TypeVar('T')


class ObjectPool(Generic[T]):
    """Generic pool that recycles instances instead of allocating new ones.

    Usage:
        pool = ObjectPool(factory=lambda: Enemy(0, 0))
        obj = pool.acquire()   # get a recycled or new instance
        pool.release(obj)      # return it for future reuse
    """

    def __init__(self, factory: Callable[[], T], max_size: int = 200):
        self._factory = factory
        self._max_size = max_size
        self._available: list[T] = []

    def acquire(self) -> T:
        """Return a pooled instance, or create a new one if the pool is empty."""
        if self._available:
            return self._available.pop()
        return self._factory()

    def release(self, obj: T) -> None:
        """Return obj to the pool for future reuse.
        Silently discards if the pool is already at max_size."""
        if len(self._available) < self._max_size:
            self._available.append(obj)

    @property
    def available_count(self) -> int:
        return len(self._available)
