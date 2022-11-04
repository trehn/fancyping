from datetime import datetime
from statistics import mean, median
from threading import Thread, Event, Lock

from icmplib import ping


class Scheduler(Thread):
    def __init__(self, recorder):
        self.recorder = recorder

    def run(self):
        while not self.recorder.stopped.wait(self.recorder.interval):
            self.recorder._schedule_ping()


class PingRecorder:
    STATS_INTERVALS = [
        (10, "10s"),
        (30, "30s"),
        (60, "60s"),
        (60 * 2, "2m"),
        (60 * 5, "5m"),
        (60 * 10, "10m"),
        (60 * 15, "15m"),
        (60 * 30, "30m"),
        (60 * 60, "1h"),
        (60 * 60 * 3, "3h"),
        (60 * 60 * 6, "6h"),
        (60 * 60 * 12, "12h"),
        (60 * 60 * 24, "24h"),
    ]

    def __init__(self, target, count=0, interval=1.0, timeout=2.0, history=60 * 60 * 24):
        self.target = target
        self.count = count
        self.interval = interval
        self.timeout = timeout
        self.history = history

        self.updated = Event()
        self._lock = Lock()
        self.stopped = Event()

        self.reset()

    @property
    def last_rtt(self):
        try:
            return self._results[0]
        except IndexError:
            return None

    def reset(self):
        with self._lock:
            self._datetimes = []
            self._results = []
            self.error = None
            self.last_alive = None
            self.last_down = None
        self.updated.set()

    def stop(self):
        self.stopped.set()

    def start(self):
        self.time_started = datetime.utcnow()
        self.stopped.clear()
        Thread(target=self._schedule_pings).start()

    def _schedule_pings(self):
        self._schedule_ping()
        while not self.stopped.wait(self.interval):
            self._schedule_ping()

    def _schedule_ping(self):
        Thread(target=self._ping).start()

    def _ping(self):
        try:
            result = ping(self.target, count=1, timeout=self.timeout, privileged=False)
        except Exception as exc:
            with self._lock:
                self.error = str(exc)
                self.last_down = datetime.utcnow()
        else:
            now = datetime.utcnow()
            with self._lock:
                if result.is_alive:
                    self._datetimes.insert(0, now)
                    self._results.insert(0, result.rtts[0])
                    self.error = None
                    self.last_alive = now
                else:
                    self._datetimes.insert(0, now)
                    self._results.insert(0, None)
                    self.error = "CONTACT LOST"
                    self.last_down = now
                if len(self._results) > self.history:
                    self._datetimes.pop()
                    self._results.pop()
                if self.count and len(self._results) > self.count:
                    self.stopped.set()
        finally:
            self.updated.set()

    def packet_loss(self, timeframe):
        results = self._results[:int(timeframe / self.interval)]
        if not results:
            return 1.0
        return results.count(None) / len(results)

    def rtt_stats(self, timeframe):
        values = list(filter(
            lambda v: v is not None,
            self._results[:int(timeframe / self.interval)],
        ))
        if not values:
            return None
        return mean(values), median(values), min(values), max(values)

    def report_stats(self):
        lines = [
            "TIME  " +
            "AVG".rjust(9) +
            "MED".rjust(9) +
            "MIN".rjust(9) +
            "MAX".rjust(9) +
            "P/L".rjust(7)
        ]
        for timeframe, label in self.STATS_INTERVALS:
            pl = self.packet_loss(timeframe)
            stats = self.rtt_stats(timeframe)
            if stats:
                lines.append(
                    f"{label.rjust(4)}  "
                    f"{stats[0]:9.2f}"
                    f"{stats[1]:9.2f}"
                    f"{stats[2]:9.2f}"
                    f"{stats[3]:9.2f}"
                    f"{pl * 100:6.1f}%"
                )
            else:
                lines.append(
                    f"{label.rjust(4)}  "
                    f"{' ':<9}"
                    f"{' ':<9}"
                    f"{' ':<9}"
                    f"{' ':<9}"
                    f"{pl * 100:6.1f}%"
                )
            if len(self._results) < int(timeframe / self.interval):
                break
        return "\n".join(lines)

    def report_write_full(self):
        Thread(target=self._report_write_full).start()

    def _report_write_full(self):
        reptime = datetime.utcnow()
        filename = f"fancyping_report_{self.target}_{reptime.strftime('%Y%m%dT%H%M%SZ')}.txt"
        with open(filename, 'w') as f:
            f.write(f"TARGET: {self.target}\n")
            f.write(f"UNTIL:  {reptime.strftime('%Y-%m-%dT%H:%M:%SZ')}\n\n")
            f.write(f"FROM:   {self.time_started.strftime('%Y-%m-%dT%H:%M:%SZ')}\n")
            f.write(self.report_stats() + "\n\n")
            for rtt, time in zip(self._results.copy(), self._datetimes.copy()):
                if rtt is None:
                    rtt_text = "TIMEOUT"
                else:
                    rtt_text = f"{rtt:9.2f}ms"
                f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')}  {rtt_text}\n")
