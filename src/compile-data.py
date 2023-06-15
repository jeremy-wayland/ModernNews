import pandas as pd, numpy as np, os
from langchain import OpenAI
from langchain.agents import load_tools
from langchain.agents import initialize_agent
from langchain.agents import AgentType
import datetime
from datetime import date, timedelta, datetime
import requests
from bs4 import BeautifulSoup
import time
import re
import urllib.parse
import string

from newsapi import NewsApiClient
import eventbrite

# THIS NEEDS TO BE DIVIDED INTO SEPARATE FILES

# ### Context

# #### Setting time parameter -  1 day lookback if a daily service

today = date.today()
yesterday = today - timedelta(days=1)

start_date = yesterday.strftime('%Y-%m-%d')
end_date = today.strftime('%Y-%m-%d')
# print(end_date)

# #### Defining user class & preferences - can be collected with an onboarding quiz

# ### News-API

# Init
newsapi = NewsApiClient(api_key='2ef02540bbec4486bd6b70872b640fbe')

# /v2/everything
all_articles = newsapi.get_everything(q='this weekend AND brooklyn',                            
                                      from_param=start_date,
                                      to=end_date,
                                      language='en',
                                      sort_by='relevancy',
                                      page=1,
                                      page_size=3)


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

def newsapi_extract_strings(query):
    '''Parse the News-API query formats to retrieve only the base string(s)'''
    
    # MIGHT NEED TO ADJUST SO THE SAME QUERY LOGIC APPLIES TO CONTENT PARSE #
    
    lower_string = query.lower()
    
    # Create a translation table with symbol characters mapped to None
    translation_table = str.maketrans('', '', string.punctuation)

    # Remove symbols using the translation table
    cleaned_string = lower_string.translate(translation_table)
    
    # Drop literal keywords from query
    literals = ['and','or','not']
    
    for word in literals:
        cleaned_string = cleaned_string.replace(word, '')
        
    search_words = cleaned_string.split()

    return search_words


def newsapi_scrape_article_content(url, div_class):
    '''Scrapes content from a url given a div class association, in str format'''
    
    # Send a request to the URL
    response = requests.get(url)
    
    # Check if the request was successful
    if response.status_code == 200:
        # Parse the HTML content using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find the article content based on HTML tags or classes specific to the website
        # Customize these lines according to the structure of the website you're scraping
        article_content = soup.find('div', class_=div_class)
        
        # Extract the text from the article content
        article_text = article_content.get_text(separator=' ')
        
        # Reduce consecutive spaces to a single space
        red_space_text = re.sub(r'\s+', ' ', article_text)
        
        # Remove '\n' from the text
        clean_text = red_space_text.replace('\n', '')
        
        # Return the scraped article content
        return clean_text
    
    # If the request was not successful, return None or handle the error accordingly
    return None


def newsapi_find_url_div_class_with_text(url, search_word):
    '''Finds all div class associations for a given word search, in list format'''
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Find all div elements on the page
    div_elements = soup.find_all('div')
    class_elements = []
    
    # Parse search words from news-api query
    query = newsapi_extract_strings(search_word)

    for div in div_elements:
        # Check if the search word(s) present in the div class text
        
        # EXPLORE HOW TO IGNORE PAYWALL SITES ALTOGETHER - IDENTIFYING THEM?
        # ALSO NEED TO FIND A WAY TO CUT DOWN ON NUM OF CLASSES - APPLY SOME CONDITIONS?
        
        if all(word in div.get_text().lower() for word in query):
            div_class = div.get('class')
            if div_class:
                for item in div_class:
                    class_elements.append(item)
            else:
                continue
                
            # If you want to extract the full content of the div, you can use div.get_text() or div.prettify() to get the HTML
    return class_elements


def newsapi_get_url_content(url, search_word):
    '''Returns the largest body of relevant content, in str format'''
    
    div_classes = newsapi_find_url_div_class_with_text(url, search_word)
    
    larg_content_piece = ''
    
    # To keep from having to re-load the largest class of content - cache only if this is largest content piece
    for class_ in div_classes:
        class_content = newsapi_scrape_article_content(url, class_)

        if len(class_content) > len(larg_content_piece):
            larg_content_piece = class_content
            
    return larg_content_piece


# #### Load content from News-API

def newsapi_load_content(q, start_date, end_date, language='en', sort_by='relevancy', page=1, n_content=3):
    '''Load and store up to top N pieces of content for this topic, in pandas format'''
    
    # /everything end point - see docs
    top_n_articles = newsapi.get_everything(q=q,                            
                                      from_param=start_date,
                                      to=end_date,
                                      language=language,
                                      sort_by=sort_by,
                                      page=1, 
                                      page_size=n_content)
    
    # Store content urls for further web parsing
    content_urls = []
    
    for item in top_n_articles['articles']:
        url = item['url']
        content_urls.append(url)
        
    # Get max content for each url and store in pandas dataframe
    df = pd.DataFrame()
    content_dict = {}
    
    content_dict['newsapi_content'] = []
    
    for url in content_urls:
        content = newsapi_get_url_content(url, q)
        content_dict['newsapi_content'].append(content)

    # Populate the DataFrame with data from the dictionary
    df['newsapi_content'] = content_dict['newsapi_content']
    
    return df

