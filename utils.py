import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from typing import Dict, List, Optional
import re

@st.cache_data
def load_food_database():
    """Load and cache the food database."""
    return pd.read_csv('data/food_database.csv')

@st.cache_data
def load_medical_conditions():
    """Load and cache the medical conditions database."""
    return pd.read_csv('data/medical_conditions.csv')

def word_to_number(word: str) -> Optional[float]:
    """Convert word numbers to numeric values."""
    word_map = {
        'one': 1, 'two': 2, 'three': 3, 'four': 4, 'five': 5,
        'half': 0.5, 'quarter': 0.25, 'third': 0.33
    }
    return word_map.get(word.lower())

def parse_quantity(quantity: str, unit: str, serving_size: str) -> float:
    """Convert quantity and unit to a standard serving size multiplier."""
    try:
        # Convert word numbers to numeric
        if quantity.lower() in ['one', 'two', 'three', 'four', 'five', 'half', 'quarter', 'third']:
            base_quantity = word_to_number(quantity)
        else:
            base_quantity = float(quantity)

        # Handle different unit types
        if 'g' in unit or 'gram' in unit:
            if 'g' in serving_size:
                serving_grams = float(serving_size.split('g')[0].strip())
                return base_quantity / serving_grams
            return base_quantity / 100  # Assume 100g standard serving
        
        if unit in ['cup', 'cups', 'bowl', 'bowls']:
            return base_quantity
        
        if unit in ['piece', 'pieces']:
            if 'piece' in serving_size:
                return base_quantity
            return base_quantity  # Assume 1 piece is one serving

        if unit in ['tbsp', 'tablespoon']:
            return base_quantity * 0.0625  # Approximate cups
        
        if unit in ['tsp', 'teaspoon']:
            return base_quantity * 0.0208  # Approximate cups

        return base_quantity  # Default to treating as servings

    except (ValueError, TypeError):
        return 1.0  # Default to one serving if conversion fails

def normalize_food_name(food_name: str, food_names: List[str]) -> Optional[str]:
    """Find the closest matching food name from the database."""
    food_name = food_name.lower()
    # First try exact match
    for db_food in food_names:
        if food_name == db_food.lower():
            return db_food
    # Then try contains match
    for db_food in food_names:
        if food_name in db_food.lower() or db_food.lower() in food_name:
            return db_food
    return None

def extract_food_items(text: str) -> List[Dict]:
    """Extract food items and quantities from input text."""
    # Convert text to lowercase for better matching
    text = text.lower()
    
    # Initialize food database
    db = load_food_database()
    food_names = db['food_name'].str.lower().tolist()
    
    # Find quantities and food items
    extracted_items = []
    words = text.split()
    i = 0
    while i < len(words):
        # Look for number words
        if words[i].isdigit() or words[i] in ['one', 'two', 'three', 'four', 'five']:
            quantity = words[i]
            if i + 1 < len(words):
                unit = words[i + 1] if words[i + 1] in ['cup', 'cups', 'piece', 'pieces', 'bowl', 'bowls', 'g', 'grams', 'ml', 'milliliters', 'tbsp', 'tablespoon', 'tsp', 'teaspoon'] else ''
                # Look ahead for food items
                for food in food_names:
                    # Look ahead up to 3 words for food items
                    for j in range(i, min(i+4, len(words))):
                        food_phrase = ' '.join(words[j:min(j+3, len(words))]).lower()
                        if food in food_phrase or food_phrase in food:
                            extracted_items.append({
                                "Food": food.title(),
                                "Quantity": f"{quantity} {unit}".strip()
                            })
                            i = j + 2  # Skip the matched food words
                            break
                    else:
                        continue
                    break
        i += 1
    return extracted_items

def safe_float_convert(value) -> float:
    """Safely convert value to float, return 0.0 if conversion fails."""
    try:
        if pd.isna(value):
            return 0.0
        return float(value)
    except (ValueError, TypeError):
        return 0.0

