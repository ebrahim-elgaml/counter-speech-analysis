from reddit.reddit_client import get_client

# Specify the subreddit
reddit = get_client()
subreddit = reddit.subreddit('politics')

# Set the number of submissions to retrieve per batch
batch_size = 10

# Set the maximum number of submissions to retrieve
max_submissions = 100

# Initialize a counter for the number of retrieved submissions
num_submissions = 0

# Initialize a list to store processed submissions
processed_submissions = []


def get_replies(comment):
    replies = []
    for reply in comment.replies:
        replies.append({
            'body': reply.body,
            'replies': get_replies(reply)
        })
    return replies
# Process submissions in batches until reaching the maximum limit or all submissions are processed


with open('./reddit/reddit_posts_with_comments2.txt', 'w', encoding='utf-8') as file:

    while num_submissions < max_submissions:
        # Retrieve submissions in a batch
        submissions = subreddit.search(
            query=' ',
            # syntax='lucene',
            sort='controversial',
            time_filter="month",
            limit=batch_size,
            params={
                "after": None
                if not processed_submissions
                else f"t3_{processed_submissions[-1].id}"
            }
        )

        for post in submissions:
            print("Processing post: ", post.url)
            # Write post information to the file
            file.write("Title: {}\n".format(post.title))
            file.write("Id: {}\n".format(post.id))
            file.write("URL: {}\n".format(post.url))
            file.write("Body: {}\n".format(post.selftext))
            file.write("Comments:\n")

            # Fetch comments for the post
            post.comments.replace_more(limit=None)

            # Iterate through the comments
            for comment in post.comments.list():
                # Write comment information to the file
                file.write("- Comment: {}\n".format(comment.body))
                if comment.replies:
                    file.write("  - Replies:\n")
                    # Function to recursively write replies

                    def write_replies(replies, level=1):
                        for reply in replies:
                            file.write("    " + "  " * level +
                                       "- " + reply['body'] + "\n")
                            if reply['replies']:
                                write_replies(reply['replies'], level + 1)
                    write_replies(get_replies(comment))

            # Add a separator between posts
            file.write("\n")

        # If all submissions are processed, break out of the loop
        if num_submissions >= max_submissions:
            break

# Print a message indicating the end of processing
print("Finished processing submissions.")
