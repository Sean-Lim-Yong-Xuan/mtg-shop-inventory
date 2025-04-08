import streamlit as st
import pandas as pd
import plotly.express as px
import pymongo
import datetime
from pymongo import MongoClient

# MongoDB Connection
MONGO_URI = "mongodb+srv://Shiranui:1234@theproject.lfcpi.mongodb.net/"
client = MongoClient(MONGO_URI)
db = client["mtgdb"]
collection = db["allmtgcards"]

# App Title
st.title("🃏 MTG Card Inventory")

# Fetch data
allmtgcards = list(collection.find({}, {"_id": 0}))
if not allmtgcards:
    st.warning("No cards found in the database.")
    st.stop()

df = pd.DataFrame(allmtgcards)
st.success("Connected to MongoDB successfully!")

# =====================
# Sidebar — Filter Panel
# =====================
st.sidebar.header("🎛️ Filter Cards")

search_query = st.sidebar.text_input("Search by Name")

card_types = df["type"].dropna().unique().tolist()
colors = df["color_identity"].dropna().unique().tolist()
power = df["power"].dropna().unique().tolist()

selected_type = st.sidebar.multiselect("Type", card_types)
selected_colors = st.sidebar.multiselect("Color", colors)
selected_power = st.sidebar.multiselect("Power", power)

# Apply Filters
filtered_df = df.copy()

if search_query:
    filtered_df = filtered_df[filtered_df["name"].str.contains(search_query, case=False, na=False)]
    search_data = {
        "query": search_query,
        "timestamp": datetime.datetime.utcnow()
    }
    collection.insert_one(search_data)
    st.sidebar.success("Search query stored!")

if selected_type:
    filtered_df = filtered_df[filtered_df["type"].isin(selected_type)]

if selected_colors:
    filtered_df = filtered_df[filtered_df["color_identity"].isin(selected_colors)]

if selected_power:
    filtered_df = filtered_df[filtered_df["power"].isin(selected_power)]

# ========================
# Main Page — Visualization
# ========================
st.subheader(f"📋 Showing {len(filtered_df)} Result(s)")

# Display table
st.dataframe(filtered_df)

# Visualization
st.subheader("📊 Visualization")

chart_option = st.selectbox("Choose a Chart Type", ["Color Identity Distribution", "Type Distribution", "Power Distribution"])

if chart_option == "Color Identity Distribution":
    fig = px.bar(filtered_df["color_identity"].value_counts().reset_index(), 
                 x="color_identity", y="count", title="Color Identity Distribution")
elif chart_option == "Type Distribution":
    fig = px.bar(filtered_df["type"].value_counts().reset_index(), 
                 x="type", y="count", title="Type Distribution")
elif chart_option == "Power Distribution":
    power_counts = filtered_df["power"].value_counts().reset_index()
    power_counts.columns = ["power", "count"]
    fig = px.pie(power_counts, names="power", values="count", title="Power Distribution")
else:
    fig = None

if fig:
    st.plotly_chart(fig)
