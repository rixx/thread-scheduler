"""
This tool helps you schedule Twitter threads.

Each thread is its own JSON file. Run this tool like this:

    python thread-scheduler.py path/to/file [--check] [--one-off]

The JSON file will be updated by this script. It looks like this:

    {
        "tweets": [
            {
                "text": "…",
                "media": "path/to/pic/or/video"
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
from pathlib import Path

import dateutil.parser
import tweepy

from settings import ACCESS_TOKEN_KEY, ACCESS_TOKEN_SECRET, API_KEY, API_SECRET


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
                "text": tweet.get("text", ""),
                "sent": dateutil.parser.parse(tweet["sent"])
                if tweet.get("sent")
                else None,
                "offset": int(tweet.get("offset", 0)),
                "twitter_id": tweet.get("twitter_id"),
                "media": tweet.get("media"),
            }
            for tweet in config["tweets"]
        ]

    def check(self):
        last_tweet = None
        for tweet in self.tweets:
            text = tweet["text"]
            media = tweet["media"]
            if media and not Path(media).is_file():
                raise Exception(f"Media file at {media} does not exist.")
            if len(text) > 280:
                raise Exception(
                    f"This tweet is {len(text)} characters long. That's {len(text) - 280} too many: "
                    + text
                )
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

    def analyze(self):
        current_time = self.start
        for tweet in self.tweets:
            current_time += dt.timedelta(seconds=tweet.get("offset", 0))
            print(
                f"{current_time.strftime('%Y-%m-%d %H:%M:%S')}: Sending tweet ({len(tweet['text'])}/280)"
            )
            print_tweet(tweet["text"], tweet["media"])
        print("Done!")


def print_tweet(text, media):
    print_lines = []
    media_text = "* with media link"
    lines = text.split("\n")
    text_width = 50
    buffer_width = text_width + 2
    for line in lines:
        print_lines += textwrap.wrap(line, text_width)
    print("┏" + "━" * buffer_width + "┓")
    print("┃" + " " * buffer_width + "┃")
    for line in print_lines:
        print("┃ " + line.ljust(text_width) + " ┃")
    if media:
        print("┃ " + media_text.ljust(text_width) + " ┃")
    print("┃" + " " * buffer_width + "┃")
    print("┗" + "━" * buffer_width + "┛")


def main():
    path = sys.argv[1]
    thread = Thread(path)
    check = "--check" in sys.argv
    one_off = "--one-off" in sys.argv
    no_sleep = "--no-sleep" in sys.argv
    analyze = "--analyze" in sys.argv

    if analyze:
        thread.analyze()
        return

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
            if check or no_sleep:
                print(
                    f"Would sleep for {sleep_minutes} minutes, {sleep_seconds} seconds, then post:"
                )
                print_tweet(tweet["text"], tweet["media"])
                return
            print(f"Will sleep for {sleep_minutes} minutes, {sleep_seconds} seconds.")
            time.sleep(sleep_duration)
        if check:
            print("Would post this tweet:")
            print_tweet(tweet["text"], tweet["media"])
            return
        if tweet["media"]:
            result = api.update_with_media(
                tweet["media"], tweet["text"], in_reply_to_status_id=twitter_id
            )
        else:
            result = api.update_status(tweet["text"], in_reply_to_status_id=twitter_id)
        tweet["twitter_id"] = result.id
        tweet["sent"] = now
        thread.save()
        print("Sent out a tweet:")
        print_tweet(result.text, None)
        if one_off:
            return
    print("All tweets have been sent!")


if __name__ == "__main__":
    main()
