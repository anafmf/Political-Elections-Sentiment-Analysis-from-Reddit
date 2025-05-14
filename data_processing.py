"""
Data processing script for Reddit comments related to Portuguese elections.

This script performs the following tasks:
1.  Connects to the Reddit API (credentials need to be provided).
2.  Fetches posts from a specified subreddit with a given flair.
3.  Fetches all comments from those posts.
4.  Cleans the comments DataFrame by keeping relevant columns.
5.  Identifies the political party mentioned in each comment based on keywords.
6.  Calculates the count of comments per identified party.

Note: The user's original request mentioned 'trendy_topics', 'identity_topics fx', 
and 'topic_counts'. These functionalities were not found in the provided Jupyter notebook 
and are therefore not implemented in this script.

IMPORTANT: Replace placeholder Reddit API credentials before running.
"""

import praw
import pandas as pd
from datetime import datetime
import re
from collections import defaultdict
import unicodedata
import time # For potential rate limiting, though not strictly used in PRAW fetch here

# --- Configuration & Constants ---

# IMPORTANT: Replace with your actual Reddit API credentials
REDDIT_CLIENT_ID = "[REDACTED]" 
REDDIT_CLIENT_SECRET = "[REDACTED]"
REDDIT_USER_AGENT = "[REDACTED]"

SUBREDDIT_NAME = "portugal"
FLAIR_TEXT = "Legislativas 2025"

PARTY_KEYWORDS = {
    "PS": [
        "ps", "partido socialista", "pedro nuno santos", "pedro nuno", "pns",
        "socialistas", "#ps", "governo socialista", "bancada socialista",
        "secretário-geral do ps", "secretario-geral do ps", "líder do ps", "lider do ps",
        "ex-ministro das infraestruturas", "geringonça", "costa", "antónio costa", "antonio costa"
    ],
    "AD": [
        "psd", "partido social democrata", "luís montenegro", "luis montenegro",
        "montenegro", "social-democratas", "aliança democrática",
        "ad", "#psd", "#ad", "psd/cds", "coligação psd/cds", "coligacao psd/cds",
        "coligação ad", "coligacao ad", "laranja", "laranjas", "primeiro-ministro",
        "cds", "cds-pp", "partido popular", "paulo núncio", "paulo nuncio",
        "sebastião bugalho", "sebastiao bugalho"
    ],
    "IL": [
        "il", "iniciativa liberal", "rui rocha", "liberais", "liberalismo", "#il",
        "bancada liberal", "deputados liberais", "carvalho da silva", "cotrim figueiredo",
        "joão cotrim", "joao cotrim", "cotrim"
    ],
    "CHEGA": [
        "chega", "andré ventura", "andre ventura", "ventura",
        "extrema direita", "#chega", "rita matias", "rita", "partido de extrema-direita",
        "partido de extrema direita", "ultraconservadores", "partido ultraconservador",
        "direita radical", "populista", "populismo", "terceira força política"
    ],
    "BE": [
        "be", "bloco de esquerda", "mariana mortágua", "mariana mortagua",
        "mortágua", "mortagua", "#be", "bloquistas", "bancada bloquista",
        "catarina martins", "louçã", "louca", "fernando rosas"
    ],
    "PCP": [
        "pcp", "partido comunista", "comunistas", "paulo raimundo", "raimundo", "cgtp", "#pcp",
        "cdu", "coligação democrática unitária", "coligacao democratica unitaria",
        "partido comunista português", "partido comunista portugues", "bancada comunista",
        "jerónimo de sousa", "jeronimo de sousa", "os verdes", "pev"
    ],
    "PAN": [
        "pan", "pessoas animais natureza", "ines sousa real", "inês sousa real", "isr", "#pan",
        "pessoas-animais-natureza", "ambientalistas", "causa animal", "partido ambientalista",
        "andré silva", "andre silva"
    ],
    "Livre": [
        "livre", "rui tavares", "tavares", "#livre", "partido livre",
        "bancada do livre", "joacine katar moreira", "jorge pinto", "partido ecologista",
        "esquerda verde", "eco-socialista", "ecosocialista"
    ],
    "Other parties": sorted(list(set([
        "partidos sem assento", "sem assento parlamentar", "sem representação", "partidos independentes",
        "movimento", "partido político", "sem bancada", "sem deputados", "partidos marginais", "sem voz no parlamento",
        "alternativa 21", "nuno afonso", "alternativa 21 partido", "adn", "alternativa democrática nacional",
        "ergue-te", "josé pinto coelho", "juntos pelo povo", "filipe sousa", "jpp", "juntos pelo povo partido",
        "nós, cidadãos!", "joaquim rocha afonso", "nós cidadãos", "nova direita", "ossanda liber", "pctp/mrpp", "mrpp",
        "partido comunista dos trabalhadores portugueses", "ptp", "josé manuel coelho", "partido trabalhista português",
        "rir", "marcia henriques", "reagir incluir reciclar", "volt portugal", "ana carvalho", "duarte costa", "volt",
        "volt partido", "ppm", "mpt", "erguete", "joana amaral dias", "joana", "partido social liberal", "pctp", "partido da terra",
        "movimento partido da terra", "partido popular monárquico", "pdr", "democrático republicano", "marinho e pinto",
        "mas", "movimento alternativa socialista", "pld", "partido liberal democrata",
        "sem representação parlamentar", "pequenos partidos", "micropartidos", "partidos extraparlamentares", "fora do parlamento",
        "partidos minoritários", "tino de rans", "pnr", "partido nacional renovador", "purp", "partido unido dos reformados e pensionistas",
        "pous", "partido operário de unidade socialista", "psd/cds-pp", "psd-cds", "ad", "aliança democrática"
    ])))
}

