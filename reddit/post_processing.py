from typing import List, Dict
from praw import models
import os
from retry import retry
import time
from utils.json_utils import append_to_jsonl
from reddit.reddit_client import get_client


class SubmissionCategory:
    HOT: str = 'hot'
    CONTROVERSIAL: str = 'controversial'
    TOP: str = 'top'


class PostRetrieval():
    def __init__(
        self,
        subreddit_name: str,
        limit_per_iteration: int = 10,
        max_posts_to_retrieve: int = 30,
        category: str = SubmissionCategory.HOT,
        use_after: bool = True
    ) -> None:
        self.reddit = get_client()
        self.subreddit = self.reddit.subreddit(subreddit_name)
        self.limit_per_iteration = limit_per_iteration
        self.max_posts_to_retrieve = max_posts_to_retrieve
        self.output_directory = './reddit/data/'
        os.makedirs(self.output_directory, exist_ok=True)
        self.seen_post_ids_file = os.path.join(
            self.output_directory, 'seen_post_ids.txt')

        seen_posts_list = self.read_seen_post_ids()
        self.last_post_id = seen_posts_list[-1] if seen_posts_list else None
        self.seen_ids = set(seen_posts_list)

        self.posts_file = os.path.join(self.output_directory, 'posts.jsonl')
        self.comments_file = os.path.join(
            self.output_directory, 'comments.jsonl')
        self.replies_file = os.path.join(
            self.output_directory, 'replies.jsonl')

        self.category = category
        self.requests_count = 0
        self.use_after = use_after

    def read_seen_post_ids(self) -> List[str]:
        if os.path.exists(self.seen_post_ids_file):
            with open(self.seen_post_ids_file, 'r') as f:
                return [line.strip() for line in f.readlines()]
        return []

    def process(self) -> None:
        number_of_posts = 0

        while number_of_posts < self.max_posts_to_retrieve:
            # Retrieve posts with pagination
            posts = self.retrieve_posts()
            print("Done processing posts")
            # Loop through each retrieved post
            for post in posts:
                # Retrieve comments and replies for the post
                post_comments = self.retrieve_comments_and_replies(post)

                # Extract relevant data for the post
                post_info = {
                    'id': post.id,
                    'url': post.url,
                    'body': post.selftext,
                    'title': post.title,
                    'created_utc': post.created_utc,
                    'is_self': post.is_self,
                    'num_comments': post.num_comments,
                    'permalink': post.permalink,
                    'score': post.score,
                    'subreddit_id': post.subreddit_id
                }

                # Retrieve and save replies for each comment
                comment_replies = []
                comments_data = []
                for comment in post_comments:
                    comment_data = {
                        'id': comment.id,
                        'permalink': comment.permalink,
                        'created_utc': comment.created_utc,
                        'subreddit_id': comment.subreddit_id,
                        'score': comment.score,
                        'post_id': post.id,
                        'body': comment.body
                    }
                    replies = self.retrieve_replies(comment)
                    comment_data["total_replies"] = len(replies)

                    comments_data.append(comment_data)
                    comment_replies.extend(replies)

                self.add_seen(post)
                append_to_jsonl([post_info], self.posts_file)
                append_to_jsonl(comments_data, self.comments_file)
                append_to_jsonl(comment_replies, self.replies_file)

                # Increment the number of processed posts
                number_of_posts += 1

        print("Process completed!")

    def add_seen(self, post: models.Submission) -> None:
        self.seen_ids.add(post.id)
        with open(self.seen_post_ids_file, 'a') as f:
            f.write(post.id + '\n')

    # Function to retrieve posts with pagination
    @retry(
        exceptions=Exception,
        tries=5,
        delay=2,
        backoff=2,
        max_delay=60,
    )
    def retrieve_posts(self) -> List[models.Submission]:
        print("last_post_id:", self.last_post_id)
        posts = []
        submissions = self._get_submissions()
        self.requests_count += 1
        self.use_after = True
        print("Retrieved submissions")
        for post in submissions:
            print("Processing post:", post.id, post.is_self, post.url)
            self.last_post_id = post.id
            if post.id not in self.seen_ids:
                print("Adding post:", post.id)
                posts.append(post)
        self.check_sleep()

        return posts

    def _get_submissions(self) -> List[models.Submission]:
        params = {
            # "after": self.last_post_id
            "after": None if self.last_post_id is None or not self.use_after else f"t3_{self.last_post_id}"
            # "after": None if self.last_post_id is None or not self.use_after else self.last_post_id
        }
        print("Params:", params)
        if self.category == SubmissionCategory.HOT:
            return self.subreddit.hot(
                limit=self.limit_per_iteration,
                params=params,
            )
        elif self.category == SubmissionCategory.CONTROVERSIAL:
            return self.subreddit.controversial(
                limit=self.limit_per_iteration,
                params=params,
            )
        elif self.category == SubmissionCategory.TOP:
            return self.subreddit.top(
                limit=self.limit_per_iteration,
                params=params,
            )

        raise Exception("Invalid category")

    @retry(exceptions=Exception, tries=5, delay=2, backoff=2, max_delay=60)
    def retrieve_comments_and_replies(
        self,
        post: models.Submission,
    ) -> List[models.Comment]:
        comments = []
        print("Processing comments for post:", post.id)
        # Retrieve comments for the post
        post.comments.replace_more(limit=None)
        all_comments = post.comments.list()
        print(f"Comments length: {len(all_comments)}")
        for comment in all_comments:
            self.requests_count += 1
            print("Processing comment:", comment.id)
            # Extract relevant data for comments

            comments.append(comment)

            self.check_sleep()

        return comments

    @retry(exceptions=Exception, tries=5, delay=2, backoff=2, max_delay=60)
    def retrieve_replies(self, comment: models.Comment) -> List[Dict]:
        replies = []
        print("Processing replies for comment:", comment.id)
        for reply in comment.replies:
            self.requests_count += 1
            # Extract relevant data for replies
            reply_data = {
                'id': reply.id,
                'permalink': reply.permalink,
                'created_utc': reply.created_utc,
                'subreddit_id': reply.subreddit_id,
                'score': reply.score,
                'parent_comment_id': comment.id,
                'body': reply.body,
                'total_replies': 0
            }
            replies.append(reply_data)

            # Recursively retrieve replies for the reply
            # if len(replies) < comment_limit:
            child_replies = self.retrieve_replies(reply)
            reply_data['total_replies'] = len(child_replies)
            replies.extend(child_replies)

            self.check_sleep()

        return replies

    def check_sleep(self):
        if self.requests_count % 1000 == 0:
            print("Sleeping for 20 seconds")
            time.sleep(10)


if __name__ == '__main__':
    post_retrieval = PostRetrieval(
        subreddit_name='politics',  # 'DebateReligion',  # 'politics',
        limit_per_iteration=10,
        max_posts_to_retrieve=6000,
        category=SubmissionCategory.HOT,
        use_after=True
    )
    post_retrieval.process()
