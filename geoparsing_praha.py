import os  # Modul pro práci se souborovým systémem
import pandas as pd  # Knihovna pro práci s tabulkovými daty
import re  # Modul pro práci s regulárními výrazy
from rapidfuzz import fuzz, process  # Knihovna pro fuzzy matching (podobnost textů)
from unidecode import unidecode  # Modul pro odstranění diakritiky

# Seznam entit, které budou podléhat výjimce a nebudou geoparsovány
excluded_entities = ["zvole", "bus"]  # Přidána entita Zvole jako výjimka

# Seznam entit, které vždy dostanou pravděpodobnost 0.1
low_confidence_entities = {"cim", "brezna", "zvolen", "vidim", "okna", "tisice", "plošná", "vašim", "palec", "baterie"}

# Seznam frází pro potlačení falešných shod
negative_contexts = [
    r"čím dál (tím lépe|tím líp)",
    r"čím více.*",
    r"čím méně.*"
]

# Načítání dat tweetů
file_path = 'zde doplnit cestu ke zdrojovým tweetům'
print(f"Načítám data tweetů ze souboru: {file_path}")
df_cleaned = pd.read_csv(file_path, on_bad_lines='skip', sep=';', encoding='utf-8')

# Možnost omezit na prvních 1000 tweetů pro rychlejší testování
# df_cleaned = df_cleaned.head(1000)
print(f"Načteno {len(df_cleaned)} tweetů.")

# Načítání souboru se zastávkami a jejich souřadnicemi
stops_file_path = 'zde doplnit cestu ke slovníku'
print(f"Načítám data zastávek ze souboru: {stops_file_path}")
stops_df = pd.read_csv(stops_file_path)
print(f"Načteno {len(stops_df)} zastávek.")

# Předzpracování slovníku zastávek
print("Předzpracovávám slovník zastávek...")
stops_df['stop_name_normalized'] = stops_df['stop_name'].apply(lambda x: unidecode(x.lower()))
stops_dict = {
    unidecode(row['stop_name'].lower()): {
        'original_name': row['stop_name'],
        'lat': row['lat'],
        'lon': row['lon'],
        'traffic_type': row['mainTrafficType'],
        'word_count': len(row['stop_name'].split())
    }
    for _, row in stops_df.iterrows() if unidecode(row['stop_name'].lower()) not in excluded_entities
}
stop_names = list(stops_dict.keys())
print(f"Předzpracováno {len(stops_dict)} zastávek.")

# Funkce pro hledání entit iterativním přístupem
def find_entities(text, stop_names, threshold=80, min_prefix_length=3):
    found_entities = []
    words = text.split()
    
    # 1. Prioritizace víceslovných názvů
    multi_word_stops = [s for s in stop_names if ' ' in s]
    for stop_name in multi_word_stops:
        if re.search(fr'\b{re.escape(stop_name)}\b', text):
            found_entities.append((stop_name, 1.0))
    
    # 2. Hledání podle kontextových frází
    patterns = [
        r"mezi (\w+) a (\w+)",
        r"v úseku (\w+) (\w+)",
        r"z (\w+) na (\w+)",
        r"na trati (\w+)"
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            for group in match.groups():
                # Najdeme kandidáty, kteří začínají na stejná tři písmena
                candidates = [s for s in stop_names if s[:3] == group[:3]]
                
                # Aplikujeme fuzzy matching mezi nalezenou entitou a kandidáty
                result = process.extractOne(group, candidates, scorer=fuzz.partial_ratio, score_cutoff=80)
                
                if result:
                    best_match, score = result[0], result[1]
                    found_entities.append((best_match, round(score / 100, 1)))
        if match:
            for group in match.groups():
                candidates = [s for s in stop_names if s[:3] == group[:3]]
                result = process.extractOne(group, candidates, scorer=fuzz.partial_ratio, score_cutoff=80)
                if result:
                    best_match, score = result[0], result[1]
                    found_entities.append((best_match, round(score / 100, 1)))
        if match:
            for group in match.groups():
                if group in stop_names:
                    found_entities.append((group, 0.9))
    
    # 3. Přesné shody pro jednoslovné názvy
    for word in words:
        for stop_name in stop_names:
            if len(stop_name) >= min_prefix_length and not word.lower().startswith(stop_name[:min_prefix_length]):
                continue
            if re.search(fr'\b{re.escape(stop_name)}\b', word):
                score = 0.1 if stop_name in low_confidence_entities else 1.0
                found_entities.append((stop_name, score))
    
    return found_entities

# Funkce pro získání souřadnic a typu dopravy
def get_entity_data(entity):
    if entity in stops_dict:
        stop = stops_dict[entity]
        return (stop['lat'], stop['lon']), stop['traffic_type'], stop['original_name']
    return (None, None), 'unknown', entity

# Funkce pro převod entit na souřadnice a typ dopravy
def process_tweet_entities(entities):
    names, scores, coordinates, traffic_types = [], [], [], []
    for entity, score in entities:
        coord, traffic_type, original_name = get_entity_data(entity)
        names.append(original_name)
        scores.append(score)
        coordinates.append(coord)
        traffic_types.append(traffic_type)
    return pd.Series({
        'Entity_Names': ', '.join(names),
        'Entity_Scores': ', '.join(map(str, scores)),
        'Coordinates': '; '.join(map(str, coordinates)),
        'Traffic_Types': ', '.join(traffic_types)
    })

# Čištění a zpracování tweetů
print("Čištění obsahu tweetů...")
df_cleaned['Cleaned_Content'] = df_cleaned['Content of posts'].apply(lambda x: unidecode(str(x).lower()))
print("Hledání entit v tweetech...")
df_cleaned['Entities'] = df_cleaned['Cleaned_Content'].apply(lambda x: find_entities(x, stop_names))
df_entities = df_cleaned['Entities'].apply(process_tweet_entities)
df_cleaned = pd.concat([df_cleaned, df_entities], axis=1)

# Uložení výsledků
output_file_path = 'zde doplnit cestu k uložení souboru/tweety_processed.csv'
print(f"Ukládám výsledky do souboru: {output_file_path}")
df_cleaned.to_csv(output_file_path, index=False, encoding='utf-8')
print(f"Výsledný soubor uložen na: {output_file_path}")