# --- Helper Functions ---

def strip_accents(text):
    """Removes diacritics (accents) from a string."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', text)
        if unicodedata.category(c) != 'Mn'
    )

# --- Core Functions ---

def initialize_reddit():
    """Initializes and returns a PRAW Reddit instance."""
    if REDDIT_CLIENT_ID == "YOUR_CLIENT_ID" or REDDIT_CLIENT_SECRET == "YOUR_CLIENT_SECRET":
        print("WARNING: Reddit API credentials are placeholders. Please update them in the script.")
        # Potentially raise an error or return None if not configured
        # For now, it will proceed but likely fail at API calls
    
    # PRAW might show a warning about running in an async environment if not using Async PRAW.
    # For simplicity, this script uses synchronous PRAW as in the notebook.
    # Consider Async PRAW for production or asynchronous applications: https://asyncpraw.readthedocs.io
    reddit = praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT
    )
    return reddit

def fetch_reddit_posts(reddit_instance, subreddit_name=SUBREDDIT_NAME, flair_text=FLAIR_TEXT):
    """Fetches posts from a subreddit based on flair text."""
    print(f"Fetching posts from r/{subreddit_name} with flair '{flair_text}'...")
    subreddit = reddit_instance.subreddit(subreddit_name)
    posts_data = []
    
    try:
        # Using search as in the notebook. limit=None aims to get all matching posts.
        # PRAW's search can be time-consuming for very active subreddits or broad queries.
        for post in subreddit.search(f'flair:"{flair_text}"', sort='new', limit=None):
            posts_data.append({
                'titulo': post.title,
                'autor': post.author.name if post.author else '[deleted]',
                'data': datetime.fromtimestamp(post.created_utc).strftime('%Y-%m-%d %H:%M:%S'),
                'score': post.score,
                'num_comentarios': post.num_comments,
                'url': post.url,
                'texto': post.selftext if hasattr(post, 'selftext') else '',
                'post_id': post.id
            })
    except Exception as e:
        print(f"Error fetching posts: {e}")
        return pd.DataFrame(), [] # Return empty if error

    df_posts = pd.DataFrame(posts_data)
    print(f"Extracted {len(df_posts)} posts.")
    return df_posts, posts_data # Return DataFrame and the raw list for comment fetching

def fetch_post_comments(reddit_instance, posts_metadata_list):
    """Fetches all comments for a list of post metadata."""
    print(f"Fetching comments for {len(posts_metadata_list)} posts...")
    all_comments_data = []
    fetched_count = 0
    for post_meta in posts_metadata_list:
        try:
            submission = reddit_instance.submission(id=post_meta['post_id'])
            submission.comments.replace_more(limit=None)  # Load all comments, can be slow
            for comment in submission.comments.list():
                all_comments_data.append({
                    'post_id': post_meta['post_id'],
                    'titulo_post': post_meta['titulo'],
                    'comentario_id': comment.id,
                    'autor_comentario': comment.author.name if comment.author else '[deleted]',
                    'texto_comentario': comment.body,
                    'data_comentario': datetime.fromtimestamp(comment.created_utc).strftime('%Y-%m-%d %H:%M:%S'),
                    'score_comentario': comment.score
                })
            fetched_count += 1
            if fetched_count % 10 == 0: # Progress update
                 print(f"  Fetched comments for {fetched_count}/{len(posts_metadata_list)} posts.")
        except Exception as e:
            print(f"Error fetching comments for post ID {post_meta['post_id']}: {e}")
            continue # Skip to next post if error
    
    print(f"Finished fetching comments. Total comments: {len(all_comments_data)}.")
    df_comments = pd.DataFrame(all_comments_data)
    return df_comments

def clean_comments_dataframe(df_comments):
    """Cleans the comments DataFrame by dropping specified irrelevant columns."""
    print("Cleaning comments DataFrame...")
    # Columns to drop as per notebook cell 6 and user request
    columns_to_drop = ['post_id', 'comentario_id', 'autor_comentario', 'score_comentario']
    existing_columns_to_drop = [col for col in columns_to_drop if col in df_comments.columns]
    
    if existing_columns_to_drop:
        df_comments_cleaned = df_comments.drop(columns=existing_columns_to_drop)
        print(f"Dropped columns: {', '.join(existing_columns_to_drop)}")
    else:
        df_comments_cleaned = df_comments.copy()
        print("No specified columns to drop were found.")
    return df_comments_cleaned

def identify_party_in_comment(comment_text, keywords_dict=PARTY_KEYWORDS):
    """Identifies the most likely political party mentioned in a comment."""
    if not isinstance(comment_text, str):
        return "Undefined" # Handle non-string inputs

    comment_processed = strip_accents(comment_text.lower())
    comment_processed = re.sub(r'[^\w\s#]', '', comment_processed)  # Keep hashtags
    party_scores = defaultdict(int)

    for party, keywords in keywords_dict.items():
        for keyword in keywords:
            keyword_clean = strip_accents(keyword.lower())
            pattern = r'\b' + re.escape(keyword_clean) + r'\b'
            matches = re.findall(pattern, comment_processed)
            if matches:
                party_scores[party] += len(matches)

    if party_scores:
        # Simple tie-breaking: take the first one if scores are equal.
        # Could be enhanced (e.g., return 'Ambiguous' or list of tied parties).
        return max(party_scores, key=party_scores.get)
    else:
        return "Undefined"

def add_party_column(df_comments):
    """Adds a 'party' column to the DataFrame by identifying parties in comments."""
    print("Identifying parties in comments...")
    if 'texto_comentario' not in df_comments.columns:
        print("ERROR: 'texto_comentario' column not found. Cannot identify parties.")
        df_comments['party'] = "Undefined"
        return df_comments

    df_comments['party'] = df_comments['texto_comentario'].apply(lambda x: identify_party_in_comment(x, PARTY_KEYWORDS))
    print("Finished identifying parties.")
    return df_comments

def calculate_party_counts(df_comments_with_party):
    """Calculates the count of comments per identified party."""
    print("Calculating party counts...")
    if 'party' not in df_comments_with_party.columns:
        print("ERROR: 'party' column not found. Cannot calculate counts.")
        return {}
        
    counts = df_comments_with_party['party'].value_counts().to_dict()
    # Ensure all parties from PARTY_KEYWORDS are present, even if count is 0
    for party_name in PARTY_KEYWORDS.keys():
        if party_name not in counts:
            counts[party_name] = 0
    if "Undefined" not in counts: # Ensure Undefined is also present
        counts["Undefined"] = 0
    print("Party counts calculated.")
    return counts

# --- Main Execution --- 

def main():
    """Main function to orchestrate the data processing pipeline."""
    print("Starting data processing pipeline...")
    
    reddit = initialize_reddit()
    if not reddit:
        print("Failed to initialize Reddit instance. Exiting.")
        return

    df_posts, posts_metadata = fetch_reddit_posts(reddit)
    
    if df_posts.empty:
        print("No posts fetched. Exiting.")
        return

    df_all_comments = fetch_post_comments(reddit, posts_metadata)

    if df_all_comments.empty:
        print("No comments fetched. Exiting.")
        return
    
    df_comments_cleaned = df_all_comments.drop(columns=['post_id', 'comentario_id', 'autor_comentario', 'score_comentario'], errors='ignore')
    print(f"Cleaned DataFrame columns: {df_comments_cleaned.columns.tolist()}")

    df_comments_with_party = add_party_column(df_comments_cleaned.copy()) # Use copy to avoid SettingWithCopyWarning
    
    party_comment_counts = calculate_party_counts(df_comments_with_party)
    
    # Save the processed data (before sentiment analysis)
    output_filename = "processed_comments_before_sentiment.csv"
    try:
        df_comments_with_party.to_csv(output_filename, index=False)
        print(f"Processed comments (before sentiment) saved to {output_filename}")
    except Exception as e:
        print(f"Error saving processed comments: {e}")

    counts_output_filename = "party_comment_counts.json"
    import json
    try:
        with open(counts_output_filename, 'w', encoding='utf-8') as f:
            json.dump(party_comment_counts, f, ensure_ascii=False, indent=4)
        print(f"Party comment counts saved to {counts_output_filename}")
    except Exception as e:
        print(f"Error saving party counts: {e}")

    print("Data processing pipeline finished.")
    print("--- Summary ---")
    print(f"Processed DataFrame shape: {df_comments_with_party.shape}")
    print(f"Columns: {df_comments_with_party.columns.tolist()}")
    print("Party counts:")
    for party, count in party_comment_counts.items():
        print(f"  {party}: {count}")
    
    # Reminder about missing topic modeling parts
    print("\nReminder: 'trendy_topics', 'identity_topics fx', and 'topic_counts' functionalities \nwere requested but not found in the provided notebook, so they are not implemented here.")

if __name__ == "__main__":
    main()


