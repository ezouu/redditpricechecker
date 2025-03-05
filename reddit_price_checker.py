import praw
import os
import sys
import re
import statistics
from datetime import datetime, timedelta
from dotenv import load_dotenv
from prawcore import exceptions
from collections import defaultdict

class RedditPriceChecker:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        # Verify environment variables are loaded
        required_vars = ['REDDIT_CLIENT_ID', 'REDDIT_CLIENT_SECRET', 'REDDIT_USERNAME', 'REDDIT_PASSWORD']
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            print(f"Error: Missing environment variables: {', '.join(missing_vars)}")
            sys.exit(1)

        # Debug: Print credential status (not the actual values)
        print("Checking credentials:")
        for var in required_vars:
            value = os.getenv(var)
            print(f"{var}: {'✓ Loaded' if value else '✗ Missing'} (Length: {len(value) if value else 0})")

        try:
            # Get credentials from environment variables
            self.reddit = praw.Reddit(
                client_id=os.getenv('REDDIT_CLIENT_ID').strip(),
                client_secret=os.getenv('REDDIT_CLIENT_SECRET').strip(),
                username=os.getenv('REDDIT_USERNAME').strip(),
                password=os.getenv('REDDIT_PASSWORD').strip(),
                user_agent="script:com.redditpricechecker:v1.0 (by /u/ezouu)",
                check_for_updates=False,
                ratelimit_seconds=300
            )
            
            # Test authentication with a simple read-only operation first
            print("\nTesting connection...")
            self.reddit.read_only = True
            test_subreddit = self.reddit.subreddit("avexchange")
            test_subreddit.title
            print("Read-only connection successful!")
            
            # Now try full authentication
            print("Verifying full authentication...")
            self.reddit.read_only = False
            self.reddit.user.me()
            print("Full authentication successful!")
            
        except exceptions.OAuthException as e:
            print(f"\nAuthentication Error: {e}")
            print("\nTroubleshooting steps:")
            print("1. Verify your Reddit password by logging in to Reddit in your browser")
            print("2. Check that your app credentials match exactly with https://www.reddit.com/prefs/apps")
            print("3. Make sure there are no extra spaces in your credentials")
            sys.exit(1)
        except Exception as e:
            print(f"\nInitialization Error: {str(e)}")
            print(f"Error type: {type(e).__name__}")
            sys.exit(1)

    def _generate_search_variations(self, item_name):
        """
        Generate variations of the search term to catch different formats while maintaining model accuracy
        """
        # Remove extra spaces and standardize spacing around model numbers
        base_term = re.sub(r'\s+', ' ', item_name).strip()
        
        # Split into parts for more precise matching
        parts = base_term.split()
        
        # Generate variations
        variations = set()
        
        # Add the exact term first
        variations.add(base_term)
        
        # Handle common format variations while preserving model number integrity
        if len(parts) > 1:
            # Get the model number (usually the last part)
            model_number = parts[-1]
            brand_name = ' '.join(parts[:-1])
            
            # Add variations that preserve the model number exactly
            variations.add(f"{brand_name}{model_number}")  # No space
            variations.add(f"{brand_name}-{model_number}")  # With hyphen
            variations.add(model_number)  # Just the model
            
            # Add case variations but keep model number exact
            variations.add(base_term.lower())
            variations.add(base_term.upper())
            variations.add(base_term.title())
            
            # Handle specific model number patterns
            if re.match(r'^[A-Za-z]+\d+$', model_number):  # Like HD800
                # Add space between letters and numbers
                letter_part = re.match(r'^[A-Za-z]+', model_number).group()
                number_part = re.match(r'\d+', model_number[len(letter_part):]).group()
                variations.add(f"{brand_name} {letter_part} {number_part}")
                variations.add(f"{brand_name} {letter_part}{number_part}")
        
        return variations

    def _get_time_filter(self, days):
        """
        Convert days to appropriate Reddit time filter
        """
        if days <= 1:
            return "day"
        elif days <= 7:
            return "week"
        elif days <= 31:
            return "month"
        elif days <= 365:
            return "year"
        else:
            return "all"

    def analyze_price_patterns(self, item_name, days_back=30, subreddits=None):
        """
        Analyze price patterns across selected subreddits
        """
        if subreddits is None:
            subreddits = ["avexchange", "photomarket"]
        
        all_results = []
        self.current_item_name = item_name
        
        # Generate search variations
        search_variations = self._generate_search_variations(item_name)
        print(f"\nSearching for variations: {', '.join(sorted(search_variations))}")
        
        # Sale post identifiers
        sale_tags = '(title:"[WTS]" OR title:"[S]")'
        
        for subreddit_name in subreddits:
            try:
                print(f"\nSearching in r/{subreddit_name}...")
                subreddit = self.reddit.subreddit(subreddit_name)
                processed_posts = set()
                
                # First try searching with just the base query
                base_query = f'(title:"{item_name}" OR selftext:"{item_name}") AND {sale_tags}'
                
                try:
                    search_results = subreddit.search(base_query, time_filter=self._get_time_filter(days_back), sort="new", limit=None)
                    self._process_search_results(search_results, processed_posts, all_results, days_back)
                except Exception as e:
                    print(f"Error with base search: {str(e)}")
                
                # Then try with variations if needed
                for search_term in search_variations:
                    if len(processed_posts) == 0:  # Only continue if we haven't found anything yet
                        query = f'(title:"{search_term}" OR selftext:"{search_term}") AND {sale_tags}'
                        try:
                            search_results = subreddit.search(query, time_filter=self._get_time_filter(days_back), sort="new", limit=None)
                            self._process_search_results(search_results, processed_posts, all_results, days_back)
                        except Exception as e:
                            continue
                
                if len(processed_posts) == 0:
                    print(f"No results found in r/{subreddit_name}. Trying broader search...")
                    # Try one more time with a very broad search
                    broad_terms = item_name.split()
                    if len(broad_terms) > 1:
                        broad_query = f'title:"{broad_terms[-1]}" AND {sale_tags}'  # Search just the model number
                        try:
                            search_results = subreddit.search(broad_query, time_filter=self._get_time_filter(days_back), sort="new", limit=None)
                            self._process_search_results(search_results, processed_posts, all_results, days_back)
                        except Exception as e:
                            print(f"Error with broad search: {str(e)}")
                
            except Exception as e:
                print(f"Error searching r/{subreddit_name}: {str(e)}")
                continue

        if not all_results:
            print(f"\nNo results found for '{item_name}' in the past {days_back} days.")
            return

        self._analyze_results(all_results, item_name)

    def _process_search_results(self, search_results, processed_posts, all_results, days_back):
        """
        Process search results and add them to all_results
        """
        for post in search_results:
            if post.id in processed_posts:
                continue
                
            created_date = datetime.fromtimestamp(post.created_utc)
            if datetime.now() - created_date <= timedelta(days=days_back):
                # Extract price using rule-based approach
                price = self._extract_price(post.title, post.selftext, self.current_item_name)
                
                # Only include prices within the specified range
                if price and self.min_price <= price <= self.max_price:
                    processed_posts.add(post.id)
                    all_results.append({
                        'subreddit': post.subreddit.display_name,
                        'title': post.title,
                        'url': post.url,
                        'date': created_date.strftime('%Y-%m-%d %H:%M:%S'),
                        'author': str(post.author),
                        'price': price
                    })
                    print(f"\nFound: {post.title}")
                    print(f"Price: ${price:.2f}")
                elif price:
                    print(f"\nSkipped (price outside range ${self.min_price:.2f}-${self.max_price:.2f}): {post.title}")
                    print(f"Found price: ${price:.2f}")

    def _extract_price(self, title, text, item_name):
        """
        Extract price based on proximity to item name and position rules
        """
        def find_prices(text):
            # Find all prices in the text
            price_matches = []
            
            # Standard price format with $ symbol
            dollar_prices = re.finditer(r'\$\s*(\d{1,3}(?:,\d{3})*|\d+)(?:\.\d{2})?', text)
            for match in dollar_prices:
                price = float(match.group(1).replace(',', ''))
                price_matches.append({
                    'price': price,
                    'position': match.start(),
                    'text': match.group(0)
                })
            
            # Prices with keywords
            keyword_prices = re.finditer(r'(?:asking|price|selling for|for)\s*\$?\s*(\d{1,4})', text, re.IGNORECASE)
            for match in keyword_prices:
                price = float(match.group(1))
                price_matches.append({
                    'price': price,
                    'position': match.start(),
                    'text': f"${match.group(1)}"
                })
            
            return price_matches

        def find_item_positions(text, item_name):
            """
            Find positions of the item name with exact model number matching,
            being careful to distinguish between base models and their variants
            """
            item_positions = []
            text = text.lower()
            item_name = item_name.lower()
            
            # Split the item name into brand and model
            parts = item_name.split()
            if len(parts) > 1:
                model_number = parts[-1]
                
                # Find all potential matches first
                base_pattern = r'\b' + re.escape(model_number)
                for match in re.finditer(base_pattern, text):
                    start_pos = match.start()
                    end_pos = match.end()
                    
                    # Look at what comes after the match
                    next_chars = text[end_pos:end_pos+2].strip()  # Get next 2 chars to check for variants
                    
                    # If we're looking for a base model (e.g., HD800)
                    if not any(c.isalpha() for c in model_number[-2:]):  # If model doesn't end in letters
                        # Only match if what follows isn't a model variant indicator
                        if not next_chars or next_chars[0] not in 'si':  # 's' for S variant, 'i' for i variant
                            item_positions.append(start_pos)
                    # If we're looking for a specific variant (e.g., HD800S)
                    else:
                        # Must match the variant exactly
                        if not next_chars or not next_chars[0].isalnum():
                            item_positions.append(start_pos)
            else:
                # If it's just one word, use exact matching
                pattern = r'\b' + re.escape(item_name) + r'\b'
                for match in re.finditer(pattern, text):
                    item_positions.append(match.start())
            
            return item_positions

        # First check the title for a simple case
        title = title.lower()
        item_name = item_name.lower()
        
        # If title contains exactly one instance of the item and one price
        title_prices = find_prices(title)
        title_item_count = len(find_item_positions(title, item_name))
        
        if title_item_count == 1 and len(title_prices) == 1:
            # Simple case: one item, one price in title
            return title_prices[0]['price']
            
        # Check for multiple items with corresponding prices in title
        if title_item_count > 0 and len(title_prices) > 0:
            # Split title into parts by common separators
            parts = re.split(r'[,/|+]', title)
            for part in parts:
                if item_name in part.lower():
                    part_prices = find_prices(part)
                    if len(part_prices) == 1:
                        # Found a part with our item and exactly one price
                        return part_prices[0]['price']

        # If no clear match in title, analyze the full text
        full_text = f"{title}\n{text}".lower()
        prices = find_prices(full_text)
        item_positions = find_item_positions(full_text, item_name)
        
        if not prices or not item_positions:
            return None
            
        # Find the best matching price based on proximity and position rules
        best_price = None
        min_distance = float('inf')
        
        for item_pos in item_positions:
            for price_info in prices:
                price_pos = price_info['position']
                
                # Calculate distance
                distance = abs(price_pos - item_pos)
                
                # Prioritize prices that come after the item name
                if price_pos > item_pos:
                    distance *= 0.5  # Give preference to prices after the item
                
                if distance < min_distance:
                    min_distance = distance
                    best_price = price_info['price']
        
        return best_price

    def _analyze_results(self, results, item_name):
        """
        Analyze the found results and display statistics
        """
        if not results:
            print("\nNo results found to analyze.")
            return

        # Sort results by date
        results.sort(key=lambda x: x['date'], reverse=True)
        
        # Extract prices for analysis
        prices = [r['price'] for r in results]
        
        # Calculate statistics
        avg_price = statistics.mean(prices)
        median_price = statistics.median(prices)
        
        print("\nPrice Analysis Results:")
        print("-" * 80)
        print(f"\nTotal listings found: {len(results)}")
        print(f"Average price: ${avg_price:.2f}")
        print(f"Median price: ${median_price:.2f}")
        print(f"Price range: ${min(prices):.2f} - ${max(prices):.2f}")
        
        print("\nDetailed Listings (Most Recent First):")
        for result in results:
            print(f"\nDate: {result['date']}")
            print(f"Price: ${result['price']:.2f}")
            print(f"Subreddit: r/{result['subreddit']}")
            print(f"Seller: u/{result['author']}")
            print(f"URL: {result['url']}")
            print(f"Title: {result['title']}")

