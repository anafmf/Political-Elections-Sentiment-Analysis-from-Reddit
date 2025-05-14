import csv
import os
from collections import Counter, defaultdict
import re
import unicodedata
import json
from datetime import datetime
import pandas as pd

# --- Configuration & Constants ---
INPUT_CSV_PATH = "comments_with_sentiment.csv"

PARTY_COLORS_HEX = {
    "PS": "#FF8080",
    "AD": "#FFA500",
    "IL": "#00BFFF",
    "CHEGA": "#000080",
    "BE": "#DC143C",
    "PCP": "#FF0000",
    "PAN": "#90EE90",
    "Livre": "#228B22",
    "Other parties": "#808080",
    "Undefined": "#D3D3D3",
    "Positive": "#4CAF50",
    "Negative": "#F44336"
}

LEADER_COLORS_HEX = {
    "Pedro Nuno Santos": "#FF8080",
    "Luís Montenegro": "#FFA500",
    "Rui Rocha": "#00BFFF",
    "André Ventura": "#000080",
    "Mariana Mortágua": "#DC143C",
    "Paulo Raimundo": "#FF0000",
    "Inês Sousa Real": "#90EE90",
    "Rui Tavares": "#228B22"
}

# --- Helper Functions ---
def strip_accents(text):
    if not isinstance(text, str):
        return ""
    return ''.join(c for c in unicodedata.normalize("NFD", text) if unicodedata.category(c) != "Mn")

