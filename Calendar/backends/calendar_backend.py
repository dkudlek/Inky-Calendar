from ics import Calendar
from enum import Enum
from urllib.request import urlopen
from pytz import timezone
from datetime import datetime, date, timedelta
import arrow



class CalendarBackend:
    class Scope(Enum):
        ALL = 0
        THIS_YEAR = 2
        THIS_MONTH = 3
        TODAY = 4
        NEXT = 5
        ACTIVE = 6

    def __init__(self, config):
        self.config = config
        self.ical_urls = config['CalendarBackend']['ical_urls']
        self.timezone = config['general']['timezone']
        self.events = None
        self.update()

    def update(self):
        all_events = None
        for icalendars in self.ical_urls:
            with urlopen(icalendars) as response:
                decode = response.read().decode()
                ical = Calendar(decode)
                events = [event for event in ical.events]
                if all_events is None:
                    all_events = events
                else:
                    all_events += events
        self.events = sorted(all_events, key=lambda x: x.begin)

    def get_events(self, mode=None):
        assert(self.events is not None)
        time_now = arrow.now(self.timezone)
        event_filter = None
        if self.Scope.THIS_YEAR == mode:
            event_filter = lambda x: x.begin.date().year == time_now.date().year
        elif self.Scope.THIS_MONTH == mode:
            event_filter = lambda x: (x.begin.date().year == time_now.date().year
                                      and x.begin.date().month == time_now.date().month)
        elif self.Scope.TODAY == mode:
            event_filter = lambda x: (x.begin.date().year == time_now.date().year
                                      and x.begin.date().month == time_now.date().month
                                      and x.begin.date().day == time_now.date().day)
        elif self.Scope.NEXT == mode:
            event_filter = lambda x: x.begin.datetime > time_now.datetime
        elif self.Scope.ACTIVE == mode:
            event_filter = lambda x: (x.begin.datetime <= time_now.datetime
                                      and x.end.datetime >= time_now.datetime)
        else:
            event_filter = lambda x: x
        result = list(filter(event_filter, self.events))
        return result


if __name__ == "__main__":
    import yaml
    config = None
    with open("../settings.yaml", 'r') as stream:
        try:
            config = yaml.safe_load(stream)
            #print(config)
        except yaml.YAMLError as exc:
            print(exc)
    cal = CalendarBackend(config)
    for x in CalendarBackend.Scope:
        print("\n\n\n{}".format(x))
        cal.update()
        evn = cal.get_events(mode=x)
        for e in evn:
            print(repr(e))
