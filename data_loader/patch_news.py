"Interface for extracting news content info from Patch - time frame is last 24 hours - 1d"

import argparse
import sys
import re
from datetime import datetime
import pandas as pd
import requests
from bs4 import BeautifulSoup

# NEED TO DEFINE A FUNCTION THAT MAPS USER PREFERENCES TO THESE PATCH topics #
topics = [
    "police-fire",
    "obituaries",
    "around-town",
    "politics",
    "traffic-transit",
    "schools",
    "restaurants-bars",
    "business",
    "weather",
    "sports",
    "pets",
    "best-of",
    "arts-entertainment",
    "lifestyle",
    "kids-family",
    "going-green",
    "holidays",
    "personal-finance",
    "travel",
]


def patch_get_content_urls(state, city, topic, max_content=5):
    """Load content urls, in list format"""

    # Define url template
    url = f"https://patch.com/{state}/{city}/{topic}"

    # Make an HTTP GET request to retrieve the HTML content
    response = requests.get(url)

    # FIRST - IDENTIFY RECENT CONTENT
    # Check if the request was successful
    if response.status_code == 200:

        # Parse the HTML using BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")

        # Find last 3 div elements with the given attributes - until content with dates can be easier identified, need to multiply max_content by 2 to actually achieve max content
        true_max = max_content * 2
        div_elements = soup.find_all(
            "span",
            class_="MuiTypography-root MuiTypography-caption css-c3ysrx",
            limit=true_max,
        )

        texts = []
        indices = []

        for index, div_element in enumerate(div_elements):
            try:
                text = div_element.text
                match = re.search(r"\d+d", text)
                if match.group() == "1d":  # Check if the date is 1d ago
                    texts.append(match.group())
                    indices.append(index)
            except AttributeError:
                pass

        # SECOND - IDENTIFY URLS FOR RECENT CONTENT
        if len(texts)>0:
            div_elements = soup.find_all(
                "a",
                class_="MuiTypography-root MuiTypography-inherit MuiLink-root MuiLink-underlineAlways css-syvjvm",
                limit=len(texts)
            )
            urls = ["https://patch.com" + i["href"] for i in div_elements]

            return urls
        else:
            return 'No recent news.'

    # If the request was not successful, return None or handle the error accordingly
    return 'Failed HTML response.'


def patch_load_content(state, city, topic, max_content=5):
    """Load and store up to top N pieces of local events content for this topic, in pandas format"""

    # Initial check
    urls = patch_get_content_urls(state, city, topic, max_content=max_content)

    # Check if URLs were returned / if there are upcoming events
    if isinstance(urls, list):

        # Define dictionary to populate pandas table
        content_dict = {}
        content_dict["patch_content"] = []

        # Get field content for each event id and store in pandas dataframe
        df = pd.DataFrame()

        # Iterate through all recent url content
        for url in urls:

            # Make an HTTP GET request to retrieve the HTML content
            response = requests.get(url)

            # Check if the request was successful
            if response.status_code == 200:
                # Parse the HTML content using BeautifulSoup
                soup = BeautifulSoup(response.content, "html.parser")

                # Find the article content based on HTML tags or classes specific to the website
                article_content = soup.find(
                    "article", class_="styles_Section__card__4Uoov"
                )

                # Extract the text from the article content
                article_text = article_content.get_text(separator=" ")

                # Reduce consecutive spaces to a single space
                red_space_text = re.sub(r"\s+", " ", article_text)

                # Remove '\n' from the text
                clean_text = red_space_text.replace("\n", "")

                # Append the scraped article content to dict
                content_dict["patch_content"].append(clean_text)

        # Populate the DataFrame with data from the dictionary
        df["patch_content"] = content_dict["patch_content"]

        return df

    else:
        return urls

# print(patch_load_content('new-york','brooklyn','around-town'))

# Making Executable Action when you run the python file
if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-S",
        "--state",
        type=str,
        default="new-york",
        help="Specify state your localized patch query.",
    )
    parser.add_argument(
        "-C",
        "--city",
        type=str,
        default="new-york-city",
        help="Specify city your localized patch query.",
    )
    parser.add_argument(
        "-T",
        "--topic",
        type=str,
        default="around-town",
        help="Specify topic your localized patch query.",
    )

    args = parser.parse_args()
    this = sys.modules[__name__]

    assert args.topic in topics, "This topic is not yet supported by our query tool."
    print(patch_load_content(args.state, args.city, args.topic))
