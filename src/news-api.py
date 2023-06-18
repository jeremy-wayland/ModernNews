" Interface for extracting info from News-API"
import argparse
import sys
import os
from datetime import date, timedelta
import string
import re
import pandas as pd
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
from newsapi.newsapi_client import NewsApiClient

# Load from .env
load_dotenv()
api_key = os.getenv("NEWS_KEY")

# Init
newsapi = NewsApiClient(api_key=api_key)

today = date.today()
yesterday = today - timedelta(days=1)

start_date = yesterday.strftime("%Y-%m-%d")
end_date = today.strftime("%Y-%m-%d")


# The News-API is helpful for retrieving the big info on news and articles, like the:
# - source
# - date
# - description
# - title
# - author
# - content (*)
#
# However the content (*)  is only a snippit (usually some 200 char) or so in length. So to build on this, we take the url and scrape the content another way.

# Guidance on q=query=key word serch in News API - Keywords or phrases to search for in the article title and body.
#
# - Surround phrases with quotes (") for exact match.
# - Prepend words or phrases that must appear with a + symbol. Eg: +bitcoin
# - Prepend words that must not appear with a - symbol. Eg: -bitcoin
# - Alternatively you can use the AND / OR / NOT keywords, and optionally group these with parenthesis. Eg: crypto AND (ethereum OR litecoin) NOT bitcoin.
# - The complete value for q must be URL-encoded. Max length: 500 chars.

# Scraping manually using BeautifulSoup


# Check snews sources in news-api
# [source['name'] for source in newsapi.get_sources()['sources'] if 'name' in source]


def newsapi_extract_strings(query):
    """Parse the News-API query formats to retrieve only the base string(s)"""

    # MIGHT NEED TO ADJUST SO THE SAME QUERY LOGIC APPLIES TO CONTENT PARSE #

    lower_string = query.lower()

    # Create a translation table with symbol characters mapped to None
    translation_table = str.maketrans("", "", string.punctuation)

    # Remove symbols using the translation table
    cleaned_string = lower_string.translate(translation_table)

    # Drop literal keywords from query
    literals = ["and", "or", "not"]

    for word in literals:
        cleaned_string = cleaned_string.replace(word, "")

    search_words = cleaned_string.split()

    return search_words


def newsapi_scrape_article_content(url, div_class):
    """Scrapes content from a url given a div class association, in str format"""

    # Send a request to the URL
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")

        # Find the article content based on HTML tags or classes specific to the website
        # Customize these lines according to the structure of the website you're scraping
        article_content = soup.find("div", class_=div_class)

        # Extract the text from the article content
        article_text = article_content.get_text(separator=" ")

        # Reduce consecutive spaces to a single space
        red_space_text = re.sub(r"\s+", " ", article_text)

        # Remove '\n' from the text
        clean_text = red_space_text.replace("\n", "")

        # Return the scraped article content
        return clean_text

    # If the request was not successful, return None or handle the error accordingly
    return None


def newsapi_find_url_div_class_with_text(url, search_word):
    """Finds all div class associations for a given word search, in list format"""
    response = requests.get(url)
    soup = BeautifulSoup(response.content, "html.parser")

    # Find all div elements on the page
    div_elements = soup.find_all("div")
    class_elements = []

    # Parse search words from news-api query
    query = newsapi_extract_strings(search_word)

    for div in div_elements:
        # Check if the search word(s) present in the div class text

        # EXPLORE HOW TO IGNORE PAYWALL SITES ALTOGETHER - IDENTIFYING THEM?
        # ALSO NEED TO FIND A WAY TO CUT DOWN ON NUM OF CLASSES - APPLY SOME CONDITIONS?

        if all(word in div.get_text().lower() for word in query):
            div_class = div.get("class")
            if div_class:
                for item in div_class:
                    class_elements.append(item)
            else:
                continue

            # If you want to extract the full content of the div, you can use div.get_text() or div.prettify() to get the HTML
    return class_elements


def newsapi_get_url_content(url, search_word):
    """Returns the largest body of relevant content, in str format"""

    div_classes = newsapi_find_url_div_class_with_text(url, search_word)

    larg_content_piece = ""

    # To keep from having to re-load the largest class of content - cache only if this is largest content piece
    for class_ in div_classes:
        class_content = newsapi_scrape_article_content(url, class_)

        if len(class_content) > len(larg_content_piece):
            larg_content_piece = class_content

    return larg_content_piece


# #### Load content from News-API


def newsapi_load_content(
    q, start_date, end_date, language="en", sort_by="relevancy", page=1, n_content=5
):
    """Load and store up to top N pieces of content for this topic, in pandas format"""

    # /everything end point - see docs
    top_n_articles = newsapi.get_everything(
        q=q,
        from_param=start_date,
        to=end_date,
        language=language,
        sort_by=sort_by,
        page=page,
        page_size=n_content,
    )

    # Store content urls for further web parsing
    content_urls = []

    for item in top_n_articles["articles"]:
        url = item["url"]
        content_urls.append(url)

    # Get max content for each url and store in pandas dataframe
    df = pd.DataFrame()
    content_dict = {}

    content_dict["newsapi_content"] = []

    for url in content_urls:
        content = newsapi_get_url_content(url, q)
        content_dict["newsapi_content"].append(content)

    # Populate the DataFrame with data from the dictionary
    df["newsapi_content"] = content_dict["newsapi_content"]

    return df


# print(newsapi_load_content(q='politics', start_date=start_date, end_date=end_date))

# Making Executable Action when you run the python file
if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-Q",
        "--query",
        type=str,
        default="street fashion",
        help="Specify search for words and phrases in the article title and body.",
    )
    parser.add_argument(
        "-S",
        "--start_date",
        type=str,
        default=start_date,
        help="Specify your earliest coverage date.",
    )
    parser.add_argument(
        "-E",
        "--end_date",
        type=str,
        default=end_date,
        help="Specify your latest coverage date.",
    )

    args = parser.parse_args()
    this = sys.modules[__name__]

    print(newsapi_load_content(args.query, args.start_date, args.end_date))

