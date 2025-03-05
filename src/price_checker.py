import praw
import os
import sys
import statistics
from datetime import datetime, timedelta
from prawcore import exceptions
from .utils.price_extractor import extract_price
from .utils.search_utils import generate_search_variations, get_time_filter

class RedditPriceChecker:
    def __init__(self):
        # Load environment variables
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

    def analyze_price_patterns(self, item_name, days_back=30, subreddits=None):
        """
        Analyze price patterns across selected subreddits
        """
        if subreddits is None:
            subreddits = ["avexchange", "photomarket"]
        
        all_results = []
        self.current_item_name = item_name
        
        # Generate search variations
        search_variations = generate_search_variations(item_name)
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
                    search_results = subreddit.search(base_query, time_filter=get_time_filter(days_back), sort="new", limit=None)
                    self._process_search_results(search_results, processed_posts, all_results, days_back)
                except Exception as e:
                    print(f"Error with base search: {str(e)}")
                
                # Then try with variations if needed
                for search_term in search_variations:
                    if len(processed_posts) == 0:  # Only continue if we haven't found anything yet
                        query = f'(title:"{search_term}" OR selftext:"{search_term}") AND {sale_tags}'
                        try:
                            search_results = subreddit.search(query, time_filter=get_time_filter(days_back), sort="new", limit=None)
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
                            search_results = subreddit.search(broad_query, time_filter=get_time_filter(days_back), sort="new", limit=None)
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
                price = extract_price(post.title, post.selftext, self.current_item_name)
                
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