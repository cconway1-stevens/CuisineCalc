import re
from fractions import Fraction
from datetime import datetime
import json

def log_error(error_message):
    print(f"Error: {error_message}")
    error_log = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "error": error_message
    }
    with open('error_log.json', 'a') as f:
        json.dump(error_log, f)
        f.write('\n')

def parse_ingredient_line(line):
    try:
        if not line.strip():
            return None
        
        # Match the amount (including fractions), unit, and ingredient
        amount_unit_regex = re.compile(r'(\d+\s*\d*/?\d*)\s*([a-zA-Z]+)?\s*(.*)')
        match = amount_unit_regex.match(line.strip())
        if not match:
            # Check for cases like "Vodka 1 oz"
            amount_unit_regex_alt = re.compile(r'(.+)\s+(\d+\s*\d*/?\d*)\s*([a-zA-Z]+)')
            match_alt = amount_unit_regex_alt.match(line.strip())
            if not match_alt:
                # Check for lines with only ingredients
                return {"amount": "", "unit": "", "ingredient": line.strip()}
            
            ingredient = match_alt.group(1).strip()
            amount = match_alt.group(2).strip()
            unit = match_alt.group(3).strip()
        else:
            amount = match.group(1).strip()
            unit = match.group(2).strip() if match.group(2) else ''
            ingredient = match.group(3).strip()

        return {
            "amount": amount,
            "unit": unit,
            "ingredient": ingredient
        }
    except Exception as e:
        log_error(f"Failed to parse line: {line} - Error: {e}")
        return None

def test_parse_ingredient_line():
    test_cases = [
        ("1 1/2 cups (355 ml) warm water (105°F-115°F)", {"amount": "1 1/2", "unit": "cups", "ingredient": "(355 ml) warm water (105°F-115°F)"}),
        ("1 package (2 1/4 teaspoons) active dry yeast", {"amount": "1", "unit": "package", "ingredient": "(2 1/4 teaspoons) active dry yeast"}),
        ("3 3/4 cups (490g) bread flour", {"amount": "3 3/4", "unit": "cups", "ingredient": "(490g) bread flour"}),
        ("2 tablespoons extra virgin olive oil (omit if cooking pizza in a wood-fired pizza oven)", {"amount": "2", "unit": "tablespoons", "ingredient": "extra virgin olive oil (omit if cooking pizza in a wood-fired pizza oven)"}),
        ("2 teaspoons kosher salt", {"amount": "2", "unit": "teaspoons", "ingredient": "kosher salt"}),
        ("1 teaspoon sugar", {"amount": "1", "unit": "teaspoon", "ingredient": "sugar"}),
        ("Vodka 1 oz", {"amount": "1", "unit": "oz", "ingredient": "Vodka"}),
        ("Cranberry juice 4 oz", {"amount": "4", "unit": "oz", "ingredient": "Cranberry juice"}),
        ("Pineapple juice 4 oz", {"amount": "4", "unit": "oz", "ingredient": "Pineapple juice"}),
        ("Soda water 4 oz", {"amount": "4", "unit": "oz", "ingredient": "Soda water"}),
        ("Fresh berries (for garnish)", {"amount": "", "unit": "", "ingredient": "Fresh berries (for garnish)"}),
        ("Mint leaf (for garnish)", {"amount": "", "unit": "", "ingredient": "Mint leaf (for garnish)"})
    ]
    
    for line, expected_output in test_cases:
        actual_output = parse_ingredient_line(line)
        print(f"Test case: {line}")
        print(f"Expected output: {expected_output}")
        print(f"Actual output: {actual_output}")
        assert actual_output == expected_output

if __name__ == "__main__":
    test_parse_ingredient_line()