def calculate_nutrition(extracted_items: List[Dict]) -> Dict:
    """Calculate nutrition totals for extracted food items."""
    db = load_food_database()
    totals = {
        "Calories": 0,
        "Protein(g)": 0,
        "Carbohydrates(g)": 0,
        "Fats(g)": 0,
        "Fiber(g)": 0,
        "Iron(mg)": 0,
        "Vitamin C(mg)": 0,
        "Vitamin A(IU)": 0,
        "Vitamin D(mcg)": 0,
        "Calcium(mg)": 0,
        "Potassium(mg)": 0,
        "Sodium(mg)": 0,
        "Zinc(mg)": 0,
        "Vitamin B12(mcg)": 0,
        "Folate(mcg)": 0
    }
    
    nutrient_mapping = {
        "Calories": "calories",
        "Protein(g)": "protein",
        "Carbohydrates(g)": "carbohydrates",
        "Fats(g)": "fats",
        "Fiber(g)": "fiber",
        "Iron(mg)": "iron",
        "Vitamin C(mg)": "vitamin_c",
        "Vitamin A(IU)": "vitamin_a",
        "Vitamin D(mcg)": "vitamin_d",
        "Calcium(mg)": "calcium",
        "Potassium(mg)": "potassium",
        "Sodium(mg)": "sodium",
        "Zinc(mg)": "zinc",
        "Vitamin B12(mcg)": "vitamin_b12",
        "Folate(mcg)": "folate"
    }
    
    for item in extracted_items:
        food_match = db[db['food_name'].str.lower() == item['Food'].lower()]
        if food_match.empty:
            continue
        food_data = food_match.iloc[0]
        quantity_parts = item['Quantity'].split()
        if not quantity_parts:
            continue
            
        quantity = quantity_parts[0]
        unit = quantity_parts[1] if len(quantity_parts) > 1 else ''
        
        # Get the serving size from food data
        serving_size = food_data['serving_size']
        multiplier = parse_quantity(quantity, unit, serving_size)
        
        # Convert all numeric values safely
        for nutrient, db_key in nutrient_mapping.items():
            if db_key in food_data:
                value = safe_float_convert(food_data[db_key])
                totals[nutrient] += value * multiplier
    
    return {k: round(v, 1) for k, v in totals.items()}

def calculate_bmr(weight: float, height: float, age: int, gender: str) -> float:
    """Calculate BMR using Mifflin-St Jeor Equation."""
    if gender == "Male":
        return (10 * weight) + (6.25 * height) - (5 * age) + 5
    return (10 * weight) + (6.25 * height) - (5 * age) - 161

