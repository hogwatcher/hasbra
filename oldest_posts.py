import requests
import datetime
import time


API_URL = "https://api.pullpush.io/reddit/search/submission/"


def fetch_oldest_posts(subreddit, limit=100):
    """
    Fetch the oldest Reddit submissions from a subreddit using PullPush.
    """

    headers = {"User-Agent": "oldest-post-fetcher/1.0"}

    posts = []
    before = None

    try:
        while len(posts) < limit:
            batch_size = min(100, limit - len(posts))

            params = {
                "subreddit": subreddit,
                "sort": "asc",
                "sort_type": "created_utc",
                "size": batch_size,
            }

            # Pagination cursor.
            if before is not None:
                params["before"] = before

            response = requests.get(API_URL, params=params, headers=headers, timeout=30)

            response.raise_for_status()

            data = response.json().get("data", [])

            if not data:
                break

            posts.extend(data)

            # Use the oldest timestamp from this batch
            timestamps = [
                post.get("created_utc")
                for post in data
                if post.get("created_utc") is not None
            ]

            if not timestamps:
                break

            new_before = min(timestamps)

            # Prevent infinite loops if the API returns the same data
            if before == new_before:
                break

            before = new_before

            # Avoid hammering the API
            time.sleep(1)

        return posts[:limit]

    except requests.exceptions.HTTPError as e:
        print(f"HTTP error: {e}")
        if response is not None:
            print(f"Response: {response.text[:500]}")
        return []

    except requests.exceptions.RequestException as e:
        print(f"Network error occurred: {e}")
        return []

    except ValueError as e:
        print(f"Invalid JSON response: {e}")
        return []


def write_posts_to_markdown(posts, subreddit, filename="oldest_posts.md"):
    """
    Write Reddit posts to a Markdown file.
    """

    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# Oldest Posts from r/{subreddit}\n\n")

            if not posts:
                f.write("No posts found.\n")
                print("No posts found to write.")
                return

            # Sort locally as an extra safeguard
            posts = sorted(
                posts, key=lambda post: post.get("created_utc", float("inf"))
            )

            for post in posts:
                title = post.get("title", "No Title")

                permalink = post.get("permalink", "")

                if permalink:
                    post_url = f"https://www.reddit.com{permalink}"
                else:
                    post_url = post.get("url", "#")

                created_utc = post.get("created_utc")

                if created_utc:
                    date_str = datetime.datetime.fromtimestamp(
                        created_utc, tz=datetime.timezone.utc
                    ).strftime("%Y-%m-%d %H:%M:%S UTC")
                else:
                    date_str = "Unknown Date"

                # Escape Markdown characters in the title
                safe_title = title.replace("[", "\\[").replace("]", "\\]")

                f.write(f"- **[{safe_title}]({post_url})** — *{date_str}*\n")

        print(f"Successfully saved {len(posts)} posts to {filename}")

    except IOError as e:
        print(f"File writing error: {e}")


if __name__ == "__main__":
    target_subreddit = "Hasan_Piker"

    number_of_posts = 10

    raw_posts = fetch_oldest_posts(target_subreddit, limit=number_of_posts)

    write_posts_to_markdown(raw_posts, target_subreddit, "oldest_hasan_posts.md")
