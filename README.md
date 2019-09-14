# Thread Scheduler

No creative names for you, I'm afraid. This is a script to post pre-configured threads on Twitter.
You can schedule when to start the thread, and then a time offset for each tweet.
It also performs basic checks for tweet length and duplicate tweets.

You can run this script either once until the whole thread is posted, or repeatedly, e.g. via cronjobs.
You'll provide a file with the tweets to be posted, which will then be updated by the script to reflect which tweet has
already been posted.

## Setup

To set it up, get yourself a virtualenv of any kind, and ``pip install -r requirements.txt``.

You'll need to [register an app](https://developers.twitter.com). This page has okay
[instructions](https://python-twitter.readthedocs.io/en/latest/getting_started.html).

Put a file called ``settings.py`` in this directory and put in your ``API_KEY``, ``API_SECRET``, ``AUTH_TOKEN_KEY`` and
``AUTH_TOKEN_SECRET``.

## Tweets

You'll need one JSON file per thread. A file looks like this:

```json
{
  "start": "2019-09-14T20:00:00",
  "tweets": [
    {
      "text": "Something"
    },
    {
      "text": "Something",
      "offset": 60  // Interval between the previous tweet and this one in seconds
    },
    {
      "text": "Tweet\nwith\nnewlines"
      "offset": 3
    }
  ]
}
```

The file will later be edited by Thread Scheduler – **please keep a backup copy**.

## Usage

Check what would happen if you were to run Thread Scheduler first:

```
python thread_scheduler.py tweets.json --check
```

Maybe post a single tweet first (useful if you want to run this via crontab):

```
python thread_scheduler.py tweets.json --one-off
```

Or just leave the script running until the thread has been posted. Will provide print output, and save progress in the
JSON file, so that you can safely abort at any time:

```
python thread_scheduler.py tweets.json
```
