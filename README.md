# Public-Perception-of-Portuguese-Political-Parties

This project provides a dashboard to analyze the public perception of political parties in Portugal using data from Reddit, specifically the /r/portugal subreddit.

## Overview

The application is built with Streamlit and visualizes sentiment and discussion trends related to various Portuguese political parties. It processes Reddit comments to identify mentions of political parties, performs sentiment analysis on these comments, and then presents the findings through interactive charts and a word cloud.

## Features

*   **Sentiment Analysis:** Displays positive vs. negative sentiment for each political party in both total counts and percentages.
*   **Party Mention Distribution:** Shows the distribution of mentions for each political party and for party leaders via pie charts.
*   **Mentions Over Time:** A time series line chart illustrating the trend of mentions for different political parties, with an option to filter by date range and specific parties. It also highlights dates of political debates.
*   **Trendy Topics:** A word cloud visualizing the most frequently discussed topics or keywords from the Reddit comments.
*   **Party Information:** A sidebar provides quick links to the official websites of the major political parties, along with their logos.

## Main Components

*   `app.py`: The main Streamlit application script that creates the dashboard interface and integrates the data visualizations.
*   `data_processing.py`: To be run separately since it is not explicitly used in `app.py`. Fetches data from Reddit, identifies party mentions and creates `comments_without_sentiment.csv`.
*   `sentiment_analysis.py`: To be run separately. Performs sentiment classification (positive, negative) on the processed comments (`comments_without_sentiment.csv`), using GPT 3o-turbo, and creates `comments_with_sentiment.csv`.
*   `visualizations.py`: Reads processed data (`comments_with_sentiment.csv`) and prepare data structures suitable for the Plotly charts and word cloud displayed in the Streamlit app. This script is called in `app.py`.
*   `comments_with_sentiment.csv`: A CSV file containing the Reddit comments along with their identified party and sentiment. This file is read by `app.py` to generate the visualizations.
*   `requirements.txt`: Lists the Python dependencies required to run the project.
*   Image files (`ps.jpg`, `ad.jpg`, etc.): Logos for the political parties displayed in the sidebar.

## How to Run

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/anafmf/Public-Perception-of-Portuguese-Political-Parties.git
    cd Public-Perception-of-Portuguese-Political-Parties
    ```
2.  **Install dependencies:**
    Make sure you have Python installed. Then, install the required libraries using pip:
    ```bash
    pip install -r requirements.txt
    ```
3. **Run following scripts individually:**
    ```
    python data_processing.py
    ```
    ```
    python sentiment_analysis.py
    ```
3.  **Run the Streamlit application:**
    ```bash
    streamlit run app.py
    ```
    This will open the web app in your web browser.

## Dependencies

Key dependencies include:

*   Streamlit
*   Pandas
*   Plotly (for interactive charts)
*   WordCloud
*   Matplotlib
*   Pillow (PIL)

Refer to `requirements.txt` for the full list of dependencies and their versions.
