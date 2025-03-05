from dotenv import load_dotenv
from ..price_checker import RedditPriceChecker

def main():
    try:
        # Load environment variables
        load_dotenv()
        
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