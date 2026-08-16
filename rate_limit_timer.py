# Copyright (C) Shigeyuki <http://patreon.com/Shigeyuki>
# License: GNU AGPL version 3 or later <http://www.gnu.org/licenses/agpl.html>

import time

class RateLimitTimer:
    def __init__(self):
        self.timers = {}

    def limit(self, key, seconds_value):
        if key not in self.timers:
            self.timers[key] = {
                'last_sync': time.time()
            }
            return False

        current_time = time.time()
        timer = self.timers[key]

        if current_time - timer['last_sync'] < seconds_value:
            return True

        timer['last_sync'] = current_time
        return False

rate_limiter = RateLimitTimer()

# print(rate_limiter.limit("example", 5)) # False
# print(rate_limiter.limit("example", 5)) # True
# time.sleep(6)
# print(rate_limiter.limit("example", 5)) # False