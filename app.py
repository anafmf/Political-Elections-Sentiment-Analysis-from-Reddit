import streamlit as st
import pandas as pd
import visualizations
import matplotlib.pyplot as plt
import plotly.express as px
import plotly.graph_objects as go
from wordcloud import WordCloud
from collections import Counter, defaultdict
import random
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image
import io
from datetime import datetime

st.set_page_config(layout="wide") 

container = st.container()
with container:
    st.title("iPolls: A Public Perception of Political Parties")
    st.markdown("This dashboard is part of a project that aims to analyze the public perception of political parties in Portugal using Reddit data.")

# data = pd.read_csv("comments_with_sentiment.csv")
data = visualizations.read_csv_data("comments_with_sentiment.csv")
# data = csv.DictReader("comments_with_sentiment.csv")

col1, col2 = st.columns([3, 2])

with col1:
    st.subheader("Sentiment Analysis")

    chart_choice = st.radio("Select Analysis:", ["Total Counts", "Percentage (%)"], horizontal=True)
    chart_data = visualizations.get_paired_bar_plot_data(data)

    if chart_choice == "Total Counts":

        df = pd.DataFrame({
            'Party': chart_data["labels"],
            'Positive': chart_data["datasets"][0]["data"],
            'Negative': chart_data["datasets"][1]["data"]
        })
        
        # Create the bar chart
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=df['Party'],
            y=df['Positive'],
            name='Positive',
            marker_color="#4CAF50",  # Green
            text=df['Positive'],
            textposition='auto'
        ))
        
        # Add negative bars
        fig.add_trace(go.Bar(
            x=df['Party'],
            y=df['Negative'],
            name='Negative',
            marker_color="#F44336",  # Red
            text=df['Negative'],
            textposition='auto'
        ))

        fig.update_layout(
            title='Positive vs Negative Sentiment',
            barmode='group',  # Side-by-side bars
            legend=dict(orientation="h")
        )

        # Display the chart
        st.plotly_chart(fig, use_container_width=True)
    
    elif chart_choice == "Percentage (%)":
        
        df = pd.DataFrame({
            'Party': chart_data["labels"],
            'Positive': [round(p) for p in chart_data["datasets"][0]["percentage"]],
            'Negative': [round(n) for n in chart_data["datasets"][1]["percentage"]],
        })

        # Create the stacked bar chart
        fig = go.Figure()

        fig.add_trace(go.Bar(
            x=df['Party'],
            y=df['Positive'],
            name='Positive',
            marker_color="#4CAF50",  # Green
            text=[f"{x}%" for x in df['Positive']],
            textposition='auto'
        ))

        fig.add_trace(go.Bar(
            x=df['Party'],
            y=df['Negative'],
            name='Negative',
            marker_color="#F44336",  # Red
            text=[f"{x}%" for x in df['Negative']],
            textposition='auto'
        ))

        fig.update_layout(
            title='Positive vs Negative Sentiment',
            barmode='stack',  # Stacked bars instead of grouped
            legend=dict(orientation="h"),
            xaxis_title='Party',
            yaxis_title='Percentage (%)',
            yaxis=dict(range=[0, 100])  # Optional: limit Y-axis to 100%
        )

        # Display the chart
        st.plotly_chart(fig, use_container_width=True)


    st.subheader("Party Mentions Over Time")

    time_series_data = visualizations.get_time_series_party_mentions_data(data)

    if time_series_data["labels"] and time_series_data["datasets"]:

        debate_info = {
            "2025-04-07": "7th April: AD-CDU (TVI), Chega-PAN (RTP3)",
            "2025-04-08": "8th April: PS-BE (SIC), Chega-Livre (RTP3)",
            "2025-04-09": "9th April: CDU-Livre (SIC Notícias)",
            "2025-04-10": "10th April: PS-IL (RTP1), BE-PAN (CNN Portugal)",
            "2025-04-11": "11th April: AD-Livre (TVI), IL-CDU (SIC Notícias)",
            "2025-04-12": "12th April: PS-PAN (TVI), BE-CDU (RTP3)",
            "2025-04-13": "13th April: AD-PAN (SIC), IL-Livre (CNN Portugal)",
            "2025-04-14": "14th April: AD-IL (RTP1), BE-Livre (SIC Notícias)",
            "2025-04-15": "15th April: PS-Chega (TVI), IL-PAN (SIC Notícias)",
            "2025-04-16": "16th April: AD-BE (RTP1), Chega-CDU (CNN Portugal)",
            "2025-04-17": "17th April: PS-Livre (SIC), Chega-IL (RTP3)",
            "2025-04-21": "21st April: PS-CDU (RTP1), Chega-BE (SIC Notícias)",
            "2025-04-22": "22nd April: Livre-PAN (RTP3)",
            "2025-04-23": "23rdth April: CDU-PAN (CNN Portugal)",
            "2025-04-24": "24th April: AD-Chega (SIC), IL-BE (CNN Portugal)",
            "2025-04-30": "30th April: AD-PS (RTP1, SIC, TVI)",
            "2025-05-04": "04th May: All-party debate (RTP1)",
            "2025-05-06": "06th May: All-party debate (RTP1)",
            "2025-05-08": "08th May: Parties with no parliamentary seat debate (RTP1)"
        }
        
        # Create a placeholder for the chart
        chart_placeholder = st.empty()

        date_objects = [datetime.strptime(label, "%Y-%m-%d") for label in time_series_data["labels"]]
        min_date = min(date_objects)
        max_date = max(date_objects)

        start_date, end_date = st.date_input(
            "Select date range:",
            value=[min_date, max_date],
            min_value=min_date,
            max_value=max_date
        )
        date_mask = [(d.date() >= start_date and d.date() <= end_date) for d in date_objects]
        # Filter the labels (dates) and datasets
        filtered_labels = [label for label, keep in zip(time_series_data["labels"], date_mask) if keep]
        filtered_dates = [d for d, keep in zip(date_objects, date_mask) if keep]
        filtered_datasets = []
        for dataset in time_series_data["datasets"]:
            filtered_data = [val for val, keep in zip(dataset["data"], date_mask) if keep]
            filtered_datasets.append({
                "label": dataset["label"],
                "data": filtered_data,
                "borderColor": dataset["borderColor"]
            })

        # Display filter options below the chart space
        selected_parties = st.multiselect(
            "Filter parties to display:",
            options=[dataset["label"] for dataset in time_series_data["datasets"]],
            default=[dataset["label"] for dataset in time_series_data["datasets"]]
        )
        
        # Create filtered figure based on selection
        filtered_fig = go.Figure()

        # Add a special invisible trace just for the hover text
        # This will be the ONLY trace that shows hover information
        hover_y_values = [0] * len(filtered_labels)
        hover_texts = [
            debate_info.get(date, "") for date, keep in zip(time_series_data["labels"], date_mask) if keep
        ]
        
        # # Populate hover texts for debate dates
        # for i, date in enumerate(time_series_data["labels"]):
        #     if date in debate_info:
        #         hover_texts[i] = debate_info[date]
        
        # Add invisible hover trace
        filtered_fig.add_trace(go.Scatter(
            x=filtered_labels,
            y=hover_y_values,
            mode='lines',
            line=dict(width=0),
            opacity=0,
            hoverinfo="text",
            text=hover_texts,
            hovertemplate="%{text}<extra></extra>",
            showlegend=False,
        ))
        
        # Add all normal data traces but with hoverinfo="none"
        for dataset in filtered_datasets:
            if dataset["label"] in selected_parties:
                filtered_fig.add_trace(go.Scatter(
                    x=filtered_labels,
                    y=dataset["data"],
                    mode='lines+markers',
                    name=dataset["label"],
                    line=dict(color=dataset["borderColor"], width=2),
                    marker=dict(size=6),
                    hoverinfo="none",  # Disable hover for data traces
                ))
        
        # Update layout
        filtered_fig.update_layout(
            title="Party Mentions Trend",
            xaxis_title="Date",
            yaxis_title="Number of Mentions",
            legend_title="Political Party",
            hovermode="x unified",  # Use closest to prevent multiple hovers
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        filtered_fig.update_xaxes(tickformat="%d/%m")

        # Display the chart in the placeholder
        chart_placeholder.plotly_chart(filtered_fig, use_container_width=True)
            
    else:
        st.warning("No time series data available to generate the chart.")

with col2:
    st.subheader("Party Mention Distribution")

    chart_choice = st.radio("Select Analysis:", ["Per Party", "Per Candidate"], horizontal=True)
    
    if chart_choice == "Per Party":

        chart_data = visualizations.get_pie_chart_party_distribution_data(data)
        df = pd.DataFrame({
            'Party': chart_data["labels"],
            'Mentions': chart_data["datasets"][0]["data"]
        })

        color_map = {party: color for party, color in zip(
            chart_data["labels"], 
            chart_data["datasets"][0]["backgroundColor"]
        )}
        
        # Create and display the Plotly pie chart
        fig = px.pie(
            df, 
            values='Mentions', 
            names='Party',
            title='Distribution of Mentions per Party',
            color='Party',
            color_discrete_map=color_map
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(
            legend_title="Political Party",
            showlegend=True,
            legend=dict(
                orientation="v",  # Changed from "h" to "v" for vertical orientation
                yanchor="middle",  # Anchor point for y
                y=0.5,  # Center vertically
                xanchor="right",  # Anchor point for x
                x=1.1  # Position slightly to the right of the plot
            )
        )
        st.plotly_chart(fig, use_container_width=True)
    
    if chart_choice == "Per Candidate":

        chart_data2 = visualizations.get_pie_chart_leader_distribution_data(data)
        df2 = pd.DataFrame({
            'Leader': chart_data2["labels"],
            'Mentions': chart_data2["datasets"][0]["data"]
        })

        color_map = {leader: color for leader, color in zip(
            chart_data2["labels"], 
            chart_data2["datasets"][0]["backgroundColor"]
        )}
        
        # Create and display the Plotly pie chart
        fig = px.pie(
            df2, 
            values='Mentions', 
            names='Leader',
            title='Distribution of Mentions per Candidate',
            color='Leader',
            color_discrete_map=color_map
        )
        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(
            legend_title="Party Leader",
            showlegend=True,
            legend=dict(
                orientation="v",  # Changed from "h" to "v" for vertical orientation
                yanchor="middle",  # Anchor point for y
                y=0.5,  # Center vertically
                xanchor="right",  # Anchor point for x
                x=1.3  # Position slightly to the right of the plot
            )
        )
        st.plotly_chart(fig, use_container_width=True)


    st.subheader("Trendy Topics")

    data = pd.DataFrame(data)
    data['topics'] = data['texto_comentario'].apply(lambda x: visualizations.identify_topics(x))
    all_topics = [topic for topics_list in data['topics'] for topic in topics_list if topic != "Undefined"]
    topic_counts = Counter(all_topics)
    topic_freq = {topic: count for topic, count in topic_counts.items()}

    portuguese_party_colors = [
        "#F886A8",  # PS (Socialist Party) - rose/pink
        "#F8812A",  # PSD (Social Democratic Party) - orange
        "#0094D4",  # CDS-PP (People's Party) - blue
        "#BE0019",  # BE (Left Bloc) - red
        "#8C0013",  # PCP (Portuguese Communist Party) - dark red
        "#00ADEF",  # IL (Liberal Initiative) - cyan/light blue
        "#122B68",  # Chega - dark blue
        "#009A49",  # Livre - green
        "#005C35"   # PAN (People-Animals-Nature) - dark green
    ]

    # Create a colormap from these colors
    portuguese_cmap = LinearSegmentedColormap.from_list("portuguese_parties", portuguese_party_colors, N=256)

    # Function to randomly select colors from the Portuguese party palette
    def portuguese_party_color_func(word, font_size, position, orientation, random_state=None, **kwargs):
        return random.choice(portuguese_party_colors)

    # Check if we have topics to display
    if topic_freq:
        # Generate the word cloud
        wordcloud = WordCloud(
            width=800, 
            height=400, 
            background_color='white', 
            color_func=portuguese_party_color_func,
            max_words=100,
            normalize_plurals=False
        ).generate_from_frequencies(topic_freq)
        
        # Create a matplotlib figure
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        
        # Display in Streamlit
        st.pyplot(fig)
        
    else:
        st.warning("No topics found in the data.")


### Sidebar 
st.sidebar.header("Political Parties")

parties = {
    "PS": {
        "image": "ps.jpg",
        "url": "https://ps.pt/"
    },
    "AD": {
        "image": "ad.jpg",
        "url": "https://ad2025.pt/"
    },
    "IL": {
        "image": "il.jpg",
        "url": "https://iniciativaliberal.pt/"
    },
    "CHEGA": {
        "image": "chega.jpg",
        "url": "https://partidochega.pt/"
    },
    "BE": {
        "image": "be.jpg",
        "url": "https://www.bloco.org/"
    },
    "Livre": {
        "image": "livre.jpg",
        "url": "https://partidolivre.pt/"
    },
    "PAN": {
        "image": "pan.jpg",
        "url": "https://www.pan.com.pt/"
    },
    "PCP": {
        "image": "pcp.jpg",
        "url": "https://www.pcp.pt/"
    },
}

IMAGE_WIDTH = 100
IMAGE_HEIGHT = 100

# Create columns in the sidebar
cols = st.sidebar.columns(2)  # 2 columns for the grid

# Render each party with an image and make it clickable
for i, (name, data) in enumerate(parties.items()):
    col_idx = i % 2  # Alternate between columns
    with cols[col_idx]:
        try:
            # Open and resize the image to consistent dimensions
            img = Image.open(data["image"])
            img = img.resize((IMAGE_WIDTH, IMAGE_HEIGHT), Image.LANCZOS)
            
            # Display the resized image
            st.image(img, use_container_width=False)
            
        except Exception as e:
            # If there's an issue loading the image, just use the original file
            st.image(data["image"], width=IMAGE_WIDTH)
        
        # Create a button with the party name that links to the website
        if st.button(f"Visit {name}", key=f"btn_{name}"):
            # This will open the URL when the button is clicked
            import webbrowser
            webbrowser.open_new_tab(data["url"])
