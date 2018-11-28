from enum import Enum

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
