import time


class TimerError(Exception):

    """A custom exception used to report errors in use of Timer class"""


class Timer:
    start_time: float

    def __init__(self):
        self.start_time = 0.0

    def start(self):

        """Start a new timer"""

        if self.start_time > 0.0:

            raise TimerError(f"Timer is running. Use '.stop()' to stop it")

        self.start_time = time.perf_counter()

    def get_time(self):

        if self.start_time == 0.0:

            raise TimerError(f"Timer is not running. Use '.start()' to start it")

        return time.perf_counter() - self.start_time

    def reset(self):

        self.start_time = time.perf_counter()

    def stop(self):

        """Stop the timer, and report the elapsed time"""

        if self.start_time == 0.0:

            raise TimerError(f"Timer is not running. Use '.start()' to start it")

        elapsed_time = time.perf_counter() - self.start_time

        self.start_time = 0.0

        print(f"[DEBUG] Elapsed time (timer): {elapsed_time:0.4f} seconds")