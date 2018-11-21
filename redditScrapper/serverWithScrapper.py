# Python 3 server example
# To launch the server, run python3 serverWithScrapper [port number]


from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import praw
import sys
from enum import Enum
import sqlite3

#TODO:  Add a query id to queries database, and make it a foreign key in the submissions
#       table, so we can check when a particular submission has been last updated.
#       This would be nice but at this moment it does not serve any real purpose in our project.
class ContentType(Enum):
    POST = 'post'
    COMMENT = 'comment'

class PostSortingOrder(Enum):
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
    def __init__(self, upperLevelId, sortingOrder, date):
        self.upperLevelId = str(upperLevelId) #subreddit or post from which we query the posts/comments
        self.sortingOrder = str(sortingOrder)
        self.date = int(date) #date of the query, so we can evaluate how stale the data is. In seconds since the epoch

class Content:
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

def loadRedditObj():
    userAgent = "python:decentralizedRedditProject:0.0 (by /u/buprojectaccount )"
    return praw.Reddit(client_id='NOElzEMDmrk2-Q',
                         client_secret='V-2RNfaQ5ryNEIbJZ8PXe1XSu-M',
                         user_agent=userAgent)

def loadSubredditPosts(reddit, subreddit, numberOfPosts, sorting):
    #If reddit is reachable:
    sortSwitcher = {
        PostSortingOrder.NEW:reddit.subreddit(subreddit).new(limit=numberOfPosts),
        PostSortingOrder.TOP:reddit.subreddit(subreddit).top(limit=numberOfPosts),
        PostSortingOrder.HOT:reddit.subreddit(subreddit).hot(limit=numberOfPosts),
        PostSortingOrder.CONTROVERSIAL:reddit.subreddit(subreddit).controversial(limit=numberOfPosts),
        PostSortingOrder.RISING:reddit.subreddit(subreddit).rising(limit=numberOfPosts),
    }

    posts = sortSwitcher[sorting]
    query = Query(subreddit, sorting,time.time())
    formatedPosts = []
    for post in posts:
        formatedPosts.append(Content(post.id, post.subreddit, post.score, post.author, post.title, post.selftext, "", post.url, post.created_utc, ContentType.POST))

    return formatedPosts, query

def loadPostComments(reddit, post, numberOfComments, sorting):
    #If reddit is reachable:
    sub = reddit.submission(id=post)
    sub.comment_sort = sorting
    #sub.comments.replace_more(limit=0)
    comments = sub.comments.list()[:numberOfComments]
    query = Query(post, sorting,time.time())
    formatedComments = []
    for com in comments:
        #We need to filter the 'more comments' stuff:
        if str(type(com)) == "<class 'praw.models.reddit.comment.Comment'>":
            post = reddit.comment(com)
            formatedComments.append(Content(post.id, post.link_id, post.score, post.author, "", post.body, post.parent_id, "", post.created_utc, ContentType.COMMENT))

    return formatedComments, query

def saveSubmissionToDb(submissions, query):
    dbName = hostName + '_' + str(serverPort) + '_localReddit' + '.db'
    #Right now those names are hardcoded in the queries but it may be better to use these variables
    subTableName = 'submission'
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
        (upperLevelId text, sorting text, date integer, PRIMARY KEY (upperLevelId, sorting))
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
    queryToInsert = (query.upperLevelId, query.sortingOrder, query.date)
    c.execute('INSERT OR REPLACE INTO queries VALUES (?,?,?)', queryToInsert)

    #committing insertions
    conn.commit()

    #Debug
    for row in c.execute('''SELECT upperLevelId FROM queries;'''):
        print(row)

    #Closing Connection
    conn.close()
    print("Database connection closed.")

hostName = "localhost"

if (len(sys.argv) > 1):
    serverPort = int(sys.argv[1])
else:
    serverPort = 8080 #Default port, can be changed

class MyServer(BaseHTTPRequestHandler):

    reddit = loadRedditObj()

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("<html><head><title>Local Reddit</title></head>", "utf-8"))
        self.wfile.write(bytes("<body>", "utf-8"))
        posts, query = loadSubredditPosts(self.reddit, 'all', 10, PostSortingOrder.TOP)
        saveSubmissionToDb(posts, query)
        for submission in posts:
            self.wfile.write(bytes("<p><a href=\"" + str(submission.url) + "\">" + str(submission.title) + "</a> ("+ "<a href=\"https://www.reddit.com/r/" + str(submission.parent) + "\">r/" + str(submission.parent) + "</a>" + ")</p>", "utf-8"))
        self.wfile.write(bytes("</body></html>", "utf-8"))

if __name__ == "__main__":
    webServer = HTTPServer((hostName, serverPort), MyServer)
    print("Server started http://%s:%s" % (hostName, serverPort))
    try:
        webServer.serve_forever()
    except KeyboardInterrupt:
        pass

    webServer.server_close()
    print("Server stopped.")
