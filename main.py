import requests
import datetime
import time


API_URL = "https://api.pullpush.io/reddit/search/submission/"


def fetch_oldest_posts(subreddit, limit=100, max_retries=5):
    """
    Fetch the oldest Reddit submissions from a subreddit
    using the PullPush API.
    """

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    }

    params = {
        "subreddit": subreddit,
        "sort": "asc",
        "sort_type": "created_utc",
        "size": min(limit, 100),
    }

    for attempt in range(1, max_retries + 1):
        try:
            print(f"Requesting PullPush API (attempt {attempt}/{max_retries})...")

            response = requests.get(API_URL, params=params, headers=headers, timeout=60)

            print(f"HTTP status: {response.status_code}")

            # Successful response
            if response.status_code == 200:
                try:
                    result = response.json()
                except ValueError:
                    print("Server returned invalid JSON.")
                    print(response.text[:500])
                    return []

                posts = result.get("data", [])

                print(f"Received {len(posts)} posts.")

                return posts

            # Temporary server-side errors
            if response.status_code in (502, 503, 504, 429):
                if response.status_code == 429:
                    print("Rate limited by PullPush.")

                else:
                    print(f"PullPush server returned {response.status_code}.")

                if attempt < max_retries:
                    wait_time = 2 ** (attempt - 1)

                    print(f"Retrying in {wait_time} seconds...")

                    time.sleep(wait_time)
                    continue

                print("Maximum retries reached.")
                return []

            # Other HTTP error
            print(f"API Error: HTTP {response.status_code}")

            print("Response:", response.text[:500])

            return []

        except requests.exceptions.Timeout:
            print("Request timed out.")

            if attempt < max_retries:
                wait_time = 2 ** (attempt - 1)

                print(f"Retrying in {wait_time} seconds...")

                time.sleep(wait_time)
            else:
                print("Maximum retries reached.")

        except requests.exceptions.ConnectionError as e:
            print(f"Connection error: {e}")

            if attempt < max_retries:
                wait_time = 2 ** (attempt - 1)

                print(f"Retrying in {wait_time} seconds...")

                time.sleep(wait_time)
            else:
                print("Maximum retries reached.")

        except requests.exceptions.RequestException as e:
            print(f"Request error: {e}")
            return []

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

            # Sort locally to guarantee oldest first
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

                # Basic Markdown escaping
                safe_title = (
                    title.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")
                )

                f.write(f"- **[{safe_title}]({post_url})** — *{date_str}*\n")

        print(f"Successfully saved {len(posts)} posts to {filename}")

    except IOError as e:
        print(f"File writing error: {e}")


if __name__ == "__main__":
    target_subreddit = "Hasan_Piker"

    number_of_posts = 10

    print(
        f"Searching for the oldest {number_of_posts} posts in r/{target_subreddit}..."
    )

    raw_posts = fetch_oldest_posts(target_subreddit, limit=number_of_posts)

    write_posts_to_markdown(raw_posts, target_subreddit, "oldest_hasan_posts.md")
