import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import json
import anthropic

# Load environment variables from .env file
load_dotenv()

SERP_API_KEY = os.getenv('SERP_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

def search_articles(query):
    """
    Searches for articles related to the query using the serper.dev API.
    Returns a list of dictionaries containing article URLs, titles, and snippets.
    """
    url = "https://google.serper.dev/search"
    
    headers = {
        'X-API-KEY': SERP_API_KEY,
        'Content-Type': 'application/json'
    }
    payload = json.dumps({"q": query})

    print(f"Using API Key: {SERP_API_KEY[:5]}...{SERP_API_KEY[-5:]}")
    print(f"Query: {query}")
    print(f"Request URL: {url}")

    try:
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        data = response.json()

        articles = []
        if 'organic' in data and isinstance(data['organic'], list):
            for result in data['organic']:
                article = {
                    'url': result.get('link'),
                    'title': result.get('title'),
                    'snippet': result.get('snippet', 'No snippet available')
                }
                articles.append(article)
        
        print(f"Retrieved articles: {articles}")
        return articles

    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP error occurred: {http_err}")
        print(f"Response content: {response.content}")
        return []
    except Exception as err:
        print(f"Other error occurred: {err}")
        return []

def fetch_article_content(url):
    """
    Fetches the article content, extracting headings and text.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        headings = [heading.get_text(strip=True) for heading in soup.find_all(['h1', 'h2', 'h3'])]
        paragraphs = [paragraph.get_text(strip=True) for paragraph in soup.find_all('p')]

        content = "\n".join(headings) + "\n\n" + "\n".join(paragraphs)
        return content.strip()

    except requests.exceptions.RequestException as e:
        print(f"Error fetching article content: {e}")
        return ""

def fetch_top_webpage_content(query):
    """
    Fetches the content of the top webpage for the given query and extracts text.
    If web scraping fails, uses the search result snippets.
    """
    try:
        # Step 1: Use Serper.dev API to get the top search results
        articles = search_articles(query)
        
        if not articles:
            print("No articles found for the given query")
            return ""
        
        # Get the URL of the top search result
        top_url = articles[0].get('url')
        
        if not top_url:
            print("No URL found in search results")
            return ""

        # Step 2: Attempt to fetch the content of the top webpage
        content = fetch_article_content(top_url)
        
        # If web scraping fails, use the snippets from search results
        if not content:
            print("Web scraping failed. Using search result snippets.")
            content = "\n\n".join([article['snippet'] for article in articles[:3]])
        
        # Limit to three paragraphs
        paragraphs = content.split('\n\n')[:3]
        return '\n\n'.join(paragraphs)

    except Exception as e:
        print(f"Error in fetch_top_webpage_content: {e}")
        return ""


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