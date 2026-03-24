"""
Proxy rotation system.
Supports HTTP, HTTPS, SOCKS5 proxies.
"""
import random
import time
from dataclasses import dataclass, field


@dataclass
class ProxyStats:
    """Statistics for a proxy."""
    url: str
    success_count: int = 0
    failure_count: int = 0
    total_time: float = 0.0
    last_used: float = 0.0
    blocked: bool = False

    @property
    def avg_response_time(self) -> float:
        total = self.success_count + self.failure_count
        return self.total_time / total if total > 0 else 0.0

    @property
    def success_rate(self) -> float:
        total = self.success_count + self.failure_count
        return self.success_count / total if total > 0 else 1.0


class ProxyRotator:
    """
    Intelligent proxy rotation with health tracking.

    Strategies:
    - Round-robin
    - Random
    - Weighted (by success rate)
    - Least-recently-used
    """

    def __init__(self, proxy_list: list[str], strategy: str = "weighted"):
        self._proxies: list[ProxyStats] = [
            ProxyStats(url=p) for p in proxy_list
        ]
        self._strategy = strategy
        self._current_idx = 0

    def has_proxies(self) -> bool:
        return len(self._proxies) > 0

    def get_next(self) -> str | None:
        """Get the next proxy based on strategy."""
        active = [p for p in self._proxies if not p.blocked]
        if not active:
            # Reset all blocked proxies as a last resort
            for p in self._proxies:
                p.blocked = False
            active = self._proxies

        if not active:
            return None

        if self._strategy == "round_robin":
            proxy = active[self._current_idx % len(active)]
            self._current_idx += 1
        elif self._strategy == "random":
            proxy = random.choice(active)
        elif self._strategy == "weighted":
            # Weight by success rate
            weights = [max(p.success_rate, 0.1) for p in active]
            proxy = random.choices(active, weights=weights, k=1)[0]
        elif self._strategy == "lru":
            proxy = min(active, key=lambda p: p.last_used)
        else:
            proxy = random.choice(active)

        proxy.last_used = time.time()
        return proxy.url

    def report_success(self, proxy_url: str, response_time: float):
        """Report a successful request through a proxy."""
        for p in self._proxies:
            if p.url == proxy_url:
                p.success_count += 1
                p.total_time += response_time
                break

    def report_failure(self, proxy_url: str, response_time: float = 0.0):
        """Report a failed request through a proxy."""
        for p in self._proxies:
            if p.url == proxy_url:
                p.failure_count += 1
                p.total_time += response_time
                # Block proxy if failure rate is too high
                if p.failure_count > 5 and p.success_rate < 0.3:
                    p.blocked = True
                break

    def get_stats(self) -> list[dict]:
        """Get statistics for all proxies."""
        return [
            {
                "url": p.url,
                "success": p.success_count,
                "failure": p.failure_count,
                "success_rate": f"{p.success_rate:.1%}",
                "avg_time": f"{p.avg_response_time:.2f}s",
                "blocked": p.blocked,
            }
            for p in self._proxies
        ]
