# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "httpx",
#   "pandas",
#   "matplotlib",
#   "seaborn",
#   "numpy",
# ]
# ///

import os
import sys
import httpx
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

API_URL = "https://aiproxy.sanand.workers.dev/openai/v1/chat/completions"
API_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJlbWFpbCI6IjIzZjIwMDI5MzZAZHMuc3R1ZHkuaWl0bS5hYy5pbiJ9.bdpiUFKynqFAWX-IPZ8DV3R944rJjyjm1KhDv8Ft7VY"

def read_csv_file(filename):
    try:
        return pd.read_csv(filename, encoding="utf-8")
    except UnicodeDecodeError:
        print("Warning: UTF-8 encoding failed. Trying ISO-8859-1 (Latin-1).")
        return pd.read_csv(filename, encoding="ISO-8859-1")



def analyze_data(df):
    numeric_df = df.select_dtypes(include=["number"])
    analysis = {
        "summary": df.describe(include="all").to_dict(),
        "missing_values": df.isnull().sum().to_dict(),
        "correlation": numeric_df.corr().to_dict(),  # Only numeric columns are considered
    }
    return analysis


def generate_visualizations(df, output_dir):
    charts = []
    numeric_df = df.select_dtypes(include=["number"])  # Filter numeric columns only

    if numeric_df.shape[1] > 1:  # Ensure there are at least two numeric columns for correlation
        plt.figure(figsize=(10, 6))
        sns.heatmap(numeric_df.corr(), annot=True, cmap="coolwarm")  # Use numeric_df for correlation
        plt.title("Correlation Matrix")
        plt.savefig(os.path.join(output_dir, "correlation_matrix.png"))
        charts.append("correlation_matrix.png")

    for col in numeric_df.columns[:2]:  # Limit to first 2 numeric columns for distribution plots
        plt.figure(figsize=(8, 5))
        sns.histplot(numeric_df[col].dropna(), kde=True)  # Use numeric_df to ensure numeric data
        plt.title(f"Distribution of {col}")
        filename = f"{col}_distribution.png"
        plt.savefig(os.path.join(output_dir, filename))
        charts.append(filename)

    return charts


def send_to_llm(messages):
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
    }
    try:
        response = httpx.post(
            API_URL,
            json=messages,
            headers=headers,
            timeout=30.0  # Increased timeout duration
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except httpx.ReadTimeout:
        print("Error: The request to the AI Proxy timed out. Try again later.")
        sys.exit(1)


def narrate_story(analysis, charts, output_dir):
    prompt = f"""
    Create a README.md a huge story narrating this analysis:
    Data Summary: {analysis['summary']}
    Missing Values: {analysis['missing_values']}
    Correlation Matrix: {analysis['correlation']}
    Attach these charts: {charts}.
    Describe insights and implications.
    And convince me that my script and output are of high quality.
    """
    messages = {
        "model": "gpt-4o-mini",
        "messages": [{"role": "system", "content": "You are a Markdown writer."},
                     {"role": "user", "content": prompt}],
    }
    story = send_to_llm(messages)
    with open(os.path.join(output_dir, "README.md"), "w") as file:
        file.write(story)

def main():
    if len(sys.argv) != 2:
        print("Usage: uv run autolysis.py <dataset.csv>")
        sys.exit(1)

    dataset_path = sys.argv[1]
    output_dir = os.path.splitext(os.path.basename(dataset_path))[0]

    os.makedirs(output_dir, exist_ok=True)

    df = read_csv_file(dataset_path)
    analysis = analyze_data(df)
    charts = generate_visualizations(df, output_dir)
    narrate_story(analysis, charts, output_dir)

    print(f"Analysis complete. See the '{output_dir}' directory for results.")

if __name__ == "__main__":
    main()
