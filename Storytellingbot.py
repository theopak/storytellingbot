#!/usr/bin/python3
# coding: utf-8


from __future__ import print_function
from localsettings import USERNAME, PASSWORD
import sqlite3
from pprint import pprint
import praw
import time
from random import randint
from Extrapolate import Extrapolate


class Storytellingbot(object):
    """
    Storytellingbot
    COGS-4640/CSCI-4977 Intelligent Virtual Agent
    https://github.com/theopak/storytellingbot
    https://github.com/reddit/reddit/wiki/API#rules
    """

    e = Extrapolate.Extrapolate()

    def __init__(self, username, password, db_file='local.db',
                 user_agent='Python:storytellingbot:v0.0.0 (by /u/theopakalyse)'):
        """
        Init data layer.
        Login to Reddit. OAuth2 bots gave a rate limit twice as high.
        """
        if DEBUG:
            print('[INFO] Storytellingbot.__init__() called...')
        self.con = sqlite3.connect(db_file)
        self.cur = self.con.cursor()
        self.setup()
        self.reddit = praw.Reddit(user_agent)
        self.reddit.login(username, password)
        if DEBUG:
            print('[INFO] Logged in as', username)

    def __del__(self):
        """
        Remove any locks on the data layer.
        """
        if DEBUG:
            print('[INFO] Storytellingbot.__del__() called...')
        self.con.close()
        if DEBUG:
            print('\tClosed db connection.')

    def setup(self):
        """
        Initialize bot implementation. This only needs to happen the first time
        but the function should be safe to call at any point.
        TODO(@theopak): Create a test subreddit if it does not exist.
        """
        query = '''
            CREATE TABLE IF NOT EXISTS outbox(
                number      integer PRIMARY KEY,-- our unique record identifier
                sent        datetime,           -- 0 if not sent, otherwise timestamp
                keyword     text,               -- keyword that was matched
                id          text,               -- reddit id (hash) of matched comment
                parentId    text,               -- reddit id (hash) of parent comment
                linkUrl     text,               -- permalink of the Submission
                body        text,               -- plaintext body of matched comment
                response    text                -- plaintext body to post as reply
            );'''
        self.cur.execute(query)
        query = '''
            CREATE TABLE IF NOT EXISTS keywords(
                word        text UNIQUE         -- one word or phrase to search for
            );'''
        self.cur.execute(query)
        query = '''
            CREATE TABLE IF NOT EXISTS stories(
                id          integer PRIMARY KEY,-- our unique record identifier
                title       text,               -- plaintext story title
                source      text,               -- URL
                begins      integer,
                ends        integer,
                FOREIGN KEY(begins) REFERENCES sentences(id),
                FOREIGN KEY(ends) REFERENCES sentences(id)
            );'''
        self.cur.execute(query)
        query = '''
            CREATE TABLE IF NOT EXISTS sentences(
                id          integer PRIMARY KEY,-- references by stories
                sentence    text                -- one line
            );'''
        self.cur.execute(query)
        # query = '''CREATE INDEX storyindex ON sentences(id);'''
        # self.cur.execute(query)
        self.con.commit()
        if DEBUG:
            print('[INFO] Setup db tables')

        # Populate db
        if DEBUG:
            self.cur.execute("SELECT Count() FROM keywords")
            number_of_rows = self.cur.fetchone()[0]
            if number_of_rows == 0:
                sample_keywords = ['unique_keyword_20150416', 'virtualagent']
                self.add_keywords(sample_keywords)
                if DEBUG:
                    print('[INFO] Populated sample keywords')
            self.cur.execute("SELECT Count() FROM stories")
            number_of_rows = self.cur.fetchone()[0]
            if number_of_rows == 0:
                sample_sentences = ['Once upon a time, there was a story.',
                                    'And then a plot occurred.',
                                    'The end.']
                bot.add_story('title', 'source', sample_sentences)
                if DEBUG:
                    print('[INFO] Populated sample story')

    def add_keywords(self, keywords):
        if DEBUG:
            print('[INFO] Storytellingbot.add_keywords(): adding keywords to db:')
        for word in keywords:
            if DEBUG:
                print('\t', word)
            self.cur.execute('INSERT into keywords VALUES (?)', (word,))
            self.con.commit()

    def queue_contains(self, id):
        """
        Return True if the given comment id is in the queue.
        """
        self.cur.execute("SELECT * FROM outbox WHERE id=?", (id,))
        result = self.cur.fetchone()
        # if DEBUG: print('[INFO] Storytellingbot.queue_contains(' + id + '):\n\t', result)
        return True if result else False

    def search(self, text):
        """
        Return the first match found in the input text, or otherwise None.
        """
        self.cur.execute("SELECT * FROM keywords WHERE instr(?, word) > 0", (text,))
        result = self.cur.fetchone()
        # if DEBUG: print('[INFO] Storytellingbot.search(' + text + '):\n\t', result)
        return result[0] if result else None

    def enqueue_response(self, comment, response, keyword):
        """
        Add the given comment and response to the outbox, ready to send.
        """
        if DEBUG:
            print('[INFO] Storytellingbot.enqueue_response():',
                  '\n\tkeyword:', keyword, ', id:', comment.id,
                  ', parent_id:', comment.parent_id,
                  '\n\tbody:', comment.body, '\n\tresponse:', response)
            # pprint(vars(comment))
        self.cur.execute("INSERT INTO outbox VALUES (null, 0, ?, ?, ?, ?, ?, ?)",
                         (keyword, comment.id, comment.parent_id, comment.link_url, comment.body, str(response)))
        self.con.commit()

    def mark_sent(self, id):
        """
        Mark the given outbox item as sent. Use the given time.
        """
        self.cur.execute("UPDATE outbox SET sent=datetime('now') WHERE id=?", (id,))
        self.con.commit()

    def get_story_count(self):
        """
        Return the number of stories in the data store.
        """
        self.cur.execute("SELECT Count() FROM stories")
        number_of_rows = self.cur.fetchone()[0]
        return number_of_rows

    def get_story(self, id=None):
        """
        Return a story from the data store.
        """
        # Count the number of stories in the db
        # TODO: Finish this. Right now it simply grabs a random story.
        self.cur.execute('SELECT Count() FROM stories')
        res = self.cur.fetchone()
        count = res[0] if res else None
        if not count or not id or (id < 1) or (id > count):
            id = randint(1, count)

        # Get all sentences from the story
        if DEBUG:
            print('[INFO] get_story()', id, 'out of', count)
        self.cur.execute('SELECT id, title, source, begins, ends FROM stories')
        stories_result = self.cur.fetchone()
        id, title, source, begins, ends = stories_result
        self.cur.execute('SELECT sentence FROM sentences WHERE id >= ? and id <= ?',
                         (begins, ends))
        result = self.cur.fetchall()

        # Return a dict
        return {'id': id,
                'title': title,
                'source': source,
                'sentences': result}

    def get_all_stories(self):
        """
        Return all stories from the data store.
        """
        self.cur.execute('SELECT content FROM stories')
        result = self.cur.fetchall()
        pprint(result)
        return [[s.encode('utf8') for s in t] for t in result] if result else None

    def add_story(self, title, source, sentences):
        if DEBUG:
            print('[INFO] Storytellingbot.add_story(): adding sentences...')

        # Insert into `sentences`
        begins = ends = None
        for s in sentences:
            self.cur.execute('INSERT into sentences VALUES (null, ?)', (s,))
            begins = min(self.cur.lastrowid, begins) if begins else self.cur.lastrowid
            ends = max(self.cur.lastrowid, ends) if ends else self.cur.lastrowid
            self.con.commit()

        # Insert foreign keys into `stories`
        if DEBUG:
            print('\tinserting...', title, source, begins, ends)
        self.cur.execute('INSERT into stories VALUES (null, ?, ?, ?, ?)',
                         (title, source, begins, ends))
        self.con.commit()

    def build_queue(self, subreddit='storytellingbottests'):
        """
        Build a work queue.
        TODO(@theopak): Enqueue responses to replies to responses, regardless
                        of whether they contain any keywords.
        """
        if DEBUG:
            print('[INFO] Storytellingbot.build_queue()')
        comments = self.reddit.get_comments(subreddit)
        for comment in comments:
            if self.queue_contains(comment.id):
                if DEBUG:
                    print('\tcomment', comment.id, 'is already enqueued')
                continue
            if comment.author is self.reddit.user:
                if DEBUG:
                    print('\tcomment', comment.id, 'is the bot\'s own comment')
                continue
            first_matched_keyword = self.search(comment.body)
            if first_matched_keyword is None:
                if DEBUG:
                    print('\tcomment', comment.id, 'contains no keywords')
                continue
            # Else, queue a response
            if DEBUG:
                print('\tcomment_id', comment.id, 'matched', first_matched_keyword)
            # response = self.e.extrapolate(comment.body, self.get_all_stories())
            response = self.e.extrapolate(comment.body)
            self.enqueue_response(comment, response, first_matched_keyword)

    def send_one(self):
        """
        Send the oldest comment in the queue and mark it as sent.
        Return False if all comments are sent or if send is unsuccessful.
        """

        # Get the oldest unsent comment from the queue
        self.cur.execute("SELECT id, linkUrl, response FROM outbox WHERE sent=0 LIMIT 1")
        item = self.cur.fetchone()
        if item is None:
            if DEBUG:
                print('[INFO] Storytellingbot.send_one(): all items sent')
            return False
        id, linkUrl, response = item
        if response is '':
            if DEBUG:
                print('[INFO] Storytellingbot.send_one(): can\'t send', id,
                      'because there is no prepared response')
            return False

        # Debug
        if DEBUG:
            print('\t', id, linkUrl, response)

        # Load the related comment object from Reddit (if it still exists)
        # and then post the outbox item as a reply to the Reddit comment.
        try:
            submission = self.reddit.get_submission(linkUrl + id)
            reply = submission.comments[0].reply(response)
            self.mark_sent(id)
            print('[INFO] Storytellingbot.send_one(): sent response to', id, ':', reply)
            return True
            pass
        except Exception as e:
            print('[ERROR] Storytellingbot.build_queue():', e)
            raise e
        return False

    def run(self):
        """
        Blocking. Requires that the user is logged in.
        Periodically check for new comments, search comments for matches,
        enqueue responses to be posted, and then post them as the Reddit API
        rate limit allows so.
        TODO: pass a loop iteration if the bot cannot connect to reddit.
        """
        while True:
            try:
                self.build_queue()
                pass
            except Exception as e:
                print('[ERROR] Storytellingbot.build_queue():', e)
                raise e

            available = True
            while available:
                available = self.send_one()

            # Reddit enforces rate limits.
            # Accounts need karma.
            print('[INFO] main(): Sleeping for 10 minutes…')
            time.sleep(600)


def main():
    """
    Login as the bot using the username and password from `localsettings.py`.
    Use `Storytellingbot.run()` to run the bot indefinitely.
    """
    bot = Storytellingbot(USERNAME, PASSWORD)
    # bot.run()
    r = bot.get_story()
    print(r)

    # Add stories
    # with open('Harry Potter and the Goblet of Fire - J.K. Rowling.txt') as f:
    #     bot.add_story('Harry Potter 4', 'pdf to txt', f.readlines())


if __name__ == '__main__':
    DEBUG = 1
    main()