def analyze_nutrition(nutrition_totals: Dict, bmr: float = 2000, age: int = 30, gender: str = "Female", tdee: float = None) -> Dict:
    """Analyze nutrition totals with comprehensive RDA-based analysis."""
    daily_calories = tdee if tdee is not None else bmr * 1.2  # Use TDEE if provided, otherwise assume sedentary
    
    # Age and gender-specific RDA values
    if gender == "Female":
        if age < 50:
            iron_rda = 18
            calcium_rda = 1000
        else:
            iron_rda = 8
            calcium_rda = 1200
    else:
        iron_rda = 8
        calcium_rda = 1000
    
    # Comprehensive RDA-based recommendations (values are for one meal - 30% of daily needs)
    recommended = {
        "Calories": (daily_calories * 0.3, daily_calories * 0.4),
        "Protein(g)": (daily_calories * 0.1 / 4, daily_calories * 0.15 / 4),
        "Carbohydrates(g)": (daily_calories * 0.45 / 4, daily_calories * 0.65 / 4),
        "Fats(g)": (daily_calories * 0.2 / 9, daily_calories * 0.35 / 9),
        "Fiber(g)": (25 * 0.3, 30 * 0.3),
        "Iron(mg)": (iron_rda * 0.3, iron_rda * 0.4),
        "Vitamin C(mg)": (90 * 0.3, 90 * 0.4),
        "Vitamin A(IU)": (3000 * 0.3, 3000 * 0.4),
        "Vitamin D(mcg)": (15 * 0.3, 15 * 0.4),
        "Calcium(mg)": (calcium_rda * 0.3, calcium_rda * 0.4),
        "Potassium(mg)": (3500 * 0.3, 3500 * 0.4),
        "Sodium(mg)": (2300 * 0.3, 2300 * 0.4),  # Upper limit
        "Zinc(mg)": (11 * 0.3, 11 * 0.4),
        "Vitamin B12(mcg)": (2.4 * 0.3, 2.4 * 0.4),
        "Folate(mcg)": (400 * 0.3, 400 * 0.4)
    }
    
    deficient = []
    excess = []
    severity_scores = {}
    
    for nutrient, (min_val, max_val) in recommended.items():
        if nutrient not in nutrition_totals:
            continue
            
        meal_value = nutrition_totals[nutrient]
        target_value = (min_val + max_val) / 2
        
        # Calculate severity score (-1 to 1, where negative means deficient)
        severity = (meal_value - target_value) / target_value if target_value != 0 else (1 if meal_value > 0 else 0)
        nutrient_name = nutrient.split('(')[0]
        severity_scores[nutrient_name] = severity
        
        if meal_value < min_val:
            if severity < -0.5:  # Severe deficiency
                deficient.insert(0, nutrient_name)  # Prioritize severe deficiencies
            else:
                deficient.append(nutrient_name)
        elif meal_value > max_val:
            if severity > 0.5:  # Severe excess
                excess.insert(0, nutrient_name)  # Prioritize severe excess
            else:
                excess.append(nutrient_name)
    
    # Generate feedback
    feedback = ""
    if not deficient and not excess:
        feedback = "Efficiently Taking! Your meal is well balanced."
    else:
        recommendations = {
            "Protein": "lean meats, eggs, or legumes",
            "Fiber": "whole grains or vegetables",
            "Iron": "spinach, lentils, or fortified cereals",
            "Vitamin C": "citrus fruits, bell peppers, or broccoli",
            "Carbohydrates": "whole grains, fruits, or sweet potatoes",
            "Fats": "nuts, avocados, or olive oil",
            "Vitamin A": "carrots, sweet potatoes, or spinach",
            "Vitamin D": "fatty fish, eggs, or fortified dairy",
            "Calcium": "dairy products, tofu, or leafy greens",
            "Potassium": "bananas, potatoes, or yogurt",
            "Zinc": "meat, shellfish, or legumes",
            "Vitamin B12": "meat, fish, or fortified cereals",
            "Folate": "leafy greens, legumes, or fortified grains"
        }
        
        if deficient:
            # Sort deficiencies by severity
            severe_deficiencies = [d for d in deficient if severity_scores.get(d, 0) < -0.5]
            mild_deficiencies = [d for d in deficient if d not in severe_deficiencies]
            
            if severe_deficiencies:
                feedback = f"Critical nutrients needed: {', '.join(severe_deficiencies)}. "
                recommendations_text = [recommendations.get(d, '') for d in severe_deficiencies]
                recommendations_text = [r for r in recommendations_text if r]  # Remove empty recommendations
                if recommendations_text:
                    feedback += f"Strongly recommend adding {', '.join(recommendations_text)}. "
            
            if mild_deficiencies:
                recommendations_text = [recommendations.get(d, '') for d in mild_deficiencies]
                recommendations_text = [r for r in recommendations_text if r]  # Remove empty recommendations
                if recommendations_text:
                    feedback += f"Also consider adding {', '.join(recommendations_text)} for more {', '.join(mild_deficiencies)}."
        
        if excess:
            feedback += f"\nConsider reducing intake of {', '.join(excess)} in future meals."
    
    return {
        "Deficient_Nutrients": deficient,
        "Excess_Nutrients": excess,
        "Feedback": feedback
    }

def create_nutrition_chart(nutrition_totals: Dict):
    """Create a bar chart for nutrition values."""
    nutrients = list(nutrition_totals.keys())
    values = list(nutrition_totals.values())
    
    fig = go.Figure(data=[
        go.Bar(
            x=nutrients,
            y=values,
            marker_color='rgb(26, 118, 255)'
        )
    ])
    
    fig.update_layout(
        title='Nutrition Analysis',
        xaxis_tickangle=-45,
        height=600,
        margin=dict(b=150),  # Increase bottom margin for labels
        yaxis_title='Amount',
        showlegend=False
    )
    
    return fig
