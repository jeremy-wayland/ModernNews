import os
import ticketpy
from dotenv import load_dotenv
import json

# ### Eventbrite API
# Load from .env
load_dotenv()

api_key = os.getenv("TICKETMASTER_KEY")

tm_client = ticketpy.ApiClient(api_key)

page = tm_client.events.find(
    classification_name='hip hop',
    state_code='NY',
    start_date_time='2023-05-21T20:00:00Z',
    end_date_time='2023-06-30T20:00:00Z'
).limit()

for event in page:
    name = event.name
    print(name)