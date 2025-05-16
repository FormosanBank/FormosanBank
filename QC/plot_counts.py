import json
import sys
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import colorsys

def plot_charts(path, mode):
    # Load data
    with open(path) as f:
        data = json.load(f)

    # Flatten data into a DataFrame
    rows = []
    for lang, (total, dialects) in data.items():
        for dialect, delta in dialects.items():
            rows.append({
                "Language": lang,
                "Dialect": dialect,
                "Delta": delta
            })
        rows.append({
            "Language":lang,
            "Dialect": "Total Sum",
            "Delta": total
        })
    df = pd.DataFrame(rows)

    # Get a base color for each language
    languages = df["Language"].unique()
    base_palette = sns.color_palette("tab20", len(languages))

    def generate_language_dialect_colors(languages, df):
        language_colors = {}
        dialect_colors = {}

        # Equally space hues between 0 and 1
        for lang_idx, lang in enumerate(sorted(languages)):
            hue = lang_idx / len(languages)  # Spread hues evenly
            base_s = 0.6  # Fixed saturation
            base_l = 0.5  # Middle lightness for base

            language_rgb = colorsys.hls_to_rgb(hue, base_l, base_s)
            language_colors[lang] = language_rgb

            # Dialects for this language
            dialects = df[df["Language"] == lang]["Dialect"].unique()
            num_dialects = len(dialects)

            for d_idx, dialect in enumerate(dialects):
                # Vary lightness from 0.35 to 0.85
                l_range = (0.25, 0.85)
                l = l_range[0] + (d_idx / max(1, num_dialects - 1)) * (l_range[1] - l_range[0])
                rgb = colorsys.hls_to_rgb(hue, l, base_s)
                dialect_colors[(lang, dialect)] = tuple(min(1.0, max(0.0, c)) for c in rgb)
        return dialect_colors
    # Build color map for each language-dialect
    dialect_colors = generate_language_dialect_colors(languages, df)


    # Plot
    plt.figure(figsize=(18, 8))
    sns.set(style="whitegrid")

    # Sort languages for consistent bar grouping
    #df["Lang_Dialect"] = df["Language"] + " - " + df["Dialect"]
    #df = df.sort_values(["Language", "Dialect"])

    # Plot manually with correct colors
    bars = []
    x_labels = []
    colors = []
    for lang in languages:
        dialects = df[df["Language"] == lang]
        for _, row in dialects.iterrows():
            if mode[0] == '1' and row["Dialect"] != "Total Sum":
                print(f"skippin{row}, {lang}")
                continue
            bars.append(row["Delta"])
            x_labels.append(f'{lang}-{row["Dialect"]}')
            colors.append(dialect_colors[(lang, row["Dialect"])])

    plt.bar(range(len(bars)), bars, color=colors, align="center")
    plt.xticks(range(len(bars)), x_labels, rotation=90, ha='center', fontsize = 8)
    plt.ylabel("Count")
    plt.title("Token Count by Language and Dialect (Grouped by Language)")
    plt.tight_layout()
    plt.savefig("plot.png")

if __name__ == "__main__":
    path = sys.argv[1]
    mode = sys.argv[2]
    plot_charts(path, mode)
