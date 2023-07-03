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
from langchain.chains import LLMChain

# Define key
load_dotenv()
openai_key = os.getenv("OPENAI_KEY")

# Function to compile all content into one for OpenAI to pick out topics
def column_to_string(df):
    content = df.loc[:,"newsapi_content"] + \
        "publication: " + df.loc[:,"newsapi_publication"] + \
        "author: " + df.loc[:,"newsapi_author"] # Extract the first column
    aggregated_string = ', '.join(content.astype(str))  # Convert values to strings and join them
    return aggregated_string

# Function to summarize article content
def get_news_summary(df_news, user_search):

    # Get news for company
    content = column_to_string(df_news)

    if len(content) > 0:

        print("Original content length:", len(content))

        # Reduce amount of content
        content = content[:14975]

        # Define OpenAI client
        llm = ChatOpenAI(temperature=0.8, model="gpt-3.5-turbo", openai_api_key=openai_key, request_timeout=120)

        # Reduce content to chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size = 5000,
            chunk_overlap  = 0
            )
        docs = text_splitter.create_documents([content])

        combined_prompt_template = f"""
        Create a concise and cohesive news editorial on the topic of {user_search} given the following content. Do not mention or include any content that does not relate to {user_search}. The report should be a single paragraph 6 sentences long. 
        Use a mix of journalistic and conversational language, adhering to Chicago style guidelines. When referencing specific parts of the content, credit the publication or author by name if provided.""" + """
        
        Content: {text}

        Please follow this format:
        [Editorial Title, in quotation marks]

        [Editorial Body, in 5 sentences]
        """
        
        # prompt = PromptTemplate(template=prompt_template, input_variables=["text"])
        combined_prompt = PromptTemplate(template=combined_prompt_template, input_variables=["text"])

        # Init Summarization Chain to summarize content chunks
        chain = load_summarize_chain(llm, chain_type="map_reduce", combine_prompt=combined_prompt)

        # Init Callback Handler
        with get_openai_callback() as cb:

            reduced = chain.run(docs)

            break_count = reduced.count("\n")

            # Check if content exceeds 1 paragraph
            if break_count > 2:

                print('Content too long, adjusting...')
            
                # Define an LLM to summarize the content
                prompt = PromptTemplate.from_template("""Rewrite the following editorial in a single paragraph less than 6 sentences in length, while maintaining all attribution of sources. 
                Editorial: {editorial}
                
                Please follow this format:
                [Editorial Title, in quotation marks]

                [Editorial Body]""")

                # Chaining to Init Callback Handler
                chain = LLMChain(llm=llm, prompt=prompt)
                reduced_final = chain.run(reduced)

                return cb, reduced_final

            else:
                return cb, reduced
    
    else:
        return "No News."