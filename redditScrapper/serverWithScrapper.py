# Python 3 server example
# To launch the server, run python3 serverWithScrapper [port number]


from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import praw
import sys
from enum import Enum
import sqlite3

#TODO: fill loadPostComments and loadSubredditPosts. The idea is to have two cases, one if reddit.com is reachable
#      and one when it's not. In both cases, we try to get stuff from our own db first. Then if we do fetch data
#      remotely, we need to add them to the db.
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

    formatedPosts = []
    for post in posts:
        formatedPosts.append(Content(post.id, post.subreddit, post.score, post.author, post.title, post.selftext, "", post.url, post.created_utc, ContentType.POST))

    return formatedPosts

def loadPostComments(reddit, post, numberOfComments, sorting):
    #If reddit is reachable:
    sub = reddit.submission(id=post)
    sub.comment_sort = sorting
    #sub.comments.replace_more(limit=0)
    comments = sub.comments.list()[:numberOfComments]
    print(comments)
    formatedComments = []
    for com in comments:
        #We need to filter the 'more comments' stuff:
        if str(type(com)) == "<class 'praw.models.reddit.comment.Comment'>":
            post = reddit.comment(com)
            formatedComments.append(Content(post.id, post.link_id, post.score, post.author, "", post.body, post.parent_id, "", post.created_utc, ContentType.COMMENT))

    return formatedComments

def saveSubmissionToDb(submissions):
    dbName = hostName + '_' + str(serverPort) + '_localReddit' + '.db'
    tableName = 'submission'
    conn = sqlite3.connect(dbName)
    c = conn.cursor()
    print("Connected to local database: " + dbName)
    c.execute('''SELECT name FROM sqlite_master WHERE type='table' AND name='submissions';''')
    if c.fetchone() == None:
        c.execute('''CREATE TABLE submissions
        (id text unique, upperLevelId text, score integer, author text, title text, content text, parent text, url text, creation_date integer, type integer)
        ;''')
        conn.commit()
    cleanedSubs = []
    for sub in submissions:
        if sub.type == ContentType.POST:
            cleanedSubs.append((sub.id, sub.upperLevelId, sub.score, sub.author, sub.title, sub.content, '', sub.url, sub.creation_date, 0))
        else:
            cleanedSubs.append((sub.id, sub.upperLevelId, sub.score, sub.author, '', sub.content, sub.parent, '', sub.creation_date, 1))
    c.executemany('INSERT OR REPLACE INTO submissions VALUES (?,?,?,?,?,?,?,?,?,?)', cleanedSubs)
    conn.commit()
    for row in c.execute('''SELECT id FROM submissions;'''):
        print(row)
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
        posts = loadSubredditPosts(self.reddit, 'all', 10, PostSortingOrder.TOP)
        saveSubmissionToDb(posts)
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
