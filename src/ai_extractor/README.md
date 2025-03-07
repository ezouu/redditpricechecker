# AI-Based Price Extractor

This directory contains an AI-powered implementation of the price extraction logic using OpenAI's GPT-3.5 API. This approach offers more sophisticated price extraction capabilities compared to the rule-based system, particularly for complex cases.

## Features

- Uses OpenAI's GPT-3.5-turbo model to extract prices from Reddit posts
- Handles complex cases where multiple prices are mentioned
- Can interpret price ranges and contextual price information
- Includes connection verification functionality
- Better at understanding context and variations in price formatting

## Requirements

Additional dependency required for this implementation:
```
openai>=1.0.0
```

## Environment Variables

In addition to the Reddit API credentials, this implementation requires:
```
OPENAI_API_KEY=your_openai_api_key
```

## Usage Example

```python
from src.ai_extractor import extract_price_with_llm, verify_openai_connection

# Verify OpenAI connection
if verify_openai_connection():
    print("Successfully connected to OpenAI API")
    
    # Extract price from a post
    price = extract_price_with_llm(
        title="[WTS] HD800S - $1000",
        text="Selling my HD800S in perfect condition. Price is $1000 shipped.",
        item_name="HD800S"
    )
    print(f"Extracted price: ${price}")
```

## Comparison with Rule-Based System

The AI-based extractor has some trade-offs compared to the rule-based system:

### Advantages
1. Better handling of complex price descriptions
2. Can understand context and intent
3. More flexible with varying price formats
4. Can handle natural language price descriptions

### Considerations
1. API calls add some latency
2. Requires OpenAI API key and has associated costs
3. Depends on external service availability

Choose this implementation when you need more sophisticated price extraction capabilities or are dealing with complex post formats. 