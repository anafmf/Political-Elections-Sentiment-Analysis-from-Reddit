"""
Sentiment analysis script for Reddit comments using an LLM API.

This script performs the following tasks:
1.  Loads processed comments from a CSV file (expected output from data_processing.py).
2.  Connects to an LLM API (e.g., OpenAI GPT-3.5-turbo) for sentiment evaluation.
3.  Iterates through comments, sending them to the LLM for sentiment classification (positive/negative).
4.  Adds the sentiment to the DataFrame.
5.  Saves the DataFrame with sentiment information to a new CSV file.

IMPORTANT: Replace placeholder LLM API key before running.
"""

import os
import csv
import pandas as pd
import time
from openai import OpenAI # Assuming OpenAI, as per the notebook

# --- Configuration & Constants ---

# IMPORTANT: Replace with your actual OpenAI API key
OPENAI_API_KEY = "[REDACTED]"

INPUT_CSV_PATH = "processed_comments_before_sentiment.csv" # From data_processing.py
OUTPUT_CSV_PATH = "comments_with_sentiment.csv"
SENTIMENT_MODEL = "gpt-3.5-turbo"
SENTIMENT_PROMPT_TEMPLATE = (
    "Classify the sentiment in this political comment as either 'positive' or 'negative'. "
    "Only reply with one of those two words.\n\n{}\n")

DELAY_BETWEEN_REQUESTS = 1  # seconds between API calls


# --- Helper Functions ---
def get_sentiment_from_llm(comment_text):
    """Gets sentiment for a given text using OpenAI API."""
    if OPENAI_API_KEY == "your_openai_api_key_placeholder":
        print("Warning: OPENAI_API_KEY is not set or is a placeholder. Returning dummy sentiment.")
        # Return a dummy sentiment for testing without a real API key
        dummy_sentiments = ["positive", "negative", "neutral"]
        return dummy_sentiments[hash(comment_text) % len(dummy_sentiments)]

    try:
        client = OpenAI(api_key=OPENAI_API_KEY)
        prompt = SENTIMENT_PROMPT_TEMPLATE.format(comment_text[:2000]) # Truncate long comments
        
        response = client.chat.completions.create(
            model=SENTIMENT_MODEL,
            messages=[
                {"role": "system", "content": "You are a sentiment classifier for Portuguese political comments. Only reply with 'positive' or 'negative'."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2, # Low temperature for more deterministic output
                max_tokens=10    # Expecting a single word response
    )
        
        sentiment = response.choices[0].message.content.strip().lower()
        if sentiment not in ["positive", "negative", "neutral"]:
            print(f"Warning: Unexpected sentiment {sentiment} from LLM. Defaulting to neutral.")
            return "neutral"
        return sentiment
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return "error_api" # Indicate an API error

def process_comments_for_sentiment(input_file, output_file):
    """Reads comments, gets sentiment, and writes to a new CSV."""
    comments_with_sentiment = []
    fieldnames_input = []
    
    if not os.path.exists(input_file):
        print(f"Error: Input file {input_file} not found. Cannot perform sentiment analysis.")
        # Create an empty output file with headers if input is missing
        with open(output_file, mode="w", newline='', encoding="utf-8") as csv_out:
            fieldnames_output = ["id_comentario", "texto_comentario", "data_comentario", "score", "url_comentario", "party", "sentiment"]
            writer_out = csv.DictWriter(csv_out, fieldnames=fieldnames_output)
            writer_out.writeheader()
        return

    try:
        with open(input_file, mode="r", newline='', encoding="utf-8") as csv_in:
            reader = csv.DictReader(csv_in)
            fieldnames_input = reader.fieldnames if reader.fieldnames else []
            if not fieldnames_input:
                print(f"Error: Input CSV {input_file} is empty or has no header.")
                return

            print(f"Processing comments from {input_file} for sentiment analysis...")
            count = 0
            for row in reader:
                count += 1
                comment_text = row.get("texto_comentario", "")
                if not comment_text.strip():
                    sentiment = "neutral" # Or skip, or mark as error
                else:
                    print(f"Analyzing comment {count}: {comment_text[:50]}...")
                    sentiment = get_sentiment_from_llm(comment_text)
                    time.sleep(DELAY_BETWEEN_REQUESTS) # Respect API rate limits
                
                # Prepare the output row, keeping all original columns
                output_row = {key: row.get(key, "") for key in fieldnames_input}
                output_row["sentiment"] = sentiment
                comments_with_sentiment.append(output_row)
                
                if count % 10 == 0:
                    print(f"Processed {count} comments so far...")

    except IOError as e:
        print(f"Error reading input CSV file {input_file}: {e}")
        return
    except Exception as e:
        print(f"An unexpected error occurred during processing: {e}")
        return

    # Define output fieldnames: input fieldnames + new sentiment column
    fieldnames_output = fieldnames_input + ["sentiment"] if "sentiment" not in fieldnames_input else fieldnames_input
    # Ensure all expected base fields are there, even if input was minimal
    expected_base_fields = ["id_comentario", "texto_comentario", "data_comentario", "score", "url_comentario", "party"]
    for f in expected_base_fields:
        if f not in fieldnames_output:
            fieldnames_output.append(f)
    if "sentiment" not in fieldnames_output: # Should be there now
         fieldnames_output.append("sentiment")
    # Remove duplicates while preserving order for Python < 3.7 compatibility if needed, though 3.11 is used
    seen = set()
    fieldnames_output = [x for x in fieldnames_output if not (x in seen or seen.add(x))]

    # Save comments with sentiment to the output CSV
    try:
        with open(output_file, mode="w", newline='', encoding="utf-8") as csv_out:
            writer_out = csv.DictWriter(csv_out, fieldnames=fieldnames_output, extrasaction="ignore"
            ) # ignore extra fields if any
            writer_out.writeheader()
            writer_out.writerows(comments_with_sentiment)
        print(f"Successfully saved {len(comments_with_sentiment)} comments with sentiment to {output_file}")
    except IOError as e:
        print(f"Error writing output CSV file {output_file}: {e}")

# --- Main Execution ---
if __name__ == "__main__":
    print("Starting sentiment analysis script (Standard Python version)...")
    if OPENAI_API_KEY == "your_openai_api_key_placeholder":
        print("--- USING DUMMY SENTIMENT ANALYSIS AS OPENAI_API_KEY IS NOT SET ---")
    
    process_comments_for_sentiment(INPUT_CSV_PATH, OUTPUT_CSV_PATH)
    print("Sentiment analysis script finished.")

