# Reddit Price Checker

A tool to analyze prices of items being sold on various Reddit marketplaces.

## Features

- Search across multiple subreddits (avexchange, photomarket, hardwareswap, etc.)
- Smart model number matching (distinguishes between base models and variants)
- Price range filtering
- Statistical analysis (average, median, price range)
- Detailed listing information with URLs

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/redditpricechecker.git
cd redditpricechecker
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file in the root directory with your Reddit API credentials:
```
REDDIT_CLIENT_ID=your_client_id
REDDIT_CLIENT_SECRET=your_client_secret
REDDIT_USERNAME=your_username
REDDIT_PASSWORD=your_password
```

To get Reddit API credentials:
1. Go to https://www.reddit.com/prefs/apps
2. Click "create another app..."
3. Select "script"
4. Fill in the required information
5. Use the generated client ID and secret in your .env file

## Usage

Run the script:
```bash
python -m src.cli.main
```

Follow the prompts to:
1. Enter the item name to search for
2. Specify minimum and maximum price range
3. Choose how many days to look back
4. Select which subreddits to search

## Example

```bash
$ python -m src.cli.main
Enter item name to search: HD800
Enter minimum expected price: $500
Enter maximum expected price: $1500
Enter number of days to look back: 30

Available subreddits:
1. r/avexchange (Audio equipment)
2. r/photomarket (Photography equipment)
3. r/hardwareswap (Computer hardware)
4. r/mechmarket (Mechanical keyboards)
5. r/Watchexchange (Watches)

Your choice(s): 1
```

## Notes

- The tool distinguishes between model variants (e.g., HD800 vs HD800S)
- Prices are extracted based on proximity to the item name in the text
- Only [WTS] and [S] tagged posts are considered
- Results are sorted by date (newest first)

### Features

- Searches specified subreddit for items
- Extracts prices from post titles and content
- Displays post details including:
  - Post title
  - Found prices
  - Post date
  - Post score
  - Post URL

### Customization

You can modify the script to:
- Change the subreddit to search in
- Change the search query
- Adjust the number of results (limit parameter)
- Modify the price extraction regex pattern

## Security Note

The `.env` file containing your Reddit API credentials is automatically ignored by Git (via .gitignore) to prevent accidentally committing sensitive information. Never commit your `.env` file to version control.

## Note

The price extraction is basic and looks for "$" followed by numbers. You might need to adjust the price extraction logic based on your specific needs. 