"Interface for generating a Brief section for given NewsAPI results"

from data_loader.news_api import newsapi_load_content
from src.content_summary import get_news_summary

# User search
user_search = "film"

# Get NewsAPI content
result = newsapi_load_content(user_search)

# Summarize NewsAPI content
brief_content = get_news_summary(result, user_search)

print(brief_content)