def main():
    try:
        # Initialize the price checker
        price_checker = RedditPriceChecker()

        # Get user input
        print("\nReddit Price Checker - Price Analysis")
        print("-" * 80)
        
        # Get item name
        item_name = input("Enter item name to search (e.g., 'Sony A7III' or 'HD800'): ")
        
        # Get price range
        while True:
            try:
                min_price = float(input("Enter minimum expected price (e.g., 500): $"))
                max_price = float(input("Enter maximum expected price (e.g., 1500): $"))
                if min_price > 0 and max_price > min_price:
                    break
                print("Invalid range. Maximum price must be greater than minimum price.")
            except ValueError:
                print("Please enter valid numbers.")
        
        # Get number of days
        days = input("Enter number of days to look back (default 30): ")
        days = int(days) if days.strip() else 30
        
        # Get subreddits to search
        print("\nAvailable subreddits:")
        print("1. r/avexchange (Audio equipment)")
        print("2. r/photomarket (Photography equipment)")
        print("3. r/hardwareswap (Computer hardware)")
        print("4. r/mechmarket (Mechanical keyboards)")
        print("5. r/Watchexchange (Watches)")
        print("Enter numbers separated by commas, or press Enter for default (avexchange, photomarket)")
        
        subreddit_choices = input("Your choice(s): ").strip()
        
        # Map of numbers to subreddit names
        subreddit_map = {
            "1": "avexchange",
            "2": "photomarket",
            "3": "hardwareswap",
            "4": "mechmarket",
            "5": "Watchexchange"
        }
        
        if subreddit_choices:
            selected_subreddits = []
            for choice in subreddit_choices.split(','):
                choice = choice.strip()
                if choice in subreddit_map:
                    selected_subreddits.append(subreddit_map[choice])
        else:
            selected_subreddits = ["avexchange", "photomarket"]
        
        # Store price range in the class
        price_checker.min_price = min_price
        price_checker.max_price = max_price
        
        # Analyze prices with selected subreddits
        price_checker.analyze_price_patterns(item_name, days, selected_subreddits)
    
    except KeyboardInterrupt:
        print("\nScript terminated by user.")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main() 