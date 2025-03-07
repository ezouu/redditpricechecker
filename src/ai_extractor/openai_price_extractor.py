from openai import OpenAI
import os
import re

def extract_price_with_llm(title, text, item_name):
    """
    Use OpenAI's API to extract price information from the post
    """
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Prepare the prompt
    prompt = f"""
    Extract the selling price for a {item_name} from this Reddit post.
    If multiple prices are mentioned, determine which one corresponds to the {item_name}.
    If a price range is given, use the lower price.
    Only respond with the numeric price value (e.g., "500" or "1200.50").
    If no clear price is found, respond with "None".

    Post Title: {title}
    Post Content: {text}
    """

    try:
        # Make API call with error handling and retry logic
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that extracts price information from Reddit posts. Only respond with the numeric price value or 'None'."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,  # Use deterministic output
            max_tokens=10   # We only need a short response
        )
        
        # Extract price from response
        price_str = response.choices[0].message.content.strip()
        
        # Convert to float if possible
        try:
            if price_str.lower() == 'none':
                return None
            # Remove any non-numeric characters except decimal point
            price_str = re.sub(r'[^\d.]', '', price_str)
            return float(price_str)
        except (ValueError, TypeError):
            return None
            
    except Exception as e:
        print(f"Error extracting price with LLM: {str(e)}")
        return None

def verify_openai_connection():
    """
    Verify connection to OpenAI API
    """
    try:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Make a minimal API call
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Respond with the word 'connected'"},
                {"role": "user", "content": "Test connection"}
            ],
            temperature=0,
            max_tokens=5
        )
        
        if response.choices[0].message.content.strip().lower() == 'connected':
            return True
        return False
        
    except Exception as e:
        print(f"OpenAI API connection test failed: {str(e)}")
        return False 