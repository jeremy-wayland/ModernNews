" Interface for extracting info from Eventbrite"

import argparse
import sys
import os
from eventbrite import Eventbrite 
import pandas as pd
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# ### Eventbrite API
# Load from .env
load_dotenv()
api_key = os.getenv("EVENTBRITE_KEY")

eventbriteapi = Eventbrite(api_key)

# See event ategories in eventbrite
# [cat['name'] for cat in eventbriteapi.get_subcategories()['subcategories'] if 'name' in cat]


def eventbrite_get_event_ids(state, city, search, num_events=6):
    """Get a list of next weeks event ids associated with a given search, in str format"""

    # Define url template - some url parameters are fixed (ie. events, next-week, pages=1, free events)
    url_template = "https://www.eventbrite.com/d/{state}-{city}/free--events--next-week/{search}/?page=1"

    # Complete url
    url = (
        url_template.replace("{state}", state)
        .replace("{city}", city)
        .replace("{search}", search)
    )

    # Make an HTTP GET request to retrieve the HTML content
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        html_content = response.text

        # Parse the HTML using BeautifulSoup
        soup = BeautifulSoup(html_content, "html.parser")

        # Find all div elements with the given attributes
        div_elements = soup.find_all(
            "div", attrs={"data-testid": "event-card-tracking-layer"}, limit=num_events
        )

        # Get the values of 'data-event-id' attribute from the first 4 div elements
        event_ids = list(
            set(
                [div_elements[i]["data-event-id"] for i in range(len(div_elements) - 1)]
            )
        )

        return event_ids

    # If the request was not successful, return None or handle the error accordingly
    return 'No relevant event IDs.'


# #### Load content from eventbrite


def eventbrite_load_events(state, city, search, n_content=3):
    """Load and store up to top N pieces of local events for this search, in pandas format"""

    # Define N as n_content * 2 to account for double (app/web) search results - until fixed
    N = n_content * 2

    # Get N event IDs
    event_ids = eventbrite_get_event_ids(state, city, search, num_events=N)
    content_dict = {}

    # Get field content for each event id and store in pandas dataframe
    df = pd.DataFrame()

    content_dict["eventbrite_desc"] = []
    content_dict["eventbrite_time"] = []
    content_dict["eventbrite_url"] = []

    for id_ in event_ids:

        # Get event description, time, and url using event id - dict
        event_desc = eventbriteapi.get_event(id=id_)["description"]
        event_time = eventbriteapi.get_event(id=id_)["start"]["local"]
        event_url = eventbriteapi.get_event(id=id_)["url"]

        content_dict["eventbrite_desc"].append(event_desc)
        content_dict["eventbrite_time"].append(event_time)
        content_dict["eventbrite_url"].append(event_url)

    # Populate the DataFrame with data from the dictionary
    df["eventbrite_desc"] = content_dict["eventbrite_desc"]
    df["eventbrite_time"] = pd.to_datetime(content_dict["eventbrite_time"])
    df["eventbrite_url"] = content_dict["eventbrite_url"]

    df_sorted = df.sort_values(by='eventbrite_time', ascending=True)

    return df_sorted

# print(eventbrite_load_events('new-york','new-york-city','sports'))

# Making Executable Action when you run the python file
if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-S",
        "--state",
        type=str,
        default="new-york",
        help="Specify state for your localized eventbrite search.",
    )
    parser.add_argument(
        "-C",
        "--city",
        type=str,
        default="new-york-city",
        help="Specify city for your localized eventbrite search.",
    )
    parser.add_argument(
        "-T",
        "--topic",
        type=str,
        default="sports",
        help="Specify topic for your localized eventbrite search.",
    )

    args = parser.parse_args()
    this = sys.modules[__name__]

    print(eventbrite_load_events(args.state, args.city, args.topic))