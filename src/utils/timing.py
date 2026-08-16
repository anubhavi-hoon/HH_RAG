"""Wall-clock timing.

The single place in the backend that turns a duration into a number. Every value
it produces is measured with :func:`time.perf_counter` and expressed in
milliseconds — nothing here estimates, simulates, or rounds a duration into
existence.
"""

import time
from types import TracebackType
from typing import Optional, Type


class Timer:
    """Measures elapsed wall-clock time in milliseconds.

    As a context manager::

        with Timer() as timer:
            result = do_work()
        timer.elapsed_ms

    Or explicitly::

        timer = Timer().start()
        ...
        elapsed = timer.stop()
    """

    __slots__ = ("_started_at", "_elapsed_ms")

    def __init__(self) -> None:
        self._started_at: Optional[float] = None
        self._elapsed_ms: float = 0.0

    def start(self) -> "Timer":
        self._started_at = time.perf_counter()
        return self

    def stop(self) -> float:
        """Freeze and return the elapsed milliseconds."""
        if self._started_at is None:
            raise RuntimeError("Timer.stop() called before start()")
        self._elapsed_ms = (time.perf_counter() - self._started_at) * 1000.0
        self._started_at = None
        return self._elapsed_ms

    @property
    def elapsed_ms(self) -> float:
        """Milliseconds elapsed; live while running, frozen once stopped."""
        if self._started_at is not None:
            return (time.perf_counter() - self._started_at) * 1000.0
        return self._elapsed_ms

    def __enter__(self) -> "Timer":
        return self.start()

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        self.stop()
