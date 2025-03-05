import re

def generate_search_variations(item_name):
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

def get_time_filter(days):
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