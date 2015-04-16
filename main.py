#!/usr/bin/python2.7
# coding: utf-8


"""
storytellingbot
COGS-4640/CSCI-4977 Intelligent Virtual Agent
Theo Pak <theopak@gmail.com>
Updated 2015-04-16
"""


from __future__ import print_function
from pprint import pprint
from nltk.tbl.demo import postag
import time, random
import praw
from Extrapolate import Extrapolate


def nltk_helloworld():
    """
    This function is an entirely useless proof-of-concept.
    """
    print("Running demo from nltk.tbl.demo.postag")
    postag(incremental_stats=True,
        separate_baseline_data=True,
        learning_curve_output="learningcurve.png")
    print("done")


def bodyContainsKeyword(body, keywords):
    """
    Returns a keyword if any word in the body matches a word from the keywrods set.
    """
    body_words = body.split()
    for word in body_words:
        if word in keywords:
            return word
    return ''


def commentObserver(username, password, content_file, subreddit='all', t=1800):
    """
    Connect to Reddit and get comments from the specified subreddit. If a
    comment meets the match conditions then reply to it with a response.
      - `outbox` is the set of matched comment IDs.
      - `content` is an ordered list of lines.
      - `t` is the amount of time in seconds to wait between cycles.
    """
    keywords = ['unique_keyword_20150416', 'keyword2', 'virtualagent', 'demo']
    outbox = set()
    content = []
    e = Extrapolate.Extrapolate()

    # Get content to reply with
    with open(content_file) as file:
        content = file.readlines()

    # Login
    user_agent = 'storytelling comment bot'
    r = praw.Reddit(user_agent)
    r.login(username, password)
    print('[INFO] Logged in as', username)

    # Build a work queue, and complete it
    while True:
        print('[INFO] Fetching new comments...')
        comments = r.get_comments('storytellingbottests')
        for comment in comments:
            match = bodyContainsKeyword(comment.body, keywords)
            if (match != '') and (comment.id not in outbox):
                print('[INFO] -- comment id', comment.id, 'matched on keyword', match)
                try:
                    # response = random.choice(content)
                    response = e.extrapolate(comment.body)
                    comment.reply(response)
                    outbox.add(comment.id)
                    pass
                except Exception, e:
                    raise e
                comment.reply("response")
                outbox.add(comment.id)

        # Redit enforces rate limits. It's better if your account has more karma.
        print('[INFO] Sleeping for 30 minutes to avoid rate limit...')
        time.sleep(t)


if __name__ == '__main__':
    commentObserver(content_file='alice-in-wonderland.txt',
        username='storytellingbot',
        password='password_changed_since_last_commit',
        subreddit='storytellingbottests')
