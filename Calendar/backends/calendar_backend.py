from ics import Calendar
from enum import Enum
from urllib.request import urlopen
from pytz import timezone
from datetime import datetime, date, timedelta
from tzlocal import get_localzone
import arrow



class CalendarBackend:
    class Scope(Enum):
        ALL = 0
        STARTING_THIS_YEAR = 1
        STARTING_THIS_MONTH = 2
        STARTING_TODAY = 3
        STARTING_TODAY_WITH_ACTIVE = 4
        THIS_YEAR = 5
        THIS_MONTH = 6
        TODAY = 7

    def __init__(self, config):
        self.config = config
        self.ical_urls = config['CalendarBackend']['ical_urls']
        self.local_tz = get_localzone()
        self.events = None

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

    def get_active_events(self):
        assert(self.events is not None)
        arr_time = arrow.now()
        result = []
        for event in self.events:
            event_start = event.begin.datetime
            event_end = event.end.datetime
            active = False
            if event.all_day:
                active = (event_start.date() <= arr_time.date()
                          and arr_time.date() < event_end.date())
            else:
                active = (event_start <= arr_time and arr_time <= event_end)
            if active:
                result.append(event)
        return result

    def get_events(self, mode=None):
        assert(self.events is not None)
        if (mode is None) or (mode.name not in self.Scope.__members__.keys()):
            mode = self.Scope.ALL
        local_tz = get_localzone()
        time = datetime.now()
        today = time.replace(tzinfo=local_tz).today()
        arr_time = arrow.now()
        result = []
        for event in self.events:
            event_start = event.begin.datetime
            event_end = event.end.datetime
            same_year = (event_start.year == today.year)
            same_year_or_greater = (event_start.year >= today.year)
            same_month = (event_start.month == today.month)
            same_month_or_greater = (event_start.month >= today.month)
            same_day = (event_start.day == today.day)
            same_day_or_greater = (event_start.day >= today.day)
            active = False
            if event.all_day:
                active = (event_start.date() <= arr_time.date()
                          and arr_time.date() < event_end.date())
            else:
                active = (event_start <= arr_time and arr_time <= event_end)
            if self.Scope.ALL == mode:
                result.append(event)
            elif self.Scope.STARTING_THIS_YEAR == mode:
                if same_year_or_greater:
                    result.append(event)
            elif self.Scope.STARTING_THIS_MONTH == mode:
                if (same_year_or_greater and same_month_or_greater):
                    result.append(event)
            elif self.Scope.STARTING_TODAY == mode:
                if (same_year_or_greater and same_month_or_greater and same_day_or_greater):
                    result.append(event)
            elif self.Scope.STARTING_TODAY_WITH_ACTIVE == mode:
                if ((same_year_or_greater and same_month_or_greater and same_day_or_greater) or active):
                    result.append(event)
            elif self.Scope.THIS_YEAR == mode:
                if same_year:
                    result.append(event)
            elif self.Scope.THIS_MONTH == mode:
                if (same_year and same_month):
                    result.append(event)
            elif self.Scope.TODAY == mode:
                if (same_year and same_month and same_day):
                    result.append(event)
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