# Check snews sources in news-api
# [source['name'] for source in newsapi.get_sources()['sources'] if 'name' in source]


# ### Eventbrite API

# eventbriteapi = eventbrite.Eventbrite(oauth_token='YFCIIJ6KT2WOL6AHRRSA')

# See event ategories in eventbrite
# [cat['name'] for cat in eventbriteapi.get_subcategories()['subcategories'] if 'name' in cat]

def eventbrite_get_event_ids(state, city, search, num_events=6):
    '''Get a list of next weeks event ids associated with a given search, in str format'''
    
    # Define url template - some url parameters are fixed (ie. events, next-week, pages=1, free events)
    url_template = 'https://www.eventbrite.com/d/{state}-{city}/free--events--next-week/{search}/?page=1'
    
    # Complete url
    url = url_template.replace('{state}', state).replace('{city}', city).replace('{search}', search)
    
    # Make an HTTP GET request to retrieve the HTML content
    response = requests.get(url)

    # Check if the request was successful
    if response.status_code == 200:
        html_content = response.text

        # Parse the HTML using BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find all div elements with the given attributes
        div_elements = soup.find_all('div', 
                                     attrs={'data-testid': 'event-card-tracking-layer'},
                                    limit=num_events)

        # Get the values of 'data-event-id' attribute from the first 4 div elements
        event_ids = list(set([div_elements[i]['data-event-id'] for i in range(len(div_elements)-1)]))

        return event_ids
    
    # If the request was not successful, return None or handle the error accordingly
    return None


# #### Load content from eventbrite

def eventbrite_load_events(state, city, search, n_content=3):
    '''Load and store up to top N pieces of local events for this search, in pandas format'''
    
    # Define N as n_content * 2 to account for double (app/web) search results - until fixed
    N = n_content*2 
    
    # Get N event IDs
    event_ids = eventbrite_get_event_ids(state, city, search, num_events=N)
    content_dict = {}
    
    # Get field content for each event id and store in pandas dataframe
    df = pd.DataFrame()
    
    content_dict['eventbrite_desc'] = []
    content_dict['eventbrite_time'] = []
    content_dict['eventbrite_url'] = []
    
    for id_ in event_ids:
    
        # Get event description, time, and url using event id - dict
        event_desc = eventbriteapi.get_event(id=id_)['description']
        event_time = eventbriteapi.get_event(id=id_)['start']['local']
        event_url = eventbriteapi.get_event(id=id_)['url']   
        
        content_dict['eventbrite_desc'].append(event_desc)
        content_dict['eventbrite_time'].append(event_time)
        content_dict['eventbrite_url'].append(event_url)
    
    # Populate the DataFrame with data from the dictionary
    df['eventbrite_desc'] = content_dict['eventbrite_desc']
    df['eventbrite_time'] = pd.to_datetime(content_dict['eventbrite_time'])
    df['eventbrite_url'] = content_dict['eventbrite_url']
    
    return df


# ### Patch API - website makeshift

# NEED TO DEFINE A FUNCTION THAT MAPS USER PREFERENCES TO THESE PATCH CATEGORIES #
categories = ['police-fire','obituaries','around-town','politics','traffic-transit','schools',
             'restaurants-bars','business','weather','sports','pets','best-of','arts-entertainment',
             'lifestyle','kids-family','going-green','holidays','personal-finance','travel']


def patch_get_content_urls(state, city, category, max_content=3):
    '''Load content urls, in list format'''
    
    # Define url template - some url parameters are fixed (ie. events, next-week, pages=1, free events)
    url_template = 'https://patch.com/{state}/{city}/{category}'
    
    # Complete url
    url = url_template.replace('{state}', state).replace('{city}', city).replace('{category}', category)
    
    # Make an HTTP GET request to retrieve the HTML content
    response = requests.get(url)

    # FIRST - IDENTIFY RECENT CONTENT
    # Check if the request was successful
    if response.status_code == 200:

        # Parse the HTML using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Find last 3 div elements with the given attributes - until content with dates can be easier identified
        div_elements = soup.find_all('span', 
                                    class_='MuiTypography-root MuiTypography-caption css-c3ysrx',
                                    limit=max_content)
        
        texts = []
        indices = []
        
        for index, div_element in enumerate(div_elements):
            try:
                text = div_element.text
                match = re.search(r'\d+d', text)
                if match:  # Check if the text contains a date
                    texts.append(match.group())
                    indices.append(index)
                else:
                    texts.append('None')
            except AttributeError:
                pass

