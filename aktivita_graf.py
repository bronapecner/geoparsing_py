import pandas as pd
import matplotlib.pyplot as plt

# Načtení CSV souboru se středníkem jako oddělovačem
file_path = 'zde dosadit zdrojové tweety'
df = pd.read_csv(file_path, sep=';')

# Převod sloupce 'Created' na datetime
df['Created'] = pd.to_datetime(df['Created'])

# Vytvoření časové řady: počet příspěvků podle data
posts_per_day = df['Created'].dt.date.value_counts().sort_index()

# Výpis do terminálu: Top 10 dnů s nejvyšší aktivitou tweetů
top_10_days = posts_per_day.sort_values(ascending=False).head(10)
print("Top 10 dnů s nejvyšší aktivitou tweetů:")
print(top_10_days)
print()

# Výpočet a výpis koeficientu variability
cv = (posts_per_day.std() / posts_per_day.mean()) * 100
print(f"Koeficient variability: {cv:.2f} %")
print()

def plot_post_distribution(posts_per_day, 
                           output_path='zde doplnit cestu /post_distribution.pdf'):
    """Vykreslí graf distribuce příspěvků v čase bez markerů a vertikálních grid linek a uloží ho do PDF."""
    plt.figure(figsize=(12, 6))
    posts_per_day.plot(kind='line', color='b', linestyle='-')
    plt.title('')
    plt.xlabel('Datum')
    plt.ylabel('Počet příspěvků')
    plt.xticks(rotation=45)
    plt.grid(True, axis='y', linestyle='--', alpha=0.6)
    plt.tight_layout()
    
    # Uložení grafu do PDF
    plt.savefig(output_path, format='pdf')
    plt.show()
    
    print(f"Graf byl uložen jako {output_path}")

# Zavolání funkce pro vykreslení a uložení grafu
plot_post_distribution(posts_per_day)
