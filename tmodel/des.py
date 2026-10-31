"""A minimal discrete-event kernel: processes are generators that yield events.

    env = Env()
    def proc(env):
        yield env.timeout(3.0)
    env.process(proc(env))
    env.run(until=10.0)

Events: env.timeout(dt); Resource.request() / Resource.release(); Store.put(item) / Store.get().
A Store of capacity 0 hands an item over only to a waiting getter (blocking after service).
"""
import heapq
import itertools


class Event:
    __slots__ = ("callbacks", "triggered", "value")

    def __init__(self):
        self.callbacks, self.triggered, self.value = [], False, None


class Env:
    def __init__(self):
        self.now = 0.0
        self._q = []
        self._n = itertools.count()

    def _schedule(self, t, fn):
        heapq.heappush(self._q, (t, next(self._n), fn))

    def succeed(self, ev, value=None, delay=0.0):
        def fire():
            ev.triggered, ev.value = True, value
            for cb in ev.callbacks:
                cb(value)
        self._schedule(self.now + delay, fire)
        return ev

    def timeout(self, dt):
        if dt < 0:
            raise ValueError("negative delay")
        return self.succeed(Event(), delay=dt)

    def process(self, gen):
        def step(value=None):
            try:
                ev = gen.send(value)
            except StopIteration:
                return
            if ev.triggered:
                self._schedule(self.now, lambda: step(ev.value))
            else:
                ev.callbacks.append(step)
        self._schedule(self.now, step)

    def run(self, until):
        while self._q and self._q[0][0] <= until:
            t, _, fn = heapq.heappop(self._q)
            self.now = t
            fn()
        self.now = until


class Resource:
    """n identical units, FIFO; tracks busy unit-time for utilisation."""

    def __init__(self, env, n):
        self.env, self.n, self.free = env, n, n
        self._wait = []
        self.busy_time, self._t = 0.0, 0.0

    def _acc(self):
        self.busy_time += (self.n - self.free) * (self.env.now - self._t)
        self._t = self.env.now

    def request(self):
        ev = Event()
        if self.free > 0 and not self._wait:
            self._acc()
            self.free -= 1
            self.env.succeed(ev)
        else:
            self._wait.append(ev)
        return ev

    def release(self):
        self._acc()
        if self._wait:
            self.env.succeed(self._wait.pop(0))
        else:
            self.free += 1


class Store:
    """capacity places; a put blocks until a place is free or a getter is waiting (capacity 0: hand-over only)."""

    def __init__(self, env, capacity):
        self.env, self.capacity = env, capacity
        self.items, self._getters, self._putters = [], [], []

    def put(self, item):
        ev = Event()
        if self._getters:
            self.env.succeed(self._getters.pop(0), item)
            self.env.succeed(ev)
        elif len(self.items) < self.capacity:
            self.items.append(item)
            self.env.succeed(ev)
        else:
            self._putters.append((item, ev))
        return ev

    def get(self):
        ev = Event()
        if self.items:
            self.env.succeed(ev, self.items.pop(0))
            if self._putters:
                item, pev = self._putters.pop(0)
                self.items.append(item)
                self.env.succeed(pev)
        elif self._putters:                       # capacity 0: take directly from a blocked putter
            item, pev = self._putters.pop(0)
            self.env.succeed(ev, item)
            self.env.succeed(pev)
        else:
            self._getters.append(ev)
        return ev
