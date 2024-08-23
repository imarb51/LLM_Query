import os
import openai
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
# Load environment variables from .env file
from dotenv import load_dotenv
import anthropic
import os

load_dotenv()

SERP_API_KEY = os.getenv('SERP_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

def search_articles(query):
    """
    Searches for articles related to the query using SerpAPI.
    Returns a list of dictionaries containing article URLs, titles, and snippets.
    """
    url = "https://serpapi.com/search.json"  # Correct base URL for SerpAPI

    # Query parameters for the search
    params = {
        "engine": "google",  # Use Google engine
        "q": query,  # The search query
        "api_key": SERP_API_KEY  # API key from .env
    }

    # Debugging
    # print(f"Using SERP_API_KEY: {SERP_API_KEY}")
    # print(f"Query: {query}")
    
    try:
        # Make the GET request
        response = requests.get(url, params=params)
        
        
        # Check for HTTP errors
        response.raise_for_status()

        # Parse the response JSON
        data = response.json()
        

        articles = []

        # Extract relevant article information
        for result in data.get('organic_results', []):
            article = {
                'url': result.get('link'),
                'title': result.get('title'),
                'snippet': result.get('snippet')
            }
            articles.append(article)

        # Return the list of articles
        return articles

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        return None
    except Exception as err:
        print(f"Other error occurred: {err}")
        return None


# Now we have got the content

def fetch_article_content(url):
    """
    Fetches the article content, extracting headings and text.
    """
    try:
        # Make the GET request to fetch the article HTML
        response = requests.get(url)
        response.raise_for_status()  # Raise an error for HTTP issues

        # Parse the HTML content
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract headings (h1, h2, h3) and paragraphs
        headings = []
        paragraphs = []
        
        for heading in soup.find_all(['h1', 'h2', 'h3']):
            headings.append(heading.get_text(strip=True))
        
        for paragraph in soup.find_all('p'):
            paragraphs.append(paragraph.get_text(strip=True))
        
        # Combine headings and paragraphs into a single string
        content = "\n".join(headings) + "\n\n" + "\n".join(paragraphs)
        
        return content.strip()

    except requests.exceptions.RequestException as e:
        print(f"Error fetching article content: {e}")
        return ""

def fetch_top_webpage_content(query):
    """
    Fetches the content of the top webpage for the given query and extracts text.
    Limits the content to no more than three paragraphs.
    """
    # Step 1: Use SerpAPI to get the top search result URL
    serp_api_key = os.getenv('SERP_API_KEY')
    serp_url = "https://serpapi.com/search.json"
    params = {
        "engine": "google",
        "q": query,
        "api_key": serp_api_key
    }
    
    response = requests.get(serp_url, params=params)
    response.raise_for_status()
    data = response.json()
    
    # Get the URL of the top search result
    top_url = data.get('organic_results', [])[0].get('link')
    
    if not top_url:
        raise ValueError("No URL found in search results")
    
    # Step 2: Fetch the content of the top webpage
    webpage_response = requests.get(top_url)
    webpage_response.raise_for_status()
    soup = BeautifulSoup(webpage_response.content, 'html.parser')
    
    # Extract text from paragraphs
    paragraphs = soup.find_all('p')
    content = ""
    for p in paragraphs[:3]:  # Limit to the first three paragraphs
        content += p.get_text() + "\n\n"
    
    return content.strip()




def generate_answer(content, query, conversation_history):
    conversation_string = "\n".join([f"{msg.type}: {msg.content}" for msg in conversation_history])
    
    prompt = f"""
    You are an AI assistant and should provide an accurate and contextual answer based on the following content, query, and conversation history.

    Content: {content}

    User Query: {query}

    Conversation History:
    {conversation_string}

    Please provide a response that takes into account the conversation history and the current query.
    """
    
    try:
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        
        message = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=1000,
            temperature=0.1,
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        
        if message.content and len(message.content) > 0:
            return message.content[0].text
        else:
            return "I apologize, but I couldn't generate a response. Could you please rephrase your question?"
    
    except Exception as e:
        print(f"An error occurred in generate_answer: {e}")
        return "I'm sorry, but an error occurred while processing your request. Please try again later."