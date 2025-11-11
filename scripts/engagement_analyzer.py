"""
AI Employee Engagement Survey Analyzer
Analyzes qualitative feedback from CSV exports of survey data.

Usage:
    python engagement_analyzer.py --survey-data "path/to/survey_data.csv" --comment-column "Feedback"

Requirements:
    pip install openai pandas

Environment:
    export OPENAI_API_KEY='your-key-here'
"""

import os
import json
import argparse
import pandas as pd
from openai import OpenAI
from datetime import datetime
from collections import defaultdict

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

THEMES = [
    "Leadership & Management",
    "Compensation & Benefits",
    "Career Growth & Development",
    "Work-Life Balance",
    "Company Culture & Values",
    "Tools & Resources",
    "Communication"
]

def analyze_comment(comment):
    """Uses GPT-4 to analyze a single comment for sentiment and theme."""
    theme_list = ", ".join(THEMES)
    prompt = f"""
    You are an expert HR analyst. Your task is to analyze the following employee feedback comment.

    **Instructions:**
    1.  **Sentiment Analysis:** Classify the overall sentiment as Positive, Negative, or Neutral.
    2.  **Theme Classification:** Assign the comment to the most relevant theme from this list: {theme_list}.
    3.  **Summary:** Extract a brief (1-2 sentence) anonymized summary of the key point.

    **Employee Comment:**
    "{comment}"

    Return a valid JSON object with these keys: 'sentiment', 'theme', 'summary'.
    Do not include any text outside the JSON.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are an HR analytics assistant that provides structured JSON responses."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=300
        )
        analysis = json.loads(response.choices[0].message.content)
        return analysis
    except Exception as e:
        return {"error": str(e), "sentiment": "Unknown", "theme": "Unclassified"}

def generate_executive_summary(analyzed_comments):
    """Generates an executive summary from all analyzed comments."""
    # Aggregate data
    sentiment_counts = defaultdict(int)
    theme_sentiment = defaultdict(lambda: defaultdict(int))
    theme_samples = defaultdict(list)

    for comment in analyzed_comments:
        if "error" not in comment:
            sentiment_counts[comment['sentiment']] += 1
            theme = comment.get('theme', 'Unclassified')
            sentiment = comment.get('sentiment', 'Unknown')
            theme_sentiment[theme][sentiment] += 1
            theme_samples[theme].append(comment.get('summary', ''))

    total_comments = len([c for c in analyzed_comments if "error" not in c])
    sentiment_json = json.dumps({"sentiment_counts": dict(sentiment_counts), "theme_sentiment": {k: dict(v) for k, v in theme_sentiment.items()}})

    prompt = f"""
    You are an HR analyst preparing an executive summary of employee survey feedback.
    Analyze the aggregated data below and provide a comprehensive summary.

    **Aggregated Analysis Data:**
    {sentiment_json}

    **Summary Requirements:**
    1. Provide an overall sentiment overview.
    2. Identify the top 3 positive and top 3 negative themes.
    3. For each theme, explain the key insight and provide one example (anonymized).
    4. Conclude with 2-3 actionable recommendations for the HR team.

    Format the response as a professional executive summary suitable for leadership presentation.
    """
    try:
        response = client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are an HR strategic advisor providing clear, actionable insights."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"Error generating summary: {str(e)}"

def main():
    """Main execution flow."""
    parser = argparse.ArgumentParser(description='AI-powered employee engagement survey analyzer.')
    parser.add_argument('--survey-data', required=True, help='Path to the survey CSV file.')
    parser.add_argument('--comment-column', required=True, help='Name of the column containing survey comments.')
    parser.add_argument('--output', default='outputs/sample_engagement_report.json', help='Output file path for the results.')
    args = parser.parse_args()

    print("--- AI Employee Engagement Analyzer Initializing ---\n")

    # Load survey data
    try:
        df = pd.read_csv(args.survey_data)
        print(f"✓ Survey data loaded from: {args.survey_data}")
        print(f"✓ Found {len(df)} survey responses.\n")
    except Exception as e:
        print(f"✗ Error: Could not read survey file. {e}")
        return

    # Check for comment column
    if args.comment_column not in df.columns:
        print(f"✗ Error: Column '{args.comment_column}' not found in survey data.")
        print(f"Available columns: {', '.join(df.columns)}")
        return

    # Analyze each comment
    analyzed_comments = []
    for idx, row in df.iterrows():
        comment = row[args.comment_column]
        if pd.isna(comment) or comment.strip() == "":
            continue

        print(f"Processing response {idx + 1}: {comment[:50]}...")
        analysis = analyze_comment(comment)
        analysis['original_comment'] = comment
        analyzed_comments.append(analysis)

    # Generate executive summary
    print(f"\n✓ Analyzed {len(analyzed_comments)} comments.")
    print("Generating executive summary...")
    executive_summary = generate_executive_summary(analyzed_comments)

    # Prepare final output
    final_report = {
        "survey_file": args.survey_data,
        "analysis_date": datetime.now().isoformat(),
        "total_responses_analyzed": len(analyzed_comments),
        "executive_summary": executive_summary,
        "detailed_comments": analyzed_comments
    }

    # Save report
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(final_report, f, indent=2)

    print(f"\n--- Analysis Complete ---")
    print(f"✓ Report saved to: {args.output}")

if __name__ == "__main__":
    main()
