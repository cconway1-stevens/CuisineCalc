import streamlit as st
import json
from pint import UnitRegistry
import re
from fractions import Fraction

# Initialize pint's UnitRegistry
ureg = UnitRegistry()

# Add custom units
ureg.define("piece = []")

# Function to convert units using pint
def convert_units(amount, from_unit, to_unit):
    try:
        amount = float(amount)
        from_quantity = amount * ureg(from_unit)
        to_quantity = from_quantity.to(to_unit)
        return to_quantity.magnitude, to_unit
    except Exception as e:
        st.error(f"Error converting units: {e}")
        return None, None

# Function to scale the recipe
def scale_recipe(ingredients, original_servings, desired_servings):
    scale_factor = desired_servings / original_servings
    scaled_ingredients = []
    for ingredient in ingredients:
        name, amount, unit = ingredient
        scaled_amount = amount * scale_factor
        scaled_ingredients.append((name, scaled_amount, unit))
    return scaled_ingredients

# Function to parse ingredient amounts
def parse_amount(amount_str):
    try:
        # Check for fractions (e.g., "1 1/2" or "1/2")
        if " " in amount_str:
            whole, fraction = amount_str.split()
            return float(Fraction(whole)) + float(Fraction(fraction))
        else:
            return float(Fraction(amount_str))
    except ValueError:
        st.error(f"Error parsing amount: {amount_str}")
        return None

# Function to clear session state
def clear_recipe():
    st.session_state['recipe_name'] = "Untitled Recipe"
    st.session_state['recipe_text'] = ""
    st.session_state['original_servings'] = 1
    st.session_state['desired_servings'] = 1
    st.session_state['ingredients'] = []

# Initialize session state
if 'recipe_name' not in st.session_state:
    clear_recipe()

# Available units
units = ['oz', 'ml', 'liters', 'lb', 'grams', 'kg', 'piece', 'cups', 'tbsp', 'tsp']
metric_units = ['ml', 'liters', 'grams', 'kg']
imperial_units = ['oz', 'lb', 'cups', 'tbsp', 'tsp']

# Streamlit app
st.set_page_config(page_title="AI Recipe Tool", layout="wide")

# Navigation bar
st.sidebar.title("Navigation")
option = st.sidebar.radio("Go to", ["Input Recipe", "Edit Recipe", "Scale and Convert Recipe"])

# Save and clear buttons
if st.sidebar.button("Save Recipe", key="save_recipe_sidebar"):
    recipe_data = {
        "name": st.session_state['recipe_name'],
        "original_servings": st.session_state['original_servings'],
        "desired_servings": st.session_state['desired_servings'],
        "ingredients": st.session_state['ingredients']
    }
    # Save JSON
    json_str = json.dumps(recipe_data, indent=4)
    st.download_button(label="Download Recipe as JSON", data=json_str, file_name=f"{st.session_state['recipe_name']}.json", mime="application/json")

    # Save TXT
    txt_str = f"Recipe Name: {st.session_state['recipe_name']}\n"
    txt_str += f"Original Servings: {st.session_state['original_servings']}\n"
    txt_str += f"Desired Servings: {st.session_state['desired_servings']}\n"
    txt_str += "Ingredients:\n"
    for name, amount, unit in st.session_state['ingredients']:
        txt_str += f"  {name}: {amount:.2f} {unit}\n"
    st.download_button(label="Download Recipe as TXT", data=txt_str, file_name=f"{st.session_state['recipe_name']}.txt", mime="text/plain")

    st.sidebar.success("Recipe saved successfully!")

if st.sidebar.button("Clear Recipe", key="clear_recipe_sidebar"):
    clear_recipe()
    st.sidebar.success("Recipe cleared!")

# Input Recipe page
if option == "Input Recipe":
    st.title("Input Your Recipe")

    uploaded_file = st.file_uploader("Upload a saved recipe (JSON or TXT)", type=["json", "txt"], key="upload_file")
    if uploaded_file is not None:
        if uploaded_file.name.endswith(".json"):
            recipe_data = json.load(uploaded_file)
        else:
            recipe_data = {}
            lines = uploaded_file.read().decode("utf-8").split("\n")
            recipe_data["name"] = lines[0].split(": ")[1]
            recipe_data["original_servings"] = int(lines[1].split(": ")[1])
            recipe_data["desired_servings"] = int(lines[2].split(": ")[1])
            recipe_data["ingredients"] = []
            for line in lines[4:]:
                if line:
                    parts = line.split(": ")
                    name = parts[0].strip()
                    amount, unit = parts[1].strip().split()
                    recipe_data["ingredients"].append((name, parse_amount(amount), unit))

        # Update session state with uploaded recipe
        st.session_state['recipe_name'] = recipe_data['name']
        st.session_state['original_servings'] = recipe_data['original_servings']
        st.session_state['desired_servings'] = recipe_data['desired_servings']
        st.session_state['ingredients'] = recipe_data['ingredients']

        st.success("Recipe uploaded successfully!")

    st.text_input("Recipe Name", value=st.session_state['recipe_name'], key='recipe_name')
    st.text_area("Enter your recipe ingredients and amounts (e.g., 'Vodka 1 oz')", value=st.session_state['recipe_text'], height=200, key='recipe_text')
    st.number_input("How many servings does this recipe make?", min_value=1, step=1, value=st.session_state['original_servings'], key='original_servings')
    if st.button("Parse Ingredients", key="parse_ingredients"):
        st.session_state['ingredients'] = []
        for line in st.session_state['recipe_text'].split("\n"):
            if line:
                try:
                    parts = re.split(r'\s+', line)
                    amount = parse_amount(parts[0])
                    unit = parts[1]
                    name = " ".join(parts[2:])
                    st.session_state['ingredients'].append((name, amount, unit))
                except ValueError:
                    st.error(f"Invalid ingredient format: {line}")

