import praw

userAgent = "python:decentralizedRedditProject:0.0 (by /u/buprojectaccount )"
reddit = praw.Reddit(client_id='NOElzEMDmrk2-Q',
                     client_secret='V-2RNfaQ5ryNEIbJZ8PXe1XSu-M',
                     user_agent=userAgent)

for submission in reddit.subreddit('all').new(limit=10):
    if not submission.stickied:
        print(submission.title)
        print(submission.subreddit)
        if (submission.selftext):
            print(submission.selftext)
        else:
            print(submission.url)
