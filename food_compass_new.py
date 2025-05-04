import streamlit as st
import requests
import json
import pandas as pd
from pandasql import sqldf

from openai import OpenAI
import os

#from dotenv import load_dotenv
#load_dotenv()  # This loads the .env file into the environment
#api_key = os.getenv("OPENAI_API_KEY")
import streamlit as st
api_key = st.secrets["OPENAI_API_KEY"]
client = OpenAI(api_key=api_key)

def analyze_nutrition_with_gpt(nutriments):
    prompt = f"""
    Analyze the following nutrition information (per 100g):
    Calories: {nutriments.get("energy-kcal_100g", "N/A")},
    Fats: {nutriments.get("fat_100g", "N/A")}g,
    Sugars: {nutriments.get("sugars_100g", "N/A")}g,
    Salt: {nutriments.get("salt_100g", "N/A")}g,
    Proteins: {nutriments.get("proteins_100g", "N/A")}g.

    Please evaluate the overall healthiness of this product and mention any specific concerns or benefits a health-conscious person should know.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ GPT Analysis failed: {e}"


# Load recall_data.json
with open("food_recall_clean.json", "r") as f:
    recall_data = json.load(f)

# Convert json to DataFrame
recall_df = pd.DataFrame(recall_data)

# Preprocess- delete all "dict"
for col in recall_df.columns:
    recall_df[col] = recall_df[col].apply(lambda x: str(x) if isinstance(x, dict) else x)

# Use SQL to look up recall count
def lookup_recall_count(firm_name):
    safe_name = firm_name.replace("'", "''")
    query = f"""
    SELECT COUNT(*) as recall_count
    FROM df
    WHERE LOWER(recalling_firm) LIKE '%{safe_name.lower()}%'
    """
    result = sqldf(query, {"df": recall_df})
    return result.iloc[0]["recall_count"]




# Streamlit
st.set_page_config("🍽 Food Compass -- Take a wisely bite :)", layout="wide")
st.title("🍽 Food Compass -- Take a wisely bite :)")
st.subheader("Analyze Food Nutrition and Dietary Preferences")
st.markdown("""
Welcome to *Food Compass*!  
This app helps you *analyze nutrition facts* of food products  
and check if they align with your *dietary needs*.
""")
st.divider()

# Sidebar
st.sidebar.header("Get Started")
barcode = st.sidebar.text_input("Product Barcode", "")

fields = st.sidebar.multiselect(
    "Fields to retrieve",
    [
        "product_name",
        "nutrition_grades",
        "ingredients_text",
        "allergens_tags",
        "labels_tags",
        "misc_tags"
    ],
    default=["product_name", "nutrition_grades"]
)

# Dietary Preferences
dietary_preferences = st.sidebar.multiselect(
    "Dietary Preference (Optional)",
    ["Low Carb", "Low Fat", "Low Sugar", "Low Salt"]
)

# Custom Nutrition Thresholds
st.sidebar.markdown("*Custom Nutrition Thresholds (per 100g)*")
max_calories = st.sidebar.number_input("Max Calories (kcal)", value=500)
max_fats = st.sidebar.number_input("Max Fats (g)", value=50.0)
max_sugars = st.sidebar.number_input("Max Sugars (g)", value=20.0)
max_salt = st.sidebar.number_input("Max Salt (g)", value=2.0)

operation = st.sidebar.radio("Operation", ["Fetch Product", "Search by Category", "Submit Missing Data"])

# Additional inputs
if operation == "Search by Category":
    st.sidebar.info("Please enter category in English, e.g. 'Orange Juice', 'Chocolate'.")
    category = st.sidebar.text_input("Category (e.g. Bread)", "")
    grade = st.sidebar.selectbox("Nutrition Grade (optional)", ["", "a", "b", "c", "d", "e"])
elif operation == "Submit Missing Data":
    uid = st.sidebar.text_input("User ID", "")
    pwd = st.sidebar.text_input("Password", type="password")


# Check Nutrition Warnings
def check_nutrition_warnings(nutriments, dietary_preferences, thresholds):
    warnings = []
    matches_preference = True

    cal = nutriments.get("energy-kcal_100g", None)
    fat = nutriments.get("fat_100g", None)
    sugars = nutriments.get("sugars_100g", None)
    salt = nutriments.get("salt_100g", None)

    # Dietary specific checks
    if "Low Carb" in dietary_preferences and sugars is not None and sugars > 10:
        warnings.append("⚠ High Carbs for Low Carb Diet")
        matches_preference = False
    if "Low Fat" in dietary_preferences and fat is not None and fat > 10:
        warnings.append("⚠ High Fat for Low Fat Diet")
        matches_preference = False
    if "Low Sugar" in dietary_preferences and sugars is not None and sugars > 5:
        warnings.append("⚠ High Sugars for Low Sugar Diet")
        matches_preference = False
    if "Low Salt" in dietary_preferences and salt is not None and salt > 0.5:
        warnings.append("⚠ High Salt for Low Salt Diet")
        matches_preference = False

    # General thresholds checks
    if cal is not None and cal > thresholds["Calories"]:
        warnings.append(f"⚠ High Calories (> {thresholds['Calories']} kcal)")
        matches_preference = False
    if fat is not None and fat > thresholds["Fats"]:
        warnings.append(f"⚠ High Fats (> {thresholds['Fats']} g)")
        matches_preference = False
    if sugars is not None and sugars > thresholds["Sugars"]:
        warnings.append(f"⚠ High Sugars (> {thresholds['Sugars']} g)")
        matches_preference = False
    if salt is not None and salt > thresholds["Salt"]:
        warnings.append(f"⚠ High Salt (> {thresholds['Salt']} g)")
        matches_preference = False

    return warnings, matches_preference


# Helper function to display a product card
def display_product_card(p, dietary_preferences, thresholds):
    product_name = p.get("product_name", "Unknown")
    code = p.get("code", "Unknown")
    brand = p.get("brands", "Unknown")
    quantity = p.get("quantity", "Unknown")
    nutrition_grade = p.get("nutrition_grades", "Unknown")
    categories = p.get("categories_tags", [])
    ecoscore = p.get("ecoscore_grade", "Unknown")
    image_url = p.get("image_small_url", "")
    ingredients = p.get("ingredients_text", "Not available")
    allergens = p.get("allergens_tags", [])
    labels = p.get("labels_tags", [])
    countries = p.get("countries_tags", [])
    nutriments = p.get("nutriments", {})
    nutriscore_data = p.get("nutriscore_data", {})

    with st.container():
        cols = st.columns([1, 3])
        with cols[0]:
            if image_url:
                st.image(image_url, width=100)
            else:
                st.image("https://upload.wikimedia.org/wikipedia/commons/6/65/No-Image-Placeholder.svg", width=100)
        with cols[1]:
            st.markdown(f"### 🥫 {product_name}")

            # Display Warnings
            warnings, matches_preference = check_nutrition_warnings(nutriments, dietary_preferences, thresholds)
            if matches_preference:
                st.success("✅ Matches Dietary Preferences!")
            else:
                st.error("❌ Does NOT Match Dietary Preferences!")
                for w in warnings:
                    st.error(w)

            # Recall Risk Alert
            recall_count = lookup_recall_count(brand)
            if recall_count > 1:
                st.error(f"⚠ High Recall Risk! ({recall_count} brand recalls found federally)")

            if brand and brand != "Unknown":
                brand_link = f"https://world.openfoodfacts.org/brand/{brand.replace(' ', '-')}"
                st.markdown(f"*Brand:* [{brand}]({brand_link})", unsafe_allow_html=True)
            else:
                st.write(f"*Brand:* {brand}")

            st.write(f"*Quantity:* {quantity}")
            st.write(f"*Barcode:* {code}")

            if nutrition_grade and nutrition_grade != "Unknown":
                grade_display = {
                    'a': '🟢 A 🥦', 'b': '🟡 B 🍊', 'c': '🟠 C 🍞', 'd': '🟠 D 🍟', 'e': '🔴 E 🍩'
                }.get(nutrition_grade.lower(), nutrition_grade.upper())
                st.write(f"*Nutrition Grade:* {grade_display}")

                score = nutriscore_data.get("score", None)
                if score is not None:
                    st.write(f"*Nutrition Score:* {score:+d}")

            if ecoscore and ecoscore != "Unknown":
                ecoscore_display = {
                    'a': '🟢 A 🌿', 'b': '🟡 B 🍂', 'c': '🟠 C 🍁', 'd': '🟠 D 🪵', 'e': '🔴 E 🔥'
                }.get(ecoscore.lower(), ecoscore.upper())
                st.write(f"*Eco-Score:* {ecoscore_display}")

            if nutriments:
                st.markdown("** Nutrition Facts (per 100g):")
                cal = nutriments.get("energy-kcal_100g", None)
                fat = nutriments.get("fat_100g", None)
                sugars = nutriments.get("sugars_100g", None)
                salt = nutriments.get("salt_100g", None)
                proteins = nutriments.get("proteins_100g", None)
                sodium = nutriments.get("sodium_100g", None)
                potassium = nutriments.get("potassium_100g", None)
                calcium = nutriments.get("calcium_100g", None)

                if cal is not None:
                    st.write(f"*Calories:* {cal:.0f} kcal")
                if fat is not None:
                    st.write(f"*Fats:* {fat:.1f} g")
                if sugars is not None:
                    st.write(f"*Sugars:* {sugars:.1f} g")
                if salt is not None:
                    st.write(f"*Salt:* {salt:.1f} g")
                if proteins is not None:
                    st.write(f"*Proteins:* {proteins:.1f} g")
                if sodium is not None:
                    st.write(f"*Sodium:* {sodium:.3f} g")
                if potassium is not None:
                    st.write(f"*Potassium:* {potassium:.0f} mg")
                if calcium is not None:
                    st.write(f"*Calcium:* {calcium:.0f} mg")

            st.markdown("🧠 **GPT-Based Nutrition Analysis:**")
            gpt_analysis = analyze_nutrition_with_gpt(nutriments)
            st.info(gpt_analysis)

            st.markdown("🌿 Ingredients:")
            st.write(ingredients if ingredients else "Not available")

            if allergens:
                st.markdown("⚠ Allergens:")
                for a in allergens:
                    st.markdown(f"{a.replace('en:', '').replace('-', ' ').title()} ", unsafe_allow_html=True)

            if labels:
                st.markdown("🔖 Labels:")
                for l in labels:
                    st.markdown(f"{l.replace('en:', '').replace('-', ' ').title()} ", unsafe_allow_html=True)

            if countries:
                st.markdown("🌍 Countries Available:")
                for c in countries:
                    st.markdown(f"{c.replace('en:', '').replace('-', ' ').title()} ", unsafe_allow_html=True)

            if categories:
                st.markdown("🏷 Categories:")
                for cat in categories:
                    st.markdown(f"{cat.replace('en:', '').replace('-', ' ').title()} ", unsafe_allow_html=True)

        st.markdown("---")


# --- Main Action ---
tab1, tab2, tab3 = st.tabs([
    "Nutrition Checker",
    "🗺️ Food Recall Map",
    "U.S. Eating Habits"
])

with tab1:
  st.info("Use the sidebar to configure your query before searching.")
  if st.sidebar.button("Go"):
      with st.spinner('Loading, please wait... 🌀'):
          requested_fields = fields + [
              "brands", "quantity", "categories_tags", "ecoscore_grade",
              "image_small_url", "countries_tags", "code", "nutriments", "nutriscore_data"
          ]

          thresholds = {
              "Calories": max_calories,
              "Fats": max_fats,
              "Sugars": max_sugars,
              "Salt": max_salt
          }

          if operation == "Fetch Product":
              if not barcode.strip():
                  st.error("Please enter a barcode.")
              else:
                  params = {"fields": ",".join(set(requested_fields))}
                  url = f"https://world.openfoodfacts.org/api/v2/product/{barcode.strip()}"
                  res = requests.get(url, params=params)
                  if res.ok and res.json().get("status") == 1:
                      st.success("✅ Product found!")
                      p = res.json()["product"]
                      display_product_card(p, dietary_preferences, thresholds)
                  else:
                      st.error("❌ Product not found or error.")

          elif operation == "Search by Category":
              if not category.strip():
                  st.error("Please enter a category.")
              else:
                  category_tag = category.lower().replace(" ", "-").strip()
                  params = {
                      "categories_tags_en": category_tag,
                      "fields": ",".join(set(requested_fields))
                  }
                  if grade:
                      params["nutrition_grades_tags"] = grade

                  url = "https://world.openfoodfacts.org/api/v2/search"
                  res = requests.get(url, params=params)
                  if res.ok:
                      obj = res.json()
                      products = obj.get("products", [])
                      st.success(f"✅ Found {obj['count']} products")

                      if not products:
                          st.warning("⚠ No products found. Check spelling or try a different category.")
                      else:
                          page_size = 20
                          page_number = st.number_input("Page Number", min_value=1,
                                                        max_value=max(1, (len(products) - 1) // page_size + 1), step=1)
                          start_idx = (page_number - 1) * page_size
                          end_idx = start_idx + page_size

                          for p in products[start_idx:end_idx]:
                              display_product_card(p, dietary_preferences, thresholds)

                  else:
                      st.error("❌ Search failed.")

import pandas as pd
import plotly.express as px

# Fetch Food Recall Data
@st.cache_data(ttl=3600)
def get_recall_data():
    url = "https://api.fda.gov/food/enforcement.json"
    params = {
        "search": "status:Ongoing",
        "limit": 1000
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        return response.json().get("results", [])
    return []

def process_data(data):
    df = pd.DataFrame(data)
    state_counts = df['state'].value_counts().reset_index()
    state_counts.columns = ['state', 'count']
    return df, state_counts

def draw_map(state_counts):
    fig = px.choropleth(
        state_counts,
        locations='state',
        locationmode="USA-states",
        color='count',
        scope="usa",
        color_continuous_scale="Reds",
        labels={'count': 'Recall Count'},
        title="Food Recalls by State (Ongoing)"
    )
    return fig

# Inside tab2
with tab2:
    st.header("🗺️ Food Recall Map")
    selected_year = st.selectbox(
        "Filter by Recall Year",
        options=["All", "2025", "2024", "2023", "2022", "2021"],
        index=0  # default is all
    )

    data = get_recall_data()
    df_raw, state_counts = process_data(data)
    if selected_year != "All":
        df_raw = df_raw[df_raw['recall_initiation_date'].str.startswith(selected_year)]
        state_counts = df_raw['state'].value_counts().reset_index()
        state_counts.columns = ['state', 'count']

    fig = draw_map(state_counts)
    st.plotly_chart(fig, use_container_width=True)

    selected_state = st.selectbox("Select a state to view recall details", state_counts['state'])

    st.subheader(f"📋 Recent Food Recalls in {selected_state}")
    state_filtered = df_raw[df_raw['state'] == selected_state.upper()].head(10)

    for _, row in state_filtered.iterrows():
        st.markdown(f"""
        **{row.get('product_description', 'No Description')}**  
        - 🏢 **Firm:** {row.get('recalling_firm', 'N/A')}  
        - ⚠️ **Reason:** {row.get('reason_for_recall', 'N/A')}  
        - 🗓️ **Date:** {row.get('recall_initiation_date', 'N/A')}
        """)
        st.markdown("---")

# Tab 3
with tab3:
    st.header("U.S. Eating Habits Overview")

    import pandas as pd
    import matplotlib.pyplot as plt

    try:
        df = pd.read_csv("nhanes_small.csv")
    except FileNotFoundError:
        st.error("❌ File 'nhanes_small.csv' not found.")
        st.stop()

    df["DR1ISODI"] = pd.to_numeric(df["DR1ISODI"], errors="coerce")  # sodium (mg)
    df["DR1ITFAT"] = pd.to_numeric(df["DR1ITFAT"], errors="coerce")  # fat (g)

    meal_map = {
        1: "Breakfast", 2: "Lunch", 3: "Dinner", 4: "Supper", 5: "Brunch",
        6: "Snack", 7: "Drink", 8: "Infant Feeding", 9: "Extended Consumption"
    }
    df["Meal Type"] = df["DR1_030Z"].map(meal_map)

    
    df_filtered = df.dropna(subset=["Meal Type", "DR1ISODI", "DR1ITFAT"])

    # 
    agg = df_filtered.groupby("Meal Type")[["DR1ISODI", "DR1ITFAT"]].mean().reset_index()
    agg = agg.rename(columns={"DR1ISODI": "Sodium (mg)", "DR1ITFAT": "Fat (g)"})

    # 
    nutrient = st.selectbox("Select Nutrient to Display", ["Sodium (mg)", "Fat (g)"], key="meal_plot_nutrient")

    # 
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(agg["Meal Type"], agg[nutrient], color="#4c72b0")
    ax.set_title(f"Average {nutrient} by Meal Type (NHANES)", fontsize=14)
    ax.set_xlabel("Meal Type")
    ax.set_ylabel(nutrient)
    ax.grid(axis='y', linestyle='--', alpha=0.5)
    plt.xticks(rotation=30)
    plt.tight_layout()

    # 
    st.pyplot(fig)

    with st.expander("About this data"):
        st.markdown("""
        This chart reflects **average nutrient intake per eating occasion** as reported
        in **NHANES 2021-2023** (`DR1IFF_L.csv`).

        1: "Breakfast"
        2: "Lunch"
        3: "Dinner"
        4: "Supper"
        5: "Brunch"
        6: "Snack"
        7: "Drink"
        8: "Infant Feeding"
        9: "Extended Consumption"

        Meals are grouped by type (breakfast, lunch, dinner, snack), and show
        the **average sodium (mg)** or **fat (g)** consumed per occasion.
        """)

st.divider()
st.markdown("""
### About Food Compass

*App Purpose:*  
> Food Compass helps you analyze nutrition facts of food products and aligns them with your dietary needs.
> Food Compass is connected to Open Food Facts API service, for all terms, please check "https://world.openfoodfacts.org/api/v2/search"

*Main Features:*  
- Barcode and Category Search  
- Nutrition Facts Detection  
- ⚠ Dietary Warnings  
- Summary Reports

---

> "Eat Smarter. Live Healthier." 🍎
""")
