" Interface for extracting info from Patch"
import argparse
import re
import sys
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


def patch_get_content_urls(state, city, topic, max_content=3):
    """Load content urls, in list format"""

    # Define url template - some url parameters are fixed (ie. events, next-week, pages=1, free events)
    url = f"https://patch.com/{state}/{city}/{topic}"

    print(url)
    # Make an HTTP GET request to retrieve the HTML content
    response = requests.get(url)

    # FIRST - IDENTIFY RECENT CONTENT
    # Check if the request was successful
    if response.status_code == 200:

        # Parse the HTML using BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")

        # Find last 3 div elements with the given attributes - until content with dates can be easier identified
        div_elements = soup.find_all(
            "span",
            class_="MuiTypography-root MuiTypography-caption css-c3ysrx",
            limit=max_content,
        )

        texts = []
        indices = []

        for index, div_element in enumerate(div_elements):
            try:
                text = div_element.text
                match = re.search(r"\d+d", text)
                if match:  # Check if the text contains a date
                    texts.append(match.group())
                    indices.append(index)
                else:
                    texts.append("None")
            except AttributeError:
                pass

        #         return texts, indices

        # SECOND - IDENTIFY URLS FOR RECENT CONTENT
        urls = []

        for i in indices:
            div_elements = soup.find_all(
                "a",
                class_="MuiTypography-root MuiTypography-inherit MuiLink-root MuiLink-underlineAlways css-syvjvm",
                limit=max_content,
            )
            urls.append("https://patch.com" + div_elements[0]["href"])

        return urls

    # If the request was not successful, return None or handle the error accordingly
    return None


def patch_load_content(state, city, topic, max_content=3):
    """Load and store up to top N pieces of local events content for this topic, in pandas format"""

    # Initial check
    urls = patch_get_content_urls(state, city, topic, max_content=3)

    if len(urls) > 0:

        # Define dictionary to populate pandas table
        content_dict = {}

        # Get field content for each event id and store in pandas dataframe
        df = pd.DataFrame()

        # Iterate through all recent url content
        for url in urls:
            search = state + "/" + city + "/" + topic

            content_dict[search] = search
            content_dict["patch_content"] = []

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
        return "No recent content."


# #### Patch events


def patch_get_event_info_url(state, city, max_content=5):
    """Load event urls, in list format"""

    # Define url template - some url parameters are fixed (ie. events, next-week, pages=1, free events)
    url_template = "https://patch.com/{state}/{city}/calendar"

    # Complete url
    url = url_template.replace("{state}", state).replace("{city}", city)

    # Make an HTTP GET request to retrieve the HTML content
    response = requests.get(url)

    # FIRST - IDENTIFY RECENT CONTENT - GET DATES
    # Check if the request was successful
    if response.status_code == 200:

        # Parse the HTML using BeautifulSoup
        soup = BeautifulSoup(response.content, "html.parser")

        # Get two sperate pieces of inforamation on events - month/day and time
        # Find most recent 5 div elements - month/day
        div_elements_date = soup.find_all(
            "div", class_="calendar-icon__date", limit=max_content
        )

        # Find most recent 5 div elements - times
        div_elements_time = soup.find_all(
            "time",
            class_="styles_EventDateAndTime__eventDetail__TNlkQ",
            limit=max_content,
        )

        # Get the current year, to append to calendar date/time
        current_year = datetime.now().year

        days = []
        for div_element in div_elements_date:
            try:
                # Extract month and day values and format as datetime object with current year
                month = div_element.find("strong", class_="calendar-icon__month").text
                day = div_element.find("strong", class_="calendar-icon__day").text
                formatted_day = datetime.strptime(
                    f"{month} {day} {current_year}", "%b %d %Y"
                )
                days.append(formatted_day)

            except AttributeError:
                pass

        times = []
        for div_element in div_elements_time:
            try:
                # Extract time string
                day_time_string = div_element.text.strip().split(", ")[1]
                # day = div_element.find('strong', class_='calendar-icon__day').text
                # formatted_date = datetime.strptime(f"{month} {day} {current_year}", "%b %d %Y")
                times.append(day_time_string)

            except AttributeError:
                pass

        formatted_dates = []

        for date, time in zip(days, times):
            formatted_time = datetime.strptime(time, "%I:%M %p").time()
            formatted_datetime = datetime.combine(
                date.date(), formatted_time
            ).isoformat()
            formatted_dates.append(formatted_datetime)

        # Make sure at LEAST one event, the earliest, is within the next 7 days
        today = date.today().date()

        # Get the first date from the list and parse the date string into a datetime object
        date_object = datetime.strptime(formatted_dates[0], "%Y-%m-%dT%H:%M:%S")
        first_date = date_object.date()

        # Calculate the difference in days
        days_diff = (first_date - today).days

        # Check if the first date is within 7 days from today
        if 0 <= days_diff <= 7:
            # SECOND - IDENTIFY URLS FOR DATED CONTENT ABOVE - GET URLS
            div_elements = soup.find_all(
                "a", class_="styles_Card__Thumbnail__FioCE", limit=max_content
            )

            urls = ["https://patch.com" + url["href"] for url in div_elements]
            return urls
        else:
            pass

    # If the request was not successful, return None or handle the error accordingly
    return "No upcoming events"


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
        default="fortgreene",
        help="Specify city your localized patch query.",
    )
    parser.add_argument(
        "-T",
        "--topic",
        type=str,
        default="sports",
        help="Specify topic your localized patch query.",
    )

    args = parser.parse_args()
    this = sys.modules[__name__]

    assert args.topic in topics, "This topic is not yet supported by our query tool."
    print(patch_load_content(args.state, args.city, args.topic))