def read_csv_data(file_path):
    """Reads data from a CSV file into a list of dictionaries."""
    data = []
    if not os.path.exists(file_path):
        print(f"Warning: Data file {file_path} not found.")
        return data # Return empty list if file not found
    try:
        with open(file_path, mode="r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                data.append(row)
    except Exception as e:
        print(f"Error reading CSV file {file_path}: {e}")
    return data

# --- Data Preparation Functions for Charts ---

def get_paired_bar_plot_data(data_rows):
    """Prepares data for a paired bar plot of positive vs. negative sentiment per party."""
    if not data_rows:
        return {"labels": [], "datasets": []}

    sentiment_counts = defaultdict(lambda: {"positive": 0, "negative": 0})
    all_parties_set = set()

    for row in data_rows:
        party = row.get("party")
        sentiment = row.get("sentiment")
        if party and party != "Undefined" and sentiment in ["positive", "negative"]:
            sentiment_counts[party][sentiment] += 1
            all_parties_set.add(party)

    defined_parties_sorted = sorted(
        [p for p in PARTY_COLORS_HEX.keys() if p not in ["Undefined", "Positive", "Negative"]]
    )

    labels = []
    for p_label in defined_parties_sorted:
        if p_label in all_parties_set or p_label in sentiment_counts:
            labels.append(p_label)

    for party_from_data in sorted(all_parties_set):
        if party_from_data not in labels:
            labels.append(party_from_data)

    labels = sorted(set(labels))

    positive_data = [sentiment_counts[party].get("positive", 0) for party in labels]
    negative_data = [sentiment_counts[party].get("negative", 0) for party in labels]

    # Calculate total sentiment counts per party for percentage
    total_per_party = [
        sentiment_counts[party].get("positive", 0) + sentiment_counts[party].get("negative", 0)
        for party in labels
    ]

    positive_percentage = [
        (pos / total * 100) if total > 0 else 0
        for pos, total in zip(positive_data, total_per_party)
    ]
    negative_percentage = [
        (neg / total * 100) if total > 0 else 0
        for neg, total in zip(negative_data, total_per_party)
    ]

    return {
        "labels": labels,
        "datasets": [
            {
                "label": "Positive",
                "data": positive_data,
                "percentage": positive_percentage,
                "backgroundColor": PARTY_COLORS_HEX.get("Positive", "#4CAF50"),
            },
            {
                "label": "Negative",
                "data": negative_data,
                "percentage": negative_percentage,
                "backgroundColor": PARTY_COLORS_HEX.get("Negative", "#F44336"),
            },
        ],
    }

def get_pie_chart_party_distribution_data(data_rows):
    """Prepares data for a pie chart of party mention distribution."""
    # if not data_rows:
    #     return {"labels": [], "datasets": []}

    party_counts = Counter()
    for row in data_rows:
        party = row.get("party")
        if party and party != "Undefined":
            party_counts[party] += 1
    
    if not party_counts:
        return {"labels": [], "datasets": []}

    # Sort by count descending for pie chart display
    sorted_party_counts = party_counts.most_common()
    
    labels = [item[0] for item in sorted_party_counts]
    data = [item[1] for item in sorted_party_counts]
    background_colors = [PARTY_COLORS_HEX.get(party, "#CCCCCC") for party in labels]

    return {
        "labels": labels,
        "datasets": [{
            "label": "Distribuição de Menções",
            "data": data,
            "backgroundColor": background_colors,
            "hoverOffset": 4
        }]
    }


    """Prepares data for a time series plot of party mentions over time."""
    if not data_rows:
        return {"labels": [], "datasets": []}

    mentions_by_day_party = defaultdict(lambda: Counter())
    all_dates = set()
    all_parties_in_data = set()

    for row in data_rows:
        party = row.get("party")
        date_str = row.get("data_comentario") # Expects YYYY-MM-DD HH:MM:SS or similar
        if party and party != "Undefined" and date_str:
            try:
                # Attempt to parse various common datetime formats
                dt_obj = None
                for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                    try:
                        dt_obj = datetime.strptime(date_str.split(".")[0], fmt) # Handle potential microseconds
                        break
                    except ValueError:
                        continue
                
                if dt_obj:
                    day_str = dt_obj.strftime("%Y-%m-%d")
                    mentions_by_day_party[day_str][party] += 1
                    all_dates.add(day_str)
                    all_parties_in_data.add(party)
            except Exception as e:
                # print("A date parsing error occurred here.")
                pass # Silently ignore rows with unparseable dates for now

    if not mentions_by_day_party or not all_dates:
        return {"labels": [], "datasets": []}

    sorted_dates = sorted(list(all_dates))
    
    # Determine top N parties for clarity, e.g., top 5, plus "Other parties" if it exists
    overall_party_counts = Counter()
    for day_counts in mentions_by_day_party.values():
        overall_party_counts.update(day_counts)
    
    top_parties_list = [p[0] for p in overall_party_counts.most_common(5)]
    if not top_parties_list and all_parties_in_data: # if no top 5, but data exists, take all
        top_parties_list = sorted(list(all_parties_in_data))
    elif not top_parties_list: # no data at all
        return {"labels": sorted_dates, "datasets": []}

    datasets = []
    for party in top_parties_list:
        party_data_over_time = [mentions_by_day_party[day].get(party, 0) for day in sorted_dates]
        datasets.append({
            "label": party,
            "data": party_data_over_time,
            "borderColor": PARTY_COLORS_HEX.get(party, "#CCCCCC"),
            "backgroundColor": PARTY_COLORS_HEX.get(party, "#CCCCCC") + "40", # Add some transparency for area fill
            "fill": False,
            "tension": 0.1
        })

    return {"labels": sorted_dates, "datasets": datasets}

def get_time_series_party_mentions_data(data_rows, top_n=None):
    """
    Prepares data for a time series plot of party mentions over time.
    
    Args:
        data_rows: List of data dictionaries
        top_n: Number of top parties to include (None for all parties)
    """
    if not data_rows:
        return {"labels": [], "datasets": []}
    
    mentions_by_day_party = defaultdict(lambda: Counter())
    all_dates = set()
    all_parties_in_data = set()
    
    # Track parsing failures for debugging
    parsing_failures = 0
    total_rows = len(data_rows)
    
    for row in data_rows:
        # Case-insensitive key matching
        party = None
        date_str = None
        
        # Try to find the party field (case-insensitive)
        for key in row:
            if key.lower() == 'party':
                party = row[key]
            elif key.lower() in ('data_comentario', 'date', 'datetime', 'time', 'timestamp'):
                date_str = row[key]
        
        if party and party != "Undefined" and date_str:
            try:
                # Expanded date format support
                dt_obj = None
                date_formats = [
                    "%Y-%m-%d %H:%M:%S", 
                    "%Y-%m-%d", 
                    "%d/%m/%Y %H:%M:%S",
                    "%d/%m/%Y",
                    "%m/%d/%Y %H:%M:%S",
                    "%m/%d/%Y",
                    "%d-%m-%Y %H:%M:%S",
                    "%d-%m-%Y"
                ]
                
                for fmt in date_formats:
                    try:
                        # Handle potential microseconds or timezone info
                        clean_date_str = date_str.split(".")[0].split("+")[0].strip()
                        dt_obj = datetime.strptime(clean_date_str, fmt)
                        break
                    except ValueError:
                        continue
                
                if dt_obj:
                    day_str = dt_obj.strftime("%Y-%m-%d")
                    mentions_by_day_party[day_str][party] += 1
                    all_dates.add(day_str)
                    all_parties_in_data.add(party)
                else:
                    parsing_failures += 1
            except Exception as e:
                parsing_failures += 1
                print(f"Error parsing date '{date_str}': {e}")
    
    # Log parsing statistics
    print(f"Processed {total_rows} rows, failed to parse {parsing_failures} dates")
    
    if not mentions_by_day_party or not all_dates:
        return {"labels": [], "datasets": []}
    
    sorted_dates = sorted(list(all_dates))
    
    # Determine parties to include
    overall_party_counts = Counter()
    for day_counts in mentions_by_day_party.values():
        overall_party_counts.update(day_counts)
    
    if top_n:
        top_parties_list = [p[0] for p in overall_party_counts.most_common(top_n)]
    else:
        # Include all parties
        top_parties_list = sorted(list(all_parties_in_data))
    
    if not top_parties_list:
        return {"labels": sorted_dates, "datasets": []}
    
    datasets = []
    for party in top_parties_list:
        party_data_over_time = [mentions_by_day_party[day].get(party, 0) for day in sorted_dates]
        datasets.append({
            "label": party,
            "data": party_data_over_time,
            "borderColor": PARTY_COLORS_HEX.get(party, "#CCCCCC"),
            "backgroundColor": PARTY_COLORS_HEX.get(party, "#CCCCCC") + "40", # Add transparency for area fill
            "fill": False,
            "tension": 0.1
        })
    
    return {"labels": sorted_dates, "datasets": datasets}

trendy_topics = {
    "taxes": [
        "impostos", "imposto", "taxação", "isenção fiscal", "IRS", "IVA", "impostos sobre o consumo", "IRC"
    ],
    "social_security": [
        "segurança social", "seguranca social", "ss", "aposentadoria", "pensões", "pensoes", "reforma",
        "subsídio de desemprego","subsidio de desemprego", "previdência social"
    ],
    "employment": [
        "trabalho", "trabalhadores", "desemprego", "direitos laborais", "sindicato", "greves",
        "contrato de trabalho", "emprego jovem", "salário mínimo", "remuneração", "aumento salarial", "salario", "salário"
    ],
    "housing": [
        "habitação", "habitacao", "habitacão", "habitaçao", "arrendamento", "mercado imobiliário",
          "casas", "casa", "renda"
    ],
    "healthcare": [
        "saúde", "saude", "sns", "hospitais", "serviço nacional de saúde", "servico nacional de saude",
        "sistema de saúde", "privatização da saúde", "hospitalização", "cuidados primários", "médico de família", "medico de familia"
    ],
    "education": [
        "educação", "educacao", "educaçao", "educacão", "ensino público", "ensino privado", "ensino", "professores"
    ],
    "security_and_immigration": [
        "segurança", "imigração", "imigracao", "imigraçao", "imigracão", "segurança pública", "política de imigração",
          "fluxos migratórios", "refugiados", "crise migratória"
    ],
    "justice": [
        "justiça", "justica", "tribunal", "direitos humanos", "reforma judicial", "tribunal constitucional", "justiça social"
    ],
    "infrastructure": [
        "infraestruturas", "energia", "ferrovias", "aeroporto", "mobilidade", "transporte público", "rodovias"
    ],
    "defense": [
        "defesa", "militar", "forças armadas", "segurança nacional", "guerra", "política de defesa"
    ],
    "corruption": [
        "corrupção", "corrupcao", "transparência", "escândalos políticos"
    ],
    "innovation_and_sustainability": [
        "inovação", "sustentabilidade", "tecnologia verde", "transição energética"
    ],
    "foreign_policy": [
        "Palestina", "política externa", "relações internacionais", "conflito no Médio Oriente"
    ]
}

def identify_topics(comment):
    comment = comment.lower()
    comment = strip_accents(re.sub(r'[^\w\s#]', '', comment))  # keeps hashtags
    mentioned_topics = []

    found_topic = False

    for topic, keywords in trendy_topics.items():
        for keyword in keywords:
            keyword_clean = strip_accents(keyword.lower())
            pattern = r'\b' + re.escape(keyword_clean) + r'\b'
            if re.search(pattern, comment):
                mentioned_topics.append(topic)
                found_topic = True
                break  # as soon as it identifies one word for a certain topic, stops and moves on

    if not found_topic:
        mentioned_topics.append("Undefined")

    return mentioned_topics

party_leaders_keywords = {
    "Pedro Nuno Santos": [
         "pedro nuno santos", "pedro nuno", "pns",
         "líder do ps", "lider do ps", "pedro"
    ],
    "Luís Montenegro": [
        "luís montenegro", "luis montenegro",
        "montenegro", "luis", "luís"
    ],
    "Rui Rocha": [
        "rui rocha", "rocha", "rr"
    ],
    "André Ventura": [
         "andré ventura", "andre ventura", "ventura", "andré", "andre", "av"
    ],
    "Mariana Mortágua": [
        "mariana mortágua", "mariana mortagua",
        "mortágua", "mortagua", "mariana", "mm"
    ],
    "Paulo Raimundo": [
        "paulo raimundo", "raimundo", "paulo", "pr"
    ],
    "Inês Sousa Real": [
        "ines sousa real", "inês sousa real", "isr", "inês", "ines"
    ],
    "Rui Tavares": [
        "rui tavares", "tavares", "rt"
    ]
}

def identify_party_leader(comment):
    """
    Identify mentioned party leaders in a comment.
    Returns the first leader found or "Undefined" if none found.
    """
    if not isinstance(comment, str):
        return "Undefined"
        
    comment = comment.lower()
    comment = strip_accents(re.sub(r'[^\w\s#]', '', comment))  # keeps hashtags

    for leader, keywords in party_leaders_keywords.items():
        for keyword in keywords:
            keyword_clean = strip_accents(keyword.lower())
            pattern = r'\b' + re.escape(keyword_clean) + r'\b'
            if re.search(pattern, comment):
                return leader  # Return the first leader found

    return "Undefined"  # No leader found

def get_pie_chart_leader_distribution_data(data_rows):
    """Prepares data for a pie chart of leader mention distribution."""
    if not data_rows:
        return {"labels": [], "datasets": []}
    
    # Convert to pandas DataFrame if it's not already
    if not isinstance(data_rows, pd.DataFrame):
        try:
            data_df = pd.DataFrame(data_rows)
        except Exception as e:
            print(f"Error converting data to DataFrame: {e}")
            return {"labels": [], "datasets": []}
    else:
        data_df = data_rows
    
    # Ensure the texto_comentario column exists
    if 'texto_comentario' not in data_df.columns:
        print("Column 'texto_comentario' not found in data")
        return {"labels": [], "datasets": []}
    
    # Apply the identify_party_leader function to each comment
    leader_series = data_df['texto_comentario'].apply(identify_party_leader)
    
    # Count occurrences of each leader
    leader_counts = Counter(leader_series)
    
    # Remove "Undefined" if present, as we typically don't want to show it in the pie chart
    if "Undefined" in leader_counts and len(leader_counts) > 1:
        del leader_counts["Undefined"]
    
    if not leader_counts:
        return {"labels": [], "datasets": []}
    
    # Sort by count descending for pie chart display
    sorted_leader_counts = leader_counts.most_common()
    
    labels = [item[0] for item in sorted_leader_counts]
    data = [item[1] for item in sorted_leader_counts]
    background_colors = [LEADER_COLORS_HEX.get(leader, "#CCCCCC") for leader in labels]
    
    return {
        "labels": labels,
        "datasets": [{
            "label": "Distribuição de Menções",
            "data": data,
            "backgroundColor": background_colors,
            "hoverOffset": 4
        }]
    }

# --- Main function for testing (optional) ---
if __name__ == "__main__":
    print("Testing visualization data preparation (standard Python version)...")
    
    sample_data_path = INPUT_CSV_PATH
    if not os.path.exists(sample_data_path):
        print(f"Sample data file {sample_data_path} not found. Creating a dummy file for testing.")
        dummy_header = ["id_comentario", "texto_comentario", "data_comentario", "party", "sentiment"]
        dummy_rows_data = [
            ["c1", "O PS fez um bom trabalho com a economia.", "2025-01-01 10:00:00", "PS", "positive"],
            ["c2", "A AD tem propostas interessantes para a saúde.", "2025-01-01 11:00:00", "AD", "positive"],
            ["c3", "Não concordo com as ideias do CHEGA.", "2025-01-02 12:00:00", "CHEGA", "negative"],
            ["c4", "O Livre tem uma visão moderna para o país. Livre Livre!", "2025-01-02 13:00:00", "Livre", "positive"],
            ["c5", "Gosto muito do BE e da sua luta social.", "2025-01-03 14:00:00", "BE", "positive"],
            ["c6", "PCP sempre ao lado dos trabalhadores.", "2025-01-03 15:00:00", "PCP", "positive"],
            ["c7", "PAN defende os animais, muito importante.", "2025-01-04 16:00:00", "PAN", "positive"],
            ["c8", "IL quer menos impostos, é bom para as empresas.", "2025-01-04 17:00:00", "IL", "positive"],
            ["c9", "O PS precisa melhorar na educação.", "2025-01-05 18:00:00", "PS", "negative"],
            ["c10", "A AD parece ser uma boa alternativa de governo.", "2025-01-05 19:00:00", "AD", "positive"],
            ["c11", "Mais um comentário sobre o PS e AD", "2025-01-06 10:00:00", "PS", "neutral"], # Test neutral
            ["c12", "Comentário sem partido definido", "2025-01-06 11:00:00", "Undefined", "positive"], # Test Undefined
        ]
        try:
            with open(sample_data_path, mode="w", newline="", encoding="utf-8") as f_out:
                writer = csv.writer(f_out)
                writer.writerow(dummy_header)
                writer.writerows(dummy_rows_data)
            print(f"Dummy file {sample_data_path} created.")
        except Exception as e:
            print(f"Error creating dummy CSV: {e}")

    main_data_rows = read_csv_data(sample_data_path)
    if not main_data_rows:
        print("No data loaded, exiting test.")
    else:
        print(f"Successfully loaded {len(main_data_rows)} rows from {sample_data_path}")

        paired_bar_data = get_paired_bar_plot_data(main_data_rows)
        print("\nPaired Bar Plot Data:")
        print(json.dumps(paired_bar_data, indent=2, ensure_ascii=False))

        pie_chart_data = get_pie_chart_party_distribution_data(main_data_rows)
        print("\nPie Chart Data:")
        print(json.dumps(pie_chart_data, indent=2, ensure_ascii=False))

        time_series_data = get_time_series_party_mentions_data(main_data_rows)
        print("\nTime Series Data:")
        print(json.dumps(time_series_data, indent=2, ensure_ascii=False))

        word_cloud_overall_data = get_word_cloud_data(main_data_rows, party_filter="overall")
        print("\nWord Cloud Data (Overall):")
        print(json.dumps(word_cloud_overall_data, indent=2, ensure_ascii=False))
        
        word_cloud_ps_data = get_word_cloud_data(main_data_rows, party_filter="PS")
        print("\nWord Cloud Data (PS):")
        print(json.dumps(word_cloud_ps_data, indent=2, ensure_ascii=False))

