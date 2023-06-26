"Interface for extracting info from Ticketmaster - time frame is next 3-10 days"

import os
import ticketpy
from dotenv import load_dotenv
import argparse
import sys
from datetime import date, timedelta
import pandas as pd

# ### Eventbrite API
# Load from .env
load_dotenv()

api_key = os.getenv("TICKETMASTER_KEY")

tm_client = ticketpy.ApiClient(api_key)

def load_ticketmaster_events(search, state_code):

    # Determine how many days to look forward for event search - defaults to one week
    today = date.today()
    start = today + timedelta(days=3)
    end = start + timedelta(days=7)

    # # Define dates
    start_date = start.strftime("%Y-%m-%dT%H:%M:%SZ")
    end_date = end.strftime("%Y-%m-%dT%H:%M:%SZ")

    page = tm_client.events.find(
        classification_name=search,
        state_code=state_code,
        start_date_time=start_date,
        end_date_time=end_date
    ).limit()


    df = pd.DataFrame()
    event_names = []
    event_genres = []
    event_venues = []
    event_urls = []

    for event in page:
        event_name = event.name
        event_genre = event.classifications
        event_venue = event.venues[0].name
        event_url = event.links['self']

        event_names.append(event_name)
        event_genres.append(event_genre)
        event_venues.append(event_venue)
        event_urls.append(event_url)

    df['event_names'] = event_names
    df['event_genres'] = event_genres
    df['event_venues'] = event_venues
    df['event_urls'] = event_urls

    if len(event_names) > 0:
        return df
    else:
        return "No upcoming events for this search."

# print(load_ticketmaster_events('brooklyn', 'NY', days_ahead=7))


# # Making Executable Action when you run the python file
if __name__ == "__main__":

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-S",
        "--search",
        type=str,
        default="latin",
        help="Specify your event genre or search.",
    )
    parser.add_argument(
        "-C",
        "--state_code",
        type=str,
        default="ny",
        help="Specify your event state code.",
    )

    args = parser.parse_args()
    this = sys.modules[__name__]

    print(load_ticketmaster_events(args.search, args.state_code))