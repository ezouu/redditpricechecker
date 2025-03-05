import re

def find_prices(text):
    """
    Find all prices in the text with their positions
    """
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

def extract_price(title, text, item_name):
    """
    Extract price based on proximity to item name and position rules
    """
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