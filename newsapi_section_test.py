"Interface for generating a Brief section for NewsAPI results"

from data_loader.news_api import newsapi_load_content
from src.content_summary import get_news_summary
import argparse
import sys

# Executable Action for test python file
if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-Q",
        "--query",
        type=str,
        default="sustainability",
        help="News topic.",
    )

    args = parser.parse_args()
    this = sys.modules[__name__]

    result = newsapi_load_content(args.query)

    # Summarize NewsAPI content
    cb, brief_content = get_news_summary(result, args.query)

    print(cb, "\n\n", brief_content)