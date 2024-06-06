import streamlit as st
import json
import re
from datetime import datetime
from fractions import Fraction
from pint import UnitRegistry
import pandas as pd

# Initialize Unit Registry for Pint
ureg = UnitRegistry()

# Initialize Session State
if 'recipe_name' not in st.session_state:
    st.session_state.recipe_name = ''
if 'recipe_text' not in st.session_state:
    st.session_state.recipe_text = ''
if 'original_servings' not in st.session_state:
    st.session_state.original_servings = 1
if 'desired_servings' not in st.session_state:
    st.session_state.desired_servings = 1
if 'ingredients' not in st.session_state:
    st.session_state.ingredients = []
if 'errors' not in st.session_state:
    st.session_state.errors = []

def clear_recipe():
    st.session_state.recipe_name = ''
    st.session_state.recipe_text = ''
    st.session_state.original_servings = 1
    st.session_state.desired_servings = 1
    st.session_state.ingredients = []
    st.session_state.errors = []

def log_error(error_message):
    st.session_state.errors.append(error_message)
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

def convert_to_fraction(amount_str):
    try:
        return Fraction(amount_str)
    except ValueError:
        # Handle mixed fractions like "1 1/2"
        parts = amount_str.split()
        if len(parts) == 2:
            whole_part = Fraction(parts[0])
            fraction_part = Fraction(parts[1])
            return whole_part + fraction_part
        else:
            raise ValueError(f"Invalid literal for Fraction: '{amount_str}'")

def input_recipe():
    st.title("Recipe Input")
    
    with st.expander("Upload Recipe"):
        st.session_state.recipe_name = st.text_input("Recipe Name", st.session_state.recipe_name)
        uploaded_file = st.file_uploader("Upload Recipe (JSON or TXT)", type=['json', 'txt'])

        if uploaded_file is not None:
            if uploaded_file.type == "application/json":
                recipe_data = json.load(uploaded_file)
                st.session_state.recipe_text = recipe_data['recipe_text']
                st.session_state.original_servings = recipe_data['servings']
                st.session_state.ingredients = recipe_data['ingredients']
            elif uploaded_file.type == "text/plain":
                st.session_state.recipe_text = uploaded_file.getvalue().decode("utf-8")

        st.write("### Expected Recipe Input Format:")
        st.write("Each ingredient should be on a new line in the format: 'amount unit ingredient'. Example: '1 cup sugar'.")
        
    st.session_state.recipe_text = st.text_area("Recipe Text", st.session_state.recipe_text)
    if st.button("Parse Recipe"):
        st.session_state.ingredients = []
        st.session_state.errors = []
        for line in st.session_state.recipe_text.split('\n'):
            ingredient = parse_ingredient_line(line)
            if ingredient:
                st.session_state.ingredients.append(ingredient)
            else:
                log_error(f"Failed to parse line: {line}")

    st.write("### Ingredients")
    ingredients_df = pd.DataFrame(st.session_state.ingredients)
    st.write(ingredients_df)
    
    if st.session_state.errors:
        st.write("### Errors:")
        for error in st.session_state.errors:
            st.write(error)

def edit_recipe():
    st.title("Edit Recipe")
    st.write("Edit the ingredients of the recipe below:")
    ingredients_df = pd.DataFrame(st.session_state.ingredients)
    edited_df = st.data_editor(ingredients_df)
    st.session_state.ingredients = edited_df.to_dict('records')
    
    if st.button("Update Ingredients"):
        st.success("Ingredients updated.")
    
    if st.button("Clear Ingredients"):
        st.session_state.ingredients = []

def scale_ingredients(scale_factor):
    scaled_ingredients = []
    for ingredient in st.session_state.ingredients:
        try:
            if ingredient['amount']:
                original_amount = convert_to_fraction(ingredient['amount'])
                scaled_amount = original_amount * scale_factor
                ingredient['amount'] = str(scaled_amount)
            scaled_ingredients.append(ingredient)
        except Exception as e:
            log_error(f"Failed to scale ingredient: {ingredient} - Error: {e}")
    return scaled_ingredients

def convert_units(ingredients, to_metric=True):
    for ingredient in ingredients:
        try:
            if ingredient['amount']:
                original_amount = ureg(ingredient['amount'] + " " + ingredient['unit'])
                if to_metric:
                    converted_amount = original_amount.to_base_units()
                else:
                    converted_amount = original_amount.to('imperial_pint')
                ingredient['amount'] = str(converted_amount.magnitude)
                ingredient['unit'] = str(converted_amount.units)
        except Exception as e:
            log_error(f"Failed to convert ingredient units: {ingredient} - Error: {e}")
    return ingredients

def scale_and_convert_recipe():
    st.title("Scale and Convert Recipe")
    
    with st.expander("Scale Recipe"):
        st.write("Specify the desired number of servings to scale the recipe accordingly.")
        st.session_state.desired_servings = st.number_input("Desired Servings", min_value=1, value=st.session_state.desired_servings)
        
        if st.session_state.original_servings == 0:
            scale_factor = 1
        else:
            scale_factor = st.session_state.desired_servings / st.session_state.original_servings

        scaled_ingredients = scale_ingredients(scale_factor)

        st.write("### Scaled Ingredients:")
        scaled_ingredients_df = pd.DataFrame(scaled_ingredients)
        st.write(scaled_ingredients_df)

    with st.expander("Convert Units"):
        st.write("### Conversion Options:")
        if st.button("Convert to Metric"):
            scaled_ingredients = convert_units(scaled_ingredients, to_metric=True)
        
        if st.button("Convert to Imperial"):
            scaled_ingredients = convert_units(scaled_ingredients, to_metric=False)

    display_as_fractions = st.checkbox("Display amounts as fractions", value=True)
    
    st.write("### Scaled and Converted Recipe:")
    for ingredient in scaled_ingredients:
        amount = ingredient['amount']
        if display_as_fractions and amount:
            try:
                amount = Fraction(amount)
            except ValueError:
                pass
        st.write(f"{amount} {ingredient['unit']} {ingredient['ingredient']}")
    
    if st.session_state.errors:
        st.write("### Errors:")
        for error in st.session_state.errors:
            st.write(error)

def save_recipe():
    st.title("Save Recipe")
    recipe_data = {
        "recipe_name": st.session_state.recipe_name,
        "recipe_text": st.session_state.recipe_text,
        "servings": st.session_state.desired_servings,
        "ingredients": st.session_state.ingredients
    }
    with open('recipe.json', 'w') as f:
        json.dump(recipe_data, f)
    with open('recipe.txt', 'w') as f:
        f.write(st.session_state.recipe_text)
    st.success("Recipe saved.")
    
    # Provide a download link for the JSON file
    st.download_button(
        label="Download Recipe as JSON",
        data=json.dumps(recipe_data),
        file_name="recipe.json",
        mime="application/json"
    )

def navigation():
    st.sidebar.title("AI Recipe Tool")
    page = st.sidebar.radio("Navigation", ["Enter Recipe", "Edit Ingredients", "Scale & Convert", "Save Recipe"])
    
    if page == "Enter Recipe":
        input_recipe()
    elif page == "Edit Ingredients":
        edit_recipe()
    elif page == "Scale & Convert":
        scale_and_convert_recipe()
    elif page == "Save Recipe":
        save_recipe()
    
    if st.sidebar.button("Clear Recipe"):
        clear_recipe()
        st.success("Recipe cleared.")

# Main application
def main():
    navigation()

if __name__ == "__main__":
    main()
