import praw
import sqlite3
import time

from enum import Enum

class ContentType(Enum):
    POST = 'post'
    COMMENT = 'comment'
    REPLY = 'reply'

class PostSortingOrder(Enum):
    #The algorithm being confidential, we cannot reproduce it from our db, so right now, top = hot, rising = new when fetching from db
    NEW = 'new'
    TOP = 'top'
    HOT = 'hot'
    CONTROVERSIAL = 'controversial'
    RISING = 'rising'

class CommentSortingOrder(Enum):
    NEW = 'new'
    TOP = 'top'
    BEST = 'best'
    CONTROVERSIAL = 'controversial'
    OLD = 'old'
    #Qna?

class Query:
    def __init__(self, upperLevelId, sortingOrder, numberOfItems, date):
        self.upperLevelId = str(upperLevelId) #subreddit or post from which we query the posts/comments
        self.sortingOrder = sortingOrder
        self.numberOfItems = int(numberOfItems)
        self.date = int(date) #date of the query, so we can evaluate how stale the data is. In seconds since the epoch

class Content:
    #TODO: add json serialization (Look at json.JSONEncoder) to encode/decode
    #Question: Do we want the permalink as well?
    def __init__(self, id, upperLevelId, score, author, title, content, parent, url, date, type):
        self.id = str(id) #id of the submission
        self.upperLevelId = str(upperLevelId) #either the subreddit of a post or the post of a comment
        self.score = int(score) #score of the submission
        self.author = str(author) #author of the submission
        self.title = str(title) #only for posts, empty string for comments
        self.content = str(content) #either the body of a comment or the selftext of a post
        self.parent = str(parent) #parent comment, empty if post, sub id if root comment
        self.url = str(url) #url to media or comment section for post, empty for comment
        self.creation_date = int(date) #creation date of the submission
        self.type = type #ContentType.POST or ContentType.COMMENT

def parseDbSelectToContent(row):
    if row[9]:  #By convention we save comments with boolean 1 and posts with boolean 0
        return Content(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],ContentType.COMMENT)
    else:
        return Content(row[0],row[1],row[2],row[3],row[4],row[5],row[6],row[7],row[8],ContentType.POST)

def loadRedditObj():
    userAgent = "python:decentralizedRedditProject:0.0 (by /u/buprojectaccount )"
    try:
        return praw.Reddit(client_id='NOElzEMDmrk2-Q',
                         client_secret='V-2RNfaQ5ryNEIbJZ8PXe1XSu-M',
                         user_agent=userAgent)
    except:
        return None

def loadSubredditPosts(reddit, subreddit, numberOfPosts, sorting, dbName):
    #If reddit is reachable:
    sortSwitcher = {
        PostSortingOrder.NEW:reddit.subreddit(subreddit).new(limit=numberOfPosts),
        PostSortingOrder.TOP:reddit.subreddit(subreddit).top(limit=numberOfPosts),
        PostSortingOrder.HOT:reddit.subreddit(subreddit).hot(limit=numberOfPosts),
        PostSortingOrder.CONTROVERSIAL:reddit.subreddit(subreddit).controversial(limit=numberOfPosts),
        PostSortingOrder.RISING:reddit.subreddit(subreddit).rising(limit=numberOfPosts),
    }

    posts = sortSwitcher[sorting]
    query = Query(subreddit, sorting, numberOfPosts, time.time())
    formatedPosts = []
    for post in posts:
        formatedPosts.append(Content(post.id, post.subreddit, post.score, post.author, post.title, post.selftext, "", post.url, post.created_utc, ContentType.POST))

    saveSubmissionToDb(formatedPosts, query, dbName)

    return formatedPosts

def loadPostComments(reddit, post, numberOfComments, sorting, dbName):
    #If reddit is reachable:
    sub = reddit.submission(id=post)
    sub.comment_sort = sorting.value
    #sub.comments.replace_more(limit=0)
    comments = sub.comments.list()[:int(numberOfComments)]
    query = Query(post, sorting, numberOfComments, time.time())
    formatedComments = []
    for com in comments:
        #We need to filter the 'more comments' stuff:
        if str(type(com)) == "<class 'praw.models.reddit.comment.Comment'>":
            post = reddit.comment(com)
            formatedComments.append(Content(post.id, post.link_id, post.score, post.author, "", post.body, post.parent_id, "", post.created_utc, ContentType.COMMENT))

    saveSubmissionToDb(formatedComments, query, dbName)

    return formatedComments

def loadCommentReplies(reddit, comment, numberOfComments, sorting, dbName):
    pass

