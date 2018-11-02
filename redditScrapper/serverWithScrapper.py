# Python 3 server example
from http.server import BaseHTTPRequestHandler, HTTPServer
import time
import praw

userAgent = "python:decentralizedRedditProject:0.0 (by /u/buprojectaccount )"
reddit = praw.Reddit(client_id='NOElzEMDmrk2-Q',
                     client_secret='V-2RNfaQ5ryNEIbJZ8PXe1XSu-M',
                     user_agent=userAgent)


hostName = "localhost"
serverPort = 8080

class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(bytes("<html><head><title>https://pythonbasics.org</title></head>", "utf-8"))
        self.wfile.write(bytes("<body>", "utf-8"))
        for submission in reddit.subreddit('all').new(limit=10):
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
