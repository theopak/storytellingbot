#!/usr/bin/python3
# coding: utf-8


from __future__ import print_function
from localsettings import USERNAME, PASSWORD
import sqlite3
from pprint import pprint
import praw
import time
import requests
from random import randint, choice
import re
from Extrapolate import Extrapolate


class Storytellingbot(object):
    """
    Storytellingbot
    COGS-4640/CSCI-4977 Intelligent Virtual Agent
    https://github.com/theopak/storytellingbot
    https://github.com/reddit/reddit/wiki/API#rules
    """

    e = Extrapolate.Extrapolate()
    metaText = '\n\n---\n[^about ^this ^bot](/r/storytellingbottests/wiki/index)'

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
        query = '''
            CREATE TABLE IF NOT EXISTS outbox(
                number      integer PRIMARY KEY,-- our unique record identifier
                sent        datetime,           -- 0 if not sent, otherwise timestamp
                keyword     text,               -- keyword that was matched
                id          text,               -- reddit id (hash) of matched comment
                parentId    text,               -- reddit id (hash) of parent comment
                linkUrl     text,               -- permalink of the Submission
                seed        integer,            -- story ID that seeded the response
                body        text,               -- plaintext body of matched comment
                response    text,               -- plaintext body to post as reply
                FOREIGN KEY(seed) REFERENCES stories(id)
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
            # if number_of_rows == 0:
            #     sample_sentences = ['Once upon a time, there was a story.',
            #                         'And then a plot occurred.',
            #                         'The end.']
            #     bot.add_story('title', 'source', sample_sentences)
            #     if DEBUG:
            #         print('[INFO] Populated sample story')

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
        self.cur.execute('SELECT * FROM outbox WHERE id=?', (id,))
        result = self.cur.fetchone()
        # if DEBUG: print('[INFO] Storytellingbot.queue_contains(' + id + '):\n\t', result)
        return True if result else False

    def find_keyword(self, text):
        """
        Return the first match found in the input text, or otherwise None.
        """
        self.cur.execute("SELECT * FROM keywords WHERE instr(?, word) > 0", (text,))
        result = self.cur.fetchone()
        # if DEBUG: print('[INFO] Storytellingbot.find_keyword(' + text + '):\n\t', result)
        return result[0] if result else None

    def enqueue_response(self, comment, response, keyword, story_id=0):
        """
        Add the given comment and response to the outbox, ready to send.
        """
        if not story_id:
            story_id = 0
        if DEBUG:
            print('[INFO] Storytellingbot.enqueue_response():',
                  '\n\tkeyword:', keyword, ', id:', comment.id,
                  ', parent_id:', comment.parent_id, ', parent_url; [...]',
                  ', seed:', story_id,
                  '\n\tbody:', comment.body, '\n\tresponse:', response)
            # pprint(vars(comment))
        self.cur.execute("INSERT INTO outbox VALUES (null, 0, ?, ?, ?, ?, ?, ?, ?)",
                         (keyword, comment.id, comment.parent_id, comment.link_url,
                          story_id, comment.body, str(response)))
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
            print('[INFO] Storytellingbot.add_story(): adding sentences…')

        # Insert into `sentences`
        begins = ends = None
        for s in sentences:
            self.cur.execute('INSERT into sentences VALUES (null, ?)', (s,))
            begins = min(self.cur.lastrowid, begins) if begins else self.cur.lastrowid
            ends = max(self.cur.lastrowid, ends) if ends else self.cur.lastrowid
            self.con.commit()

        # Insert foreign keys into `stories`
        if DEBUG:
            print('\tinserting…', title, source, begins, ends)
        self.cur.execute('INSERT into stories VALUES (null, ?, ?, ?, ?)',
                         (title, source, begins, ends))
        self.con.commit()

    def find_sentence_helper(self, candidates):
        """
        TODO: Replace this super hacky function.
        """
        # sql = ''
        # for sentence in candidates:
        #     sql = sql + '?, '
        # sql = '(' + sql[:-2] + ')'

        # First try to find a real match
        for sentence in candidates:
            # self.cur.execute('SELECT id, sentence FROM sentences WHERE sentence LIKE ANY ' + sql, (candidates,))
            self.cur.execute('SELECT id, sentence FROM sentences WHERE sentence LIKE ?',
                             ('%' + sentence + '%',))
            match = self.cur.fetchone()
            if not (match is None):
                return match

        # Otherwise, guess at random
        self.cur.execute('SELECT id, sentence FROM sentences ORDER BY random() LIMIT 1')
        match = self.cur.fetchone()
        return match

    def find_sentence(self, candidates):
        # find the first sentence that matches a candidate
        if DEBUG:
            print('[INFO] Storytellingbot.find_sentence() similar to one of:', len(candidates))
            # for i, s in enumerate(candidates):
            #     print('\t' + str(i) + '.', re.sub(r'^(.{70}).*(.{5})$', '\g<1>…\g<2>', s))
        sentence_id, sentence = self.find_sentence_helper(candidates)
        if DEBUG:
            print('\tresult: using', sentence_id, ':', sentence)
            # input('!!!!!!!!!!!!!!!')

        # correlate sentence ID to story ID
        self.cur.execute('SELECT id, ends FROM stories WHERE begins<=? and ends>=?',
                         (sentence_id, sentence_id))
        result = self.cur.fetchone()
        if result:
            seed, ends = result
            self.cur.execute('SELECT sentence FROM sentences WHERE id>? and id<=? LIMIT 2',
                             (sentence_id, ends))
            next_sentences = self.cur.fetchall()
            for s in next_sentences:
                sentence = sentence + ' ' + s[0]
        return seed, sentence

    def build_queue(self, subreddit='all'):
        """
        Build a work queue.
        TODO(@theopak): Enqueue responses to replies to responses, regardless
                        of whether they contain any keywords.
        TODO(@theopak): Separate response generation into a separate thread.
        """
        dtext = '[INFO] Storytellingbot.build_queue()\n'
        comments = self.reddit.get_comments(subreddit)
        for comment in comments:
            if self.queue_contains(comment.id):
                # if DEBUG:
                #     print(dtext, '\tcomment', comment.id, 'is already enqueued')
                continue
            if comment.author == self.reddit.user:
                # if DEBUG:
                #     print(dtext, '\tcomment', comment.id, 'is the bot\'s own comment')
                continue
            first_matched_keyword = self.find_keyword(comment.body)
            if first_matched_keyword is None:
                # if DEBUG:
                #     print(dtext, '\tcomment', comment.id, 'contains no keywords')
                continue
            # Else, queue a response
            if DEBUG:
                print(dtext, '\tcomment_id:', comment.id, 'first_matched_keyword:', first_matched_keyword)
            # response = self.e.extrapolate(comment.body, self.get_all_stories())
            # response = self.e.extrapolate(comment.body)
            # nearest_match = self.get_story()
            # nearest_match_sentence = choice(nearest_match['sentences'])[0].rstrip()

            # nearest_match_sentence = find_sentence(candidates, nearest_match['sentences'])
            candidates = self.e.extrapolate(comment.body)
            matched_seed, matched_sentence = self.find_sentence(candidates)
            if DEBUG:
                print('\t\tmatch', matched_seed, ':', matched_sentence)
            response = self.e.transform(comment.body, matched_sentence)
            if DEBUG:
                print('\t\tresponse:', response)
            self.enqueue_response(comment, response, first_matched_keyword, matched_seed)

    def build_citation(self, story_id):
        """
        Generate a Markdown-formatted citation of the given story.
        """
        self.cur.execute('SELECT title, source FROM stories WHERE id=?', (story_id,))
        result = self.cur.fetchone()
        if result:
            title, source = result
            out = '| this comment was algorithmically generated based on ' + \
                  title + ' via ' + source
            return '^' + out.replace(' ', ' ^')
        return ''

    def send_one(self):
        """
        Send the oldest comment in the queue and mark it as sent.
        Return False if all comments are sent or if send is unsuccessful.
        """

        # Get the oldest unsent comment from the queue
        self.cur.execute('SELECT id, linkUrl, seed, response FROM outbox WHERE sent=0 LIMIT 1')
        item = self.cur.fetchone()
        if item is None:
            # if DEBUG:
            #     print('[INFO] Storytellingbot.send_one(): all items sent')
            return False
        id, linkUrl, seed, response = item
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
            footer = self.metaText + ' ' + self.build_citation(seed)
            reply = submission.comments[0].reply(response + footer)
            self.mark_sent(id)
            print('[INFO] Storytellingbot.send_one(): sent response to', id,
                  '\n\tresponse:', response)
            return True
            pass
        except requests.exceptions.HTTPError as e:
            print('[ERROR] Storytellingbot.send_one():', e)
            self.mark_sent(id)
            pass
        else:
            # raise NameError('could not send response')
            pass
        return False

    def run(self):
        """
        Blocking. Requires that the user is logged in.
        Periodically check for new comments, search comments for matches,
        enqueue responses to be posted, and then post them as the Reddit API
        rate limit allows so.
        TODO: pass a loop iteration if the bot cannot connect to reddit.
        """
        print('Running bot at maximum limits auto-enforced by API wrapper...')
        while True:
            try:
                self.build_queue(subreddit='all')
                pass
            except Exception as e:
                print('[ERROR] Storytellingbot.build_queue():', e)
                raise e

            available = True
            while available:
                available = self.send_one()

            # Reddit enforces rate limits.
            # Accounts need karma.
            # print('[INFO] main(): Sleeping for 10 minutes…')
            # time.sleep(600)


def main():
    """
    Login as the bot using the username and password from `localsettings.py`.
    Use `Storytellingbot.run()` to run the bot indefinitely.
    """
    bot = Storytellingbot(USERNAME, PASSWORD)
    bot.run()

    # Populate db
    # harry_potter_keywords = ['wizard', 'magic', 'story', 'bot', 'karma']
    # bot.add_keywords(harry_potter_keywords)
    if False:
        harry_potter_keywords = ['Harry Potter']
        bot.add_keywords(harry_potter_keywords)
        with open('Harry Potter and the Sorcerer\'s Stone - J.K. Rowling.txt') as f:
            bot.add_story('Harry Potter and the Sorcerer\'s Stone, by J. K. Rowling',
                          'a pirated pdf converted to txt',
                          f.readlines())
        with open('Harry Potter and the Chamber of Secrets - J.K. Rowling.txt') as f:
            bot.add_story('Harry Potter and the Chamber of Secrets, by J. K. Rowling',
                          'a pirated pdf converted to txt',
                          f.readlines())
        with open('Harry Potter and the Prisoner of Azkaban - J.K. Rowling.txt') as f:
            bot.add_story('Harry Potter and the Prisoner of Azkaban, by J. K. Rowling',
                          'a pirated pdf converted to txt',
                          f.readlines())
        with open('Harry Potter and the Goblet of Fire - J.K. Rowling.txt') as f:
            bot.add_story('Harry Potter and the Goblet of Fire, by J. K. Rowling',
                          'a pirated pdf converted to txt',
                          f.readlines())
        with open('Harry Potter and the Order of the Phoenix - J.K. Rowling.txt') as f:
            bot.add_story('Harry Potter and the Order of the Phoenix, by J. K. Rowling',
                          'a pirated pdf converted to txt',
                          f.readlines())
        with open('Harry Potter and the Half-Blood Prince - J.K. Rowling.txt') as f:
            bot.add_story('Harry Potter and the Half-Blood Prince, by J. K. Rowling',
                          'a pirated pdf converted to txt',
                          f.readlines())
        with open('Harry Potter and the Deathly Hallows - J.K. Rowling.txt') as f:
            bot.add_story('Harry Potter and the Deathly Hallows, by J. K. Rowling',
                          'a pirated pdf converted to txt',
                          f.readlines())


if __name__ == '__main__':
    DEBUG = 1
    main()