# Edit Recipe page
if option == "Edit Recipe":
    st.title("Edit Ingredients")
    for i, (name, amount, unit) in enumerate(st.session_state['ingredients']):
        with st.expander(f"Ingredient {i+1}: {name}"):
            new_name = st.text_input("Name", value=name, key=f'name_{i}')
            new_amount = st.number_input("Amount", value=amount, key=f'amount_{i}')
            new_unit = st.selectbox("Unit", options=units, index=units.index(unit), key=f'unit_{i}')
            st.session_state['ingredients'][i] = (new_name, new_amount, new_unit)

    if st.button("Update Ingredients", key="update_ingredients"):
        st.success("Ingredients updated successfully!")

    if st.button("Clear Ingredients", key="clear_ingredients"):
        st.session_state['ingredients'] = []
        st.success("Ingredients cleared!")

# Scale and Convert Recipe page
if option == "Scale and Convert Recipe":
    st.title("Scale and Convert Recipe")
    st.number_input("How many servings do you want to make?", min_value=1, step=1, value=st.session_state['desired_servings'], key='desired_servings')

    scaled_ingredients = scale_recipe(st.session_state['ingredients'], st.session_state['original_servings'], st.session_state['desired_servings'])
    converted_ingredients = []

    for i, (name, amount, unit) in enumerate(scaled_ingredients):
        with st.expander(f"Ingredient {i+1}: {name}"):
            new_name = st.text_input("Name", value=name, key=f'scale_name_{i}')
            new_amount = st.number_input("Amount", value=amount, key=f'scale_amount_{i}')
            new_unit = st.selectbox("Unit", options=units, index=units.index(unit), key=f'scale_unit_{i}')
            possible_units = [u for u in units if ureg(new_unit).dimensionality == ureg(u).dimensionality]
            desired_unit = st.selectbox(f"Desired unit for {new_name}", options=possible_units, key=f'scale_desired_unit_{i}')
            converted_amount, converted_unit = convert_units(new_amount, new_unit, desired_unit)
            if converted_amount is not None:
                converted_ingredients.append((new_name, converted_amount, converted_unit))

    if st.button("Convert All Units", key="convert_all"):
        st.session_state['ingredients'] = converted_ingredients
        st.success("Units converted successfully!")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("Convert to Metric", key="convert_metric"):
            for i, (name, amount, unit) in enumerate(converted_ingredients):
                if unit not in metric_units:
                    converted_amount, converted_unit = convert_units(amount, unit, 'grams' if 'gram' in ureg(unit).dimensionality else 'ml')
                    if converted_amount is not None:
                        converted_ingredients[i] = (name, converted_amount, converted_unit)
            st.session_state['ingredients'] = converted_ingredients
            st.success("Converted to Metric units successfully!")

    with col2:
        if st.button("Convert to Imperial", key="convert_imperial"):
            for i, (name, amount, unit) in enumerate(converted_ingredients):
                if unit not in imperial_units:
                    converted_amount, converted_unit = convert_units(amount, unit, 'oz' if 'ounce' in ureg(unit).dimensionality else 'cups')
                    if converted_amount is not None:
                        converted_ingredients[i] = (name, converted_amount, converted_unit)
            st.session_state['ingredients'] = converted_ingredients
            st.success("Converted to Imperial units successfully!")

    with col3:
        if st.button("Convert to Weight Only", key="convert_weight"):
            for i, (name, amount, unit) in enumerate(converted_ingredients):
                if 'mass' not in ureg(unit).dimensionality:
                    converted_amount, converted_unit = convert_units(amount, unit, 'grams')
                    if converted_amount is not None:
                        converted_ingredients[i] = (name, converted_amount, converted_unit)
            st.session_state['ingredients'] = converted_ingredients
            st.success("Converted to Weight Only units successfully!")

    st.header("Scaled and Converted Recipe")
    for name, amount, unit in converted_ingredients:
        st.write(f"{name}: {amount:.2f} {unit}")
