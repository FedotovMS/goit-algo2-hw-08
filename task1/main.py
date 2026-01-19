import random
import time
from collections import OrderedDict


# ---------------------------
# LRU Cache (готовий клас)
# ---------------------------
class LRUCache:
    def __init__(self, capacity: int):
        self.capacity = capacity
        self.od = OrderedDict()

    def get(self, key):
        if key not in self.od:
            return -1
        self.od.move_to_end(key)  # позначаємо як "найсвіжіший"
        return self.od[key]

    def put(self, key, value):
        if key in self.od:
            self.od.move_to_end(key)
        self.od[key] = value
        if len(self.od) > self.capacity:
            self.od.popitem(last=False)  # видаляємо "найстаріший"

    def keys(self):
        # потрібні для інвалідації лінійним проходом
        return self.od.keys()

    def delete(self, key):
        if key in self.od:
            del self.od[key]


# ---------------------------
# Генератор запитів 
# ---------------------------
def make_queries(n, q, hot_pool=30, p_hot=0.95, p_update=0.03):
    hot = [(random.randint(0, n // 2), random.randint(n // 2, n - 1))
           for _ in range(hot_pool)]
    queries = []
    for _ in range(q):
        if random.random() < p_update:        # ~3% запитів — Update
            idx = random.randint(0, n - 1)
            val = random.randint(1, 100)
            queries.append(("Update", idx, val))
        else:                                 # ~97% — Range
            if random.random() < p_hot:       # 95% — «гарячі» діапазони
                left, right = random.choice(hot)
            else:                             # 5% — випадкові діапазони
                left = random.randint(0, n - 1)
                right = random.randint(left, n - 1)
            queries.append(("Range", left, right))
    return queries


# ---------------------------
# 4 обов'язкові функції
# ---------------------------
def range_sum_no_cache(array, left, right):
    # Сума без кешування
    s = 0
    for i in range(left, right + 1):
        s += array[i]
    return s


def update_no_cache(array, index, value):
    # Оновлення без кешування
    array[index] = value


def range_sum_with_cache(array, left, right, cache: LRUCache):
    # Сума з використанням LRUCache (K=1000)
    key = (left, right)
    cached = cache.get(key)
    if cached != -1:
        return cached

    s = 0
    for i in range(left, right + 1):
        s += array[i]

    cache.put(key, s)
    return s


def update_with_cache(array, index, value, cache: LRUCache):
    # Оновлюємо масив
    array[index] = value

    # Інвалідуємо всі діапазони, що містять index (лінійний прохід по ключах кешу)
    to_delete = []
    for (l, r) in list(cache.keys()):  # list(...) щоб безпечно видаляти
        if l <= index <= r:
            to_delete.append((l, r))

    for key in to_delete:
        cache.delete(key)


# ---------------------------
# Прогін та замір часу
# ---------------------------
def run_no_cache(array, queries):
    start = time.perf_counter()
    checksum = 0  # щоб оптимізатор випадково нічого "не викинув"
    for q in queries:
        if q[0] == "Range":
            _, l, r = q
            checksum ^= range_sum_no_cache(array, l, r)
        else:
            _, idx, val = q
            update_no_cache(array, idx, val)
    elapsed = time.perf_counter() - start
    return elapsed, checksum


def run_with_cache(array, queries, capacity=1000):
    cache = LRUCache(capacity)
    hits = 0
    misses = 0

    start = time.perf_counter()
    checksum = 0
    for q in queries:
        if q[0] == "Range":
            _, l, r = q
            key = (l, r)
            v = cache.get(key)
            if v != -1:
                hits += 1
                checksum ^= v
            else:
                misses += 1
                v = range_sum_with_cache(array, l, r, cache)
                checksum ^= v
        else:
            _, idx, val = q
            update_with_cache(array, idx, val, cache)

    elapsed = time.perf_counter() - start
    return elapsed, checksum, hits, misses


def main():
    # Параметри з ТЗ
    N = 100_000
    Q = 50_000
    K = 1000

    # Для повторюваності
    random.seed(42)

    # Початковий масив і запити
    base_array = [random.randint(1, 100) for _ in range(N)]
    queries = make_queries(N, Q)

    # ВАЖЛИВО: для чесного порівняння — однаковий стартовий масив в обох прогонах
    arr1 = base_array.copy()
    arr2 = base_array.copy()

    t1, cs1 = run_no_cache(arr1, queries)
    t2, cs2, hits, misses = run_with_cache(arr2, queries, capacity=K)

    # Перевірка (не обов'язково, але корисно): результати мають збігатись
    if cs1 != cs2:
        print("УВАГА: checksum не співпав — перевірте логіку кешування/інвалідації!")

    speedup = (t1 / t2) if t2 > 0 else float("inf")

    print(f"Без кешу : {t1:6.2f} c")
    print(f"LRU-кеш  : {t2:6.2f} c  (прискорення ×{speedup:.1f})")
    print(f"Cache stats: hits={hits}, misses={misses}, hit-rate={hits/(hits+misses+1e-9)*100:.1f}%")


if __name__ == "__main__":
    main()