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

# Sidebar Style Menu
st.sidebar.markdown("### 🗃️ DATABASE")
page = st.sidebar.radio(" ", ["📇 Card Inventory", "📊 Visualization"], label_visibility="collapsed")

st.sidebar.markdown("### 🧰 SERVICES")
st.sidebar.markdown("- 🔍 Atlas Search\n- 🔄 Stream Processing\n- 🎯 Triggers\n- 🚚 Migration\n- 🌐 Data Federation")

# Page Title
st.title("🃏 MTG Card Inventory")

# Load data
allmtgcards = list(collection.find({}, {"_id": 0}))
if allmtgcards:
    df = pd.DataFrame(allmtgcards)
    st.info("Successfully connected to MongoDB!!")

    if page == "📇 Card Inventory":
        # Filters and Search
        search_query = st.text_input("Search for a card:", "")
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
            search_data = {"query": search_query, "timestamp": datetime.datetime.utcnow()}
            collection.insert_one(search_data)
            st.success(f"Search query '{search_query}' stored successfully!")

            st.subheader("🔍 Search Trends")
            pipeline = [
                {"$group": {"_id": "$query", "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}}
            ]
            search_stats = list(collection.aggregate(pipeline))
            for entry in search_stats:
                st.write(f"🔹 **{entry['_id']}** - Searched **{entry['count']}** times")

        if selected_type:
            filtered_df = filtered_df[filtered_df["type"].isin(selected_type)]
        if selected_colors:
            filtered_df = filtered_df[filtered_df["color_identity"].isin(selected_colors)]
        if selected_power:
            filtered_df = filtered_df[filtered_df["power"].isin(selected_power)]

        st.write(f"### Showing {len(filtered_df)} results")
        st.dataframe(filtered_df)

    elif page == "📊 Visualization":
        st.subheader("📊 MTG Card Data Visualization")
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
