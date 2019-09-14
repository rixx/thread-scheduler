# Thread Scheduler

No creative names for you, I'm afraid. This is a script to post pre-configured threads on Twitter.
You can schedule when to start the thread, and then a time offset for each tweet.
It also performs basic checks for tweet length and duplicate tweets.

You can run this script either once until the whole thread has been posted, or repeatedly, e.g. via cronjobs.
You'll provide a file with the tweets to be posted, which will then be updated by the script to reflect which tweet has
already been posted.

## Setup

To get set up, get yourself a virtualenv of any kind, and ``pip install -r requirements.txt``. (If this sounds like
magic to you, scroll all the way down.)

You'll need to [register an app](https://developers.twitter.com). This page has okay
[instructions](https://python-twitter.readthedocs.io/en/latest/getting_started.html).

Put a file called ``settings.py`` in this directory:

```python
API_KEY = "..."
API_SECRET = "..."
AUTH_TOKEN_KEY = "..."
AUTH_TOKEN_SECRET = "..."
```

## Tweets

You'll need one JSON file per thread. Please note that the "offset" key denotes the delay between the previous and
current tweet, and is a value in **seconds**. A file looks like this:

```json
{
  "start": "2019-09-14T20:00:00",
  "tweets": [
    {
      "text": "Something"
    },
    {
      "text": "Something",
      "offset": 60
    },
    {
      "text": "Tweet\nwith\nnewlines",
      "offset": 3
    }
  ]
}
```

The file will later be edited by the script to add sent timestamps and tweet IDs.

## Usage

Check what would happen if you were to run Thread Scheduler first:

```
python thread_scheduler.py tweets.json --check
```

Maybe post a single tweet first (useful if you want to run this via crontab):

```
python thread_scheduler.py tweets.json --one-off
```


If you choose to run your script via one-offs, you probably want to add the ``--no-sleep`` flag, too, to prevent the
script from hanging until the next tweet is due:

```
python thread_scheduler.py tweets.json --one-off --no-sleep
```

Or just leave the script running until the thread has been posted. Will provide print output, and save progress in the
JSON file, so that you can safely abort at any time:

```
python thread_scheduler.py tweets.json
```

## Detailed setup instructions

1. Open a terminal and make sure you have ``python3`` available.
2. Next, clone this repository: ``git clone git@github.com:rixx/thread-scheduler.git``.
3. Go into the newly cloned repository: ``cd thread-scheduler``
4. Start a virtual environment: ``python3 -m venv .venv``
5. Activate the virtual environment: ``source .venv/bin/activate``. **Repeat this step any time you want to use the
   thread scheduler**.
6. Install the dependencies: ``pip install -r requirements.txt``
