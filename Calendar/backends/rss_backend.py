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
        """Custom function to display longer text into multiple lines (wrapping)"""
        def multiline_text(text, max_width, font=default):
            lines = []
            if font.getsize(text)[0] <= max_width:
                lines.append(text)
            else:
                words = text.split(' ')
                i = 0
                while i < len(words):
                    line = ''
                    while i < len(words) and font.getsize(line + words[i])[0] <= max_width:
                        line = line + words[i] + " "
                        i += 1
                    if not line:
                        line = words[i]
                        i += 1
                    lines.append(line)
            return lines

        """Parse the RSS-feed titles and save them to a list"""
        rss_feed = []
        for feeds in rss_feeds:
            text = feedparser.parse(feeds)
            for posts in text.entries:
                rss_feed.append(posts.summary)#title

        """Shuffle the list to prevent displaying the same titles over and over"""
        random.shuffle(rss_feed)
        news = []

        """Remove all titles except the first 4 or 6,
        depenfing on how much space is available on the """
        if middle_section is 'Calendar' and len(cal) is 5 or middle_section is 'Agenda':
            del rss_feed[6:]

        if len(cal) is 6:
            del rss_feed[4:]

        """Split titles of the rss feeds into lines that can fit
        on the Calendar and add them to a list"""
        for title in range(len(rss_feeds)):
            news.append(multiline_text(rss_feed[title], 384))

        news = [j for i in news for j in i]

        """Display the split lines of the titles"""
        if middle_section is 'Calendar' and len(cal) is 5 or middle_section is 'Agenda':
            if len(news) > 6:
                del news[6:]
            for lines in range(len(news)):
                write_text(384, 25, news[lines], rss_places['line_'+str(lines+1)], alignment = 'left')

        if len(cal) is 6:
            if len(news) > 4:
                del news[4:]
            for lines in range(len(news)):
                write_text(384, 25, news[lines], rss_places['line_'+str(lines+3)], alignment = 'left')

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