#         return texts, indices

        # SECOND - IDENTIFY URLS FOR RECENT CONTENT
        urls = []
        
        for i in indices:
            div_elements = soup.find_all('a', 
                                        class_='MuiTypography-root MuiTypography-inherit MuiLink-root MuiLink-underlineAlways css-syvjvm',
                                        limit=max_content)
            urls.append('https://patch.com'+div_elements[0]['href'])
        
        return urls
    
    # If the request was not successful, return None or handle the error accordingly
    return None


def patch_load_content(state, city, category, max_content=3):
    '''Load and store up to top N pieces of local events content for this category, in pandas format'''
    
    # Initial check
    urls = patch_get_content_urls(state, city, category, max_content=3)
    
    if len(urls) > 0:
    
        # Define dictionary to populate pandas table
        content_dict = {}

        # Get field content for each event id and store in pandas dataframe
        df = pd.DataFrame()

        # Iterate through all recent url content
        for url in urls:
            search = state+'/'+city+'/'+category
            
            content_dict[search] = search
            content_dict['patch_content'] = []
            
            # Make an HTTP GET request to retrieve the HTML content
            response = requests.get(url)

            # Check if the request was successful
            if response.status_code == 200:
                # Parse the HTML content using BeautifulSoup
                soup = BeautifulSoup(response.content, 'html.parser')

                # Find the article content based on HTML tags or classes specific to the website
                article_content = soup.find('article', class_='styles_Section__card__4Uoov')

                # Extract the text from the article content
                article_text = article_content.get_text(separator=' ')

                # Reduce consecutive spaces to a single space
                red_space_text = re.sub(r'\s+', ' ', article_text)

                # Remove '\n' from the text
                clean_text = red_space_text.replace('\n', '')

                # Append the scraped article content to dict
                content_dict['patch_content'].append(clean_text)
                
        # Populate the DataFrame with data from the dictionary
        df['patch_content'] = content_dict['patch_content']
        
        return df
                
    else:
        return 'No recent content.'


# #### Patch events

def patch_get_event_info_url(state, city, max_content=5):
    '''Load event urls, in list format'''
    
    # Define url template - some url parameters are fixed (ie. events, next-week, pages=1, free events)
    url_template = 'https://patch.com/{state}/{city}/calendar'
    
    # Complete url
    url = url_template.replace('{state}', state).replace('{city}', city)
    
    # Make an HTTP GET request to retrieve the HTML content
    response = requests.get(url)

    # FIRST - IDENTIFY RECENT CONTENT - GET DATES
    # Check if the request was successful
    if response.status_code == 200:

        # Parse the HTML using BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')

        # Get two sperate pieces of inforamation on events - month/day and time
        # Find most recent 5 div elements - month/day
        div_elements_date = soup.find_all('div', 
                                    class_='calendar-icon__date',
                                    limit=max_content)
        
         # Find most recent 5 div elements - times
        div_elements_time = soup.find_all('time', 
                                    class_='styles_EventDateAndTime__eventDetail__TNlkQ',
                                    limit=max_content)

        # Get the current year, to append to calendar date/time
        current_year = datetime.now().year

        days = []        
        for div_element in div_elements_date:
            try:
                # Extract month and day values and format as datetime object with current year
                month = div_element.find('strong', class_='calendar-icon__month').text
                day = div_element.find('strong', class_='calendar-icon__day').text
                formatted_day = datetime.strptime(f"{month} {day} {current_year}", "%b %d %Y")
                days.append(formatted_day)
                
            except AttributeError:
                pass
        
        times = []
        for div_element in div_elements_time:
            try:
                # Extract time string
                day_time_string = div_element.text.strip().split(', ')[1]
                # day = div_element.find('strong', class_='calendar-icon__day').text
                # formatted_date = datetime.strptime(f"{month} {day} {current_year}", "%b %d %Y")
                times.append(day_time_string)
                
            except AttributeError:
                pass

        formatted_dates = []

        for date, time in zip(days, times):
            formatted_time = datetime.strptime(time, "%I:%M %p").time()
            formatted_datetime = datetime.combine(date.date(), formatted_time).isoformat()
            formatted_dates.append(formatted_datetime)

        # Make sure at LEAST one event, the earliest, is within the next 7 days
        today = date.today().date()

        # Get the first date from the list and parse the date string into a datetime object
        date_object = datetime.strptime(formatted_dates[0], '%Y-%m-%dT%H:%M:%S')
        first_date = date_object.date()

        # Calculate the difference in days
        days_diff = (first_date - today).days

        # Check if the first date is within 7 days from today
        if 0 <= days_diff <= 7:
            # SECOND - IDENTIFY URLS FOR DATED CONTENT ABOVE - GET URLS
            div_elements = soup.find_all('a', 
                                        class_='styles_Card__Thumbnail__FioCE',
                                        limit=max_content)
        
            urls = ['https://patch.com'+url['href'] for url in div_elements]
            return urls
        else:
            pass
    
    # If the request was not successful, return None or handle the error accordingly
    return 'No upcoming events'


patch_get_event_info_url('new-york','fortgreene')


