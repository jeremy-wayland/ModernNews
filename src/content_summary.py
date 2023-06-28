"Interface for summarizing news content"

import argparse
import sys
import os
import pandas as pd
from dotenv import load_dotenv
from langchain import PromptTemplate
from langchain.chat_models import ChatOpenAI
from langchain.chains.summarize import load_summarize_chain
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.callbacks import get_openai_callback

# Define key
load_dotenv()
openai_key = os.getenv("OPENAI_KEY")

# Function to compile all content into one for OpenAI to pick out topics
def column_to_string(df):
    first_column = df.iloc[:, 0]  # Extract the first column
    aggregated_string = ', '.join(first_column.astype(str))  # Convert values to strings and join them
    return aggregated_string

# Function to summarize article content
def get_news_summary(df_news, user_search):

    # Get news for company
    content = column_to_string(df_news)

    print('content length:', len(content))

    if len(content) > 0:

        # Define OpenAI client
        llm = ChatOpenAI(temperature=0.5, model="gpt-3.5-turbo", openai_api_key=openai_key, request_timeout=120)

        # Reduce content to chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size = 4500,
            chunk_overlap  = 0
            )
        docs = text_splitter.create_documents([content])

        print('un-adjusted number of docs:', len(docs))

        if len(docs)>7:
            docs = docs[:7]
            print('adjusted number of docs:', len(docs))

        # Define separate prompts to handle docs indivdually and collectively 
        prompt_template = f"""
        Write a summary of the following document as it relates to {user_search}. Otherwise, return a blank string.""" + """
        
        Document: {text}

        Summary:
        """
        combined_prompt_template = f"""
        Given the following content, create a concise and cohesive objective editorial piece that is 6 sentences long, summarizing the 
        information as it relates to the topic of {user_search}, using a mix of journalistic and conversational language, written in Chicago style, and that is avoidant of 
        redundant language. Include a short title for the editorial piece.""" + """
        
        Content Summaries: {text}
        
        Follow this format:
        [Editorial Title, in quotation marks]
        
        [Editorial piece, in 6 sentences]
        """ 
        
        prompt = PromptTemplate(template=prompt_template, input_variables=["text"])
        combined_prompt = PromptTemplate(template=combined_prompt_template, input_variables=["text"])

        # Init Summarization Chain to summarize content chunks
        chain = load_summarize_chain(llm, chain_type="map_reduce", map_prompt=prompt, combine_prompt=combined_prompt)

        # Init Callback Handler
        with get_openai_callback() as cb:
            reduced = chain.run(docs)
        
        # Show cost to generate + details
        print(cb)

        return reduced
    
    else:
        return "No News."