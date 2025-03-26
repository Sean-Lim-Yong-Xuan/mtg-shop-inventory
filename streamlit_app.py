import streamlit as st
import pandas as pd
import plotly.express as px
import pymongo
import datetime
from pymongo import MongoClient

# MongoDB Connection
#MONGO_URI = "mongodb+srv://Cluster0:123@cluster0.wi9dl.mongodb.net/"
MONGO_URI = "mongodb+srv://Shiranui:1234@theproject.lfcpi.mongodb.net/"
client = MongoClient(MONGO_URI)

#Choosing the database and the collection
db = client["mtgdb"]
collection = db["allmtgcards"]

# Streamlit App
st.title("🃏 MTG Card Inventory")

#df = load_data()
allmtgcards = list(collection.find({}, {"_id": 0}))  # Exclude ObjectId

def display_data_from_mongodb():
    """Displays data from MongoDB in Streamlit."""
    try:
        collection = db.get_collection("allmtgcards")  # Replace with your collection name
        data = list(collection.find())
        if data:
            df = pd.DataFrame(data)
            df = df.drop(columns=['_id'], errors='ignore') #remove mongodb's _id
            st.dataframe(df)
        else:
            st.info("No data found in MongoDB.")
    except Exception as e:
        st.error(f"Error retrieving data from MongoDB: {e}")

#Fetching data...
allmtgcards = list(collection.find({}, {"_id": 0}))

if allmtgcards:
    df = pd.DataFrame(allmtgcards)
    st.info("Successfully connected to MongoDB!!")
    # Search bar
    search_query = st.text_input("Search for a card:", "")
    
    # Filter options
    card_types = df["type"].dropna().unique().tolist()
    colors = df["color_identity"].dropna().unique().tolist()
    power = df["power"].dropna().unique().tolist()
    
    selected_type = st.multiselect("Filter by Type:", card_types)
    selected_colors = st.multiselect("Filter by Color:", colors)
    selected_power = st.multiselect("Filter by Power:", power)
    
    # Apply filters
    filtered_df = df.copy()
    if search_query:
        filtered_df = filtered_df[filtered_df["name"].str.contains(search_query, case=False, na=False)]
        search_data = {
            "query": search_query,
            "timestamp": datetime.datetime.utcnow()
        }
        collection.insert_one(search_data)  # Store search query in MongoDB Atlas
        st.success(f"Search query '{search_query}' stored successfully!")
        # Display past searches
        st.subheader("Recent Searches")
        search_history = list(collection.find({}, {"_id": 0}).sort("timestamp", -1).limit(10))  # Get last 10 searches
        if search_history:
            for search in search_history:
                st.write(f"🔎 {search.get('query', 'N/A')} (Searched on: {search.get("timestamp", 'Unknown')})")

        else:
            st.info("No search history found.")
            
    if selected_type:
        filtered_df = filtered_df[filtered_df["type"].isin(selected_type)]
    if selected_colors:
        filtered_df = filtered_df[filtered_df["color_identity"].isin(selected_colors)]
    if selected_power:
        filtered_df = filtered_df[filtered_df["power"].isin(selected_power)]
    
    st.write(f"### Showing {len(filtered_df)} results")
    st.dataframe(filtered_df)
    
    # Visualization
    chart_option = st.selectbox("Select a chart type:", ["Color Identity Distribution", "Type Distribution", "Power Distribution"])
    
    if chart_option == "Color Identity Distribution":
        st.write ("Data Obtained")
        fig = px.bar(filtered_df["color_identity"].value_counts().reset_index(), x="color_identity", y="count", title="Color Identity Distribution")
    elif chart_option == "Type Distribution":
        fig = px.bar(filtered_df["type"].value_counts().reset_index(), x="type", y="count", title="Type Distribution")
    elif chart_option == "Power Distribution":
        power_counts = filtered_df["power"].value_counts().reset_index()
        power_counts.columns = ["power", "count"]
        fig = px.pie(power_counts, names="power", values="count", title="Power Distribution of Cards")    
    else:
        st.write ("No chart.")

    st.plotly_chart(fig)
