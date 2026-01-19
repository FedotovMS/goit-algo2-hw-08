import random
from typing import Dict, Deque
import time
from collections import deque


class SlidingWindowRateLimiter:
    def __init__(self, window_size: int = 10, max_requests: int = 1):
        self.window_size = window_size
        self.max_requests = max_requests
        self.user_requests: Dict[str, Deque[float]] = {}

    def _cleanup_window(self, user_id: str, current_time: float) -> None:
        """
        Видаляє застарілі timestamps (старіші за window_size) з deque користувача.
        Якщо deque стає порожнім — прибирає користувача зі структури.
        """
        q = self.user_requests.get(user_id)
        if not q:
            return

        window_start = current_time - self.window_size
        while q and q[0] <= window_start:
            q.popleft()

        if not q:
            # Критерій: якщо всі повідомлення видалені — видаляємо запис про користувача
            self.user_requests.pop(user_id, None)

    def can_send_message(self, user_id: str) -> bool:
        """
        Повертає True, якщо користувач може відправити повідомлення зараз.
        """
        now = time.time()
        self._cleanup_window(user_id, now)

        q = self.user_requests.get(user_id)
        if not q:
            # Перше повідомлення завжди дозволене
            return True

        return len(q) < self.max_requests

    def record_message(self, user_id: str) -> bool:
        """
        Якщо можна — записує timestamp повідомлення і повертає True.
        Якщо не можна — нічого не записує і повертає False.
        """
        now = time.time()
        self._cleanup_window(user_id, now)

        if self.can_send_message(user_id):
            if user_id not in self.user_requests:
                self.user_requests[user_id] = deque()
            self.user_requests[user_id].append(now)
            return True

        return False

    def time_until_next_allowed(self, user_id: str) -> float:
        """
        Повертає час очікування (в секундах) до можливості відправити наступне повідомлення.
        Якщо можна відправляти вже зараз — 0.0
        """
        now = time.time()
        self._cleanup_window(user_id, now)

        q = self.user_requests.get(user_id)
        if not q:
            return 0.0

        if len(q) < self.max_requests:
            return 0.0

        # Треба дочекатися, поки найстаріший timestamp "випаде" з вікна
        oldest = q[0]
        wait = self.window_size - (now - oldest)
        return max(0.0, wait)


# Демонстрація роботи
def test_rate_limiter():
    # Створюємо rate limiter: вікно 10 секунд, 1 повідомлення
    limiter = SlidingWindowRateLimiter(window_size=10, max_requests=1)

    # Симулюємо потік повідомлень від користувачів (послідовні ID від 1 до 20)
    print("\n=== Симуляція потоку повідомлень ===")
    for message_id in range(1, 11):
        # Симулюємо різних користувачів (ID від 1 до 5)
        user_id = message_id % 5 + 1

        result = limiter.record_message(str(user_id))
        wait_time = limiter.time_until_next_allowed(str(user_id))

        print(f"Повідомлення {message_id:2d} | Користувач {user_id} | "
              f"{'✓' if result else f'× (очікування {wait_time:.1f}с)'}")

        # Випадкова затримка від 0.1 до 1 секунди
        time.sleep(random.uniform(0.1, 1.0))

    # Чекаємо, поки вікно очиститься
    print("\nОчікуємо 4 секунди...")
    time.sleep(4)

    print("\n=== Нова серія повідомлень після очікування ===")
    for message_id in range(11, 21):
        user_id = message_id % 5 + 1
        result = limiter.record_message(str(user_id))
        wait_time = limiter.time_until_next_allowed(str(user_id))

        print(f"Повідомлення {message_id:2d} | Користувач {user_id} | "
              f"{'✓' if result else f'× (очікування {wait_time:.1f}с)'}")

        time.sleep(random.uniform(0.1, 1.0))


if __name__ == "__main__":
    test_rate_limiter()