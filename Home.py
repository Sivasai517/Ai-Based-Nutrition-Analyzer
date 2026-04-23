import streamlit as st

st.set_page_config(
    page_title="NutroDet - Nutrition Analysis",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Set up session state for user profile if not exists
if 'age' not in st.session_state:
    st.session_state.age = 30
if 'gender' not in st.session_state:
    st.session_state.gender = 'Female'
if 'weight' not in st.session_state:
    st.session_state.weight = 60
if 'height' not in st.session_state:
    st.session_state.height = 165
if 'activity_level' not in st.session_state:
    st.session_state.activity_level = 'Light'
if 'conditions' not in st.session_state:
    st.session_state.conditions = []
if 'bmr' not in st.session_state:
    st.session_state.bmr = 1500
if 'tdee' not in st.session_state:
    st.session_state.tdee = 1800

# Main page content
st.title('🥗 Welcome to NutroDet')
st.write('Your personal nutrition analysis and recommendation system.')

# Features overview in columns
col1, col2 = st.columns(2)

with col1:
    st.subheader('📱 Main Features')
    st.markdown("""
    - **🍽️ Meal Analysis**: Analyze your meals for nutritional content
    - **👤 Profile Settings**: Customize your health profile
    - **📊 Food Database**: Explore our comprehensive food database
    - **🏥 Health Conditions**: Get condition-specific dietary advice
    """)

    st.subheader('🎯 Getting Started')
    st.markdown("""
    1. Set up your profile in **Profile Settings**
    2. Enter your meal in **Meal Analysis**
    3. Get personalized recommendations!
    """)

with col2:
    st.subheader('🌟 Key Benefits')
    st.markdown("""
    - **Personalized Analysis**: Get nutrition advice based on your profile
    - **Health-Aware**: Recommendations consider your medical conditions
    - **Comprehensive Data**: Access detailed nutritional information
    - **Easy to Use**: Simple interface for quick analysis
    """)

    st.subheader('💡 Tips')
    st.info("""
    - Update your profile regularly for accurate recommendations
    - Be specific when describing your meals
    - Check the Food Database for accurate portion sizes
    - Review Health Conditions for dietary restrictions
    """)

# Quick start section
st.subheader('⚡ Quick Start')
if st.button('Go to Meal Analysis', type='primary'):
    st.switch_page('pages/1_🍽️_Meal_Analysis.py')

# Footer
st.markdown('---')
st.markdown('Made with ❤️ by NutroDet Team')
