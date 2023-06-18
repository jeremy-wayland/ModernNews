import os
import ticketpy
from dotenv import load_dotenv
import argparse
import sys
from datetime import date, timedelta

# ### Eventbrite API
# Load from .env
load_dotenv()

api_key = os.getenv("TICKETMASTER_KEY")

tm_client = ticketpy.ApiClient(api_key)

# # Define dates
today = date.today()
time_frame = today + timedelta(days=7)

start_date = today.strftime("%Y-%m-%dT%H:%M:%SZ")
end_date = time_frame.strftime("%Y-%m-%dT%H:%M:%SZ")

page = tm_client.events.find(
    classification_name='hip hop',
    state_code='NY',
    start_date_time=start_date,
    end_date_time=end_date
).limit()

for event in page:
    name = event.name
    print(name)

# ### Eventbrite API
# Load from .env
# load_dotenv()

# api_key = os.getenv("TICKETMASTER_KEY")

# # Load ticketmaster API wrapper
# tm_client = ticketpy.ApiClient(api_key)

# # Define dates
# today = date.today()
# time_frame = today + timedelta(days=7)

# start_date = today.strftime("%Y-%m-%dT%H:%M:%SZ")
# end_date = time_frame.strftime("%Y-%m-%dT%H:%M:%SZ")

# def load_ticketmaster_events(search, state_code, start_date=start_date, end_date=time_frame):
    
#     search = search.lower()
#     state_code = state_code.lower()

#     page = tm_client.events.find(
#         classification_name=search,
#         state_code=state_code,
#         start_date_time=start_date,
#         end_date_time=time_frame
#     ).limit()

#     for event in page:
#         name = event.name
#         print(name)


# # Making Executable Action when you run the python file
# if __name__ == "__main__":

#     parser = argparse.ArgumentParser()

#     parser.add_argument(
#         "-S",
#         "--search",
#         type=str,
#         default="hip-hop",
#         help="Specify your event genre or search.",
#     )
#     parser.add_argument(
#         "-C",
#         "--state_code",
#         type=str,
#         default="ny",
#         help="Specify your event state code.",
#     )
#     parser.add_argument(
#         "-s",
#         "--start_date",
#         type=str,
#         default=start_date,
#         help="Specify your earliest coverage date.",
#     )
#     parser.add_argument(
#         "-E",
#         "--end_date",
#         type=str,
#         default=end_date,
#         help="Specify your latest coverage date.",
#     )

#     args = parser.parse_args()
#     this = sys.modules[__name__]

#     load_ticketmaster_events(args.search, args.state_code, args.start_date, args.end_date)