def getQueryDate(upperLevelId, sorting, numberOfItems, dbName):
    recordTableName = 'queries'

    #Connection to database
    conn = sqlite3.connect(dbName)
    c = conn.cursor()
    print("Connected to local database: " + dbName)

    c.execute('''SELECT name FROM sqlite_master WHERE type='table' AND name='queries';''')
    if c.fetchone() == None:
        conn.close()
        return 0
    c.execute('''SELECT * FROM queries WHERE upperLevelId = ? AND sorting = ? AND numberOfItems >= ?;''', (upperLevelId, sorting.value, numberOfItems))
    query = c.fetchone()
    if query == None:
        conn.close()
        return 0
    else:
        #the third element of the tuple is the date
        conn.close()
        return query[3]

def getSubmissionsFromDb(upperLevelId, sorting, numberOfItems, dbName):
    subTableName = 'submissions'
    #Connection to database
    conn = sqlite3.connect(dbName)
    c = conn.cursor()
    print("Connected to local database: " + dbName)

    #Verification that submissions table exists
    c.execute('''SELECT name FROM sqlite_master WHERE type='table' AND name='submissions';''')
    if c.fetchone() == None:
        return []

    subs = []
    sortSwitcher = {
        PostSortingOrder.NEW:'SELECT * FROM submissions WHERE upperLevelId LIKE ? ORDER BY creation_date ASC LIMIT ?;',
        PostSortingOrder.TOP:'SELECT * FROM submissions WHERE upperLevelId LIKE ? ORDER BY score DESC LIMIT ?;',
        PostSortingOrder.HOT:'SELECT * FROM submissions WHERE upperLevelId LIKE ? ORDER BY score DESC LIMIT ?;',
        PostSortingOrder.CONTROVERSIAL:'SELECT * FROM submissions WHERE upperLevelId LIKE ? ORDER BY score ASC LIMIT ?;',
        PostSortingOrder.RISING:'SELECT * FROM submissions WHERE upperLevelId LIKE ? ORDER BY creation_date ASC LIMIT ?;',
        CommentSortingOrder.NEW:'SELECT * FROM submissions WHERE upperLevelId LIKE ? ORDER BY creation_date DESC LIMIT ?;',
        CommentSortingOrder.TOP:'SELECT * FROM submissions WHERE upperLevelId LIKE ? ORDER BY score DESC LIMIT ?;',
        CommentSortingOrder.OLD:'SELECT * FROM submissions WHERE upperLevelId LIKE ? ORDER BY creation_date DESC LIMIT ?;',
        CommentSortingOrder.BEST:'SELECT * FROM submissions WHERE upperLevelId LIKE ? ORDER BY score DESC LIMIT ?;',
    }
    for row in c.execute(sortSwitcher[sorting], ('%' if upperLevelId == 'all' else "%" + upperLevelId, numberOfItems)):
        subs.append(parseDbSelectToContent(row))
    return subs

def saveSubmissionToDb(submissions, query, dbName):
    #Right now those names are hardcoded in the queries but it may be better to use these variables
    subTableName = 'submissions'
    recordTableName = 'queries'

    #Connection to database
    conn = sqlite3.connect(dbName)
    c = conn.cursor()
    print("Connected to local database: " + dbName)

    #Verification that both submissions and queries tables exist, creating them if not
    c.execute('''SELECT name FROM sqlite_master WHERE type='table' AND name='submissions';''')
    if c.fetchone() == None:
        c.execute('''CREATE TABLE submissions
        (id text unique, upperLevelId text, score integer, author text, title text, content text, parent text, url text, creation_date integer, type integer)
        ;''')
        conn.commit()
    c.execute('''SELECT name FROM sqlite_master WHERE type='table' AND name='queries';''')
    if c.fetchone() == None:
        c.execute('''CREATE TABLE queries
        (upperLevelId text, sorting text, numberOfItems integer, date integer, PRIMARY KEY (upperLevelId, sorting))
        ;''')
        conn.commit()

    #Insertion of posts/comments to submissions
    cleanedSubs = []
    for sub in submissions:
        if sub.type == ContentType.POST:
            cleanedSubs.append((sub.id, sub.upperLevelId, sub.score, sub.author, sub.title, sub.content, '', sub.url, sub.creation_date, 0))
        else:
            cleanedSubs.append((sub.id, sub.upperLevelId, sub.score, sub.author, '', sub.content, sub.parent, '', sub.creation_date, 1))
    c.executemany('INSERT OR REPLACE INTO submissions VALUES (?,?,?,?,?,?,?,?,?,?)', cleanedSubs)

    #Insertion of query to queries
    queryToInsert = (query.upperLevelId, query.sortingOrder.value, query.numberOfItems, query.date)
    c.execute('INSERT OR REPLACE INTO queries VALUES (?,?,?,?)', queryToInsert)

    #committing insertions
    conn.commit()

    #Debug
    #for row in c.execute('''SELECT * FROM submissions;'''):
    #    print(row)

    #Closing Connection
    conn.close()
    print("Database connection closed.")
