"""
This tool helps you schedule Twitter threads.

Each thread is its own JSON file. Run this tool like this:

    python thread-scheduler.py path/to/file [--check] [--one-off]

The JSON file will be updated by this script. It looks like this:

    {
        "tweets": [
            {
                "text": "…",
            },
            {
                "text": "…",
                "offset": 60  // Seconds in between this and the previous tweet
            },
        ],
        "start": "2019-08-13T20:00:00"
    }

Put a settings.py next to this file with your API_KEY, API_SECRET,
ACCESS_TOKEN_KEY and ACCESS_TOKEN_SECRET.
"""
import datetime as dt
import json
import sys
import textwrap
import time

import dateutil.parser
import tweepy

from settings import API_KEY, API_SECRET, ACCESS_TOKEN_KEY, ACCESS_TOKEN_SECRET


def json_datetime(value):
    if isinstance(value, dt.datetime):
        return value.isoformat()
    raise ValueError


class Thread:
    def __init__(self, path):
        self.path = path
        self.load()
        self.check()

    def load(self):
        with open(self.path) as fp:
            config = json.load(fp)
        self.start = dateutil.parser.parse(config["start"])
        self.tweets = [
            {
                "text": tweet["text"],
                "sent": dateutil.parser.parse(tweet["sent"])
                if tweet.get("sent")
                else None,
                "offset": tweet.get("offset", 0),
                "twitter_id": tweet.get("twitter_id"),
            }
            for tweet in config["tweets"]
        ]

    def check(self):
        last_tweet = None
        for tweet in self.tweets:
            text = tweet["text"]
            if len(text) > 280:
                raise Exception("Tweet cannot be longer than 280 characters: " + text)
            if text == last_tweet:
                raise Exception(
                    "Twitter will probably prevent two same tweets in a row: " + text
                )
            last_tweet = text

    def save(self):
        with open(self.path, "w") as fp:
            text = json.dumps(  # We use dumps instead of dump to prevent file corruption
                {"start": self.start, "tweets": self.tweets},
                default=json_datetime,
                indent=4,
            )
            fp.write(text)

    def get_to_be_sent(self):
        last_sent = None
        last_id = None
        for tweet in self.tweets:
            if tweet["sent"]:
                last_sent = tweet["sent"]
                last_id = tweet["twitter_id"]
                continue
            return (
                tweet,
                (last_sent or self.start) + dt.timedelta(seconds=tweet["offset"]),
                last_id,
            )


def print_tweet(text):
    print_lines = []
    lines = text.split("\n")
    text_width = 50
    buffer_width = text_width + 2
    for line in lines:
        print_lines += textwrap.wrap(line, text_width)
    print("┏" + "━" * buffer_width + "┓")
    print("┃" + " " * buffer_width + "┃")
    for line in print_lines:
        print("┃ " + line.ljust(text_width) + " ┃")
    print("┃" + " " * buffer_width + "┃")
    print("┗" + "━" * buffer_width + "┛")


def main():
    path = sys.argv[1]
    thread = Thread(path)
    check = "--check" in sys.argv
    one_off = "--one-off" in sys.argv
    if not check:
        auth = tweepy.OAuthHandler(API_KEY, API_SECRET)
        auth.set_access_token(ACCESS_TOKEN_KEY, ACCESS_TOKEN_SECRET)
        api = tweepy.API(auth)

    while thread.get_to_be_sent():
        tweet, timestamp, twitter_id = thread.get_to_be_sent()
        now = dt.datetime.now()
        if timestamp and timestamp > now:
            sleep_duration = int((timestamp - now).total_seconds())
            sleep_minutes = int(sleep_duration / 60)
            sleep_seconds = int(sleep_duration % 60)
            if check:
                print(
                    f"Would sleep for {sleep_minutes} minutes, {sleep_seconds} seconds, then post:"
                )
                print_tweet(tweet["text"])
                return
            print(f"Will sleep for {sleep_minutes} minutes, {sleep_seconds} seconds.")
            time.sleep(sleep_duration)
        if check:
            print("Would post this tweet:")
            print_tweet(tweet["text"])
            return
        result = api.update_status(tweet["text"], in_reply_to_status_id=twitter_id)
        tweet["twitter_id"] = result.id
        tweet["sent"] = now
        thread.save()
        print("Sent out a tweet:")
        print_tweet(tweet["text"])
        if one_off:
            return
    print("All tweets have been sent!")


if __name__ == "__main__":
    main()
