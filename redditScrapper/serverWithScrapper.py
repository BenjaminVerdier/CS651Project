# Python 3 server example
# To launch the server, run python3 serverWithScrapper [port number]


from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import praw
import sys
from enum import Enum

#TODO: create a post class with: Id, subreddit, score, content, url
#TODO: create a comment class with: Id, post, score, content

#Or: do a general content class that can be a post or a comment with: Id, parent(subreddit/post), score, content, url

class ContentType(Enum):
    POST = 'post'
    COMMENT = 'comment'

class SortingOrder(Enum):
    NEW = 'new'
    TOP = 'top'
    HOT = 'hot'
    CONTROVERSIAL = 'controversial'
    RISING = 'rising'

class Content:
    def __init__(self, id, parent, score, content, url, type):
        self.id = id
        self.parent = parent
        self.score = score
        self.content = content
        self.url = url
        self.type = type

def loadRedditObj():
    userAgent = "python:decentralizedRedditProject:0.0 (by /u/buprojectaccount )"
    return praw.Reddit(client_id='NOElzEMDmrk2-Q',
                         client_secret='V-2RNfaQ5ryNEIbJZ8PXe1XSu-M',
                         user_agent=userAgent)

#def loadSubredditPosts(subreddit, numberOfPosts, sorting):

#def loadPostComments(post, numberOfComments, sorting)

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
        self.wfile.write(bytes("<html><head><title>https://pythonbasics.org</title></head>", "utf-8"))
        self.wfile.write(bytes("<body>", "utf-8"))
        for submission in self.reddit.subreddit('all').controversial(limit=10):
            if not (submission.over_18):
                self.wfile.write(bytes("<p><a href=\"" + str(submission.url) + "\">" + str(submission.title) + "</a> ("+ "<a href=\"https://www.reddit.com/r/" + str(submission.subreddit) + "\">r/" + str(submission.subreddit) + "</a>" +")</p>", "utf-8"))
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
