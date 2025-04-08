import streamlit as st
import pandas as pd
import plotly.express as px
import pymongo
import datetime
from pymongo import MongoClient

# MongoDB Connection
MONGO_URI = "mongodb+srv://Shiranui:1234@theproject.lfcpi.mongodb.net/"
client = MongoClient(MONGO_URI)

# Choosing the database and the collection
db = client["mtgdb"]
collection = db["allmtgcards"]

# App Title
st.title("🃏 MTG Card Inventory")

# Sidebar Navigation
page = st.sidebar.radio("Go to", ["Card Inventory", "Visualization"])

# Fetching data...
allmtgcards = list(collection.find({}, {"_id": 0}))
if allmtgcards:
    df = pd.DataFrame(allmtgcards)
    st.info("Successfully connected to MongoDB!!")

    if page == "Card Inventory":
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

            st.subheader("🔍 Search Trends (Alphabetically Ordered)")
            pipeline = [
                {"$group": {"_id": "$query", "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}}
            ]
            search_stats = list(collection.aggregate(pipeline))

            if search_stats:
                for entry in search_stats:
                    st.write(f"🔹 **{entry['_id']}** - Searched **{entry['count']}** times")
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

    elif page == "Visualization":
        # Use filtered data from df (if needed, you can persist filters using session state)
        st.subheader("📊 Visualization")
        chart_option = st.selectbox("Select a chart type:", ["Color Identity Distribution", "Type Distribution", "Power Distribution"])

        if chart_option == "Color Identity Distribution":
            fig = px.bar(df["color_identity"].value_counts().reset_index(), x="color_identity", y="count", title="Color Identity Distribution")
        elif chart_option == "Type Distribution":
            fig = px.bar(df["type"].value_counts().reset_index(), x="type", y="count", title="Type Distribution")
        elif chart_option == "Power Distribution":
            power_counts = df["power"].value_counts().reset_index()
            power_counts.columns = ["power", "count"]
            fig = px.pie(power_counts, names="power", values="count", title="Power Distribution of Cards")
        else:
            st.write("No chart selected.")

        st.plotly_chart(fig)
