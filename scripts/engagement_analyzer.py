"""
AI Employee Engagement Survey Analyzer
Usage: python engagement_analyzer.py --survey-data survey.csv --comment-column "Feedback"
Requirements: pip install google-generativeai pandas python-dotenv
"""

import os, json, argparse, pandas as pd
from datetime import datetime
from collections import Counter
import google.generativeai as genai

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
if not GEMINI_API_KEY:
    try:
        from dotenv import load_dotenv
        load_dotenv()
        GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    except:
        pass

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

THEMES = ["Leadership", "Compensation", "Career Growth", "Work-Life Balance", 
          "Culture", "Tools", "Communication"]

def analyze_comment(comment):
    prompt = f"""Analyze this employee feedback. Return JSON with:
- sentiment: Positive/Negative/Neutral
- theme: one of [{", ".join(THEMES)}]
- summary: brief summary

Comment: {comment}"""
    
    try:
        response = model.generate_content(prompt)
        text = response.text
        start = text.find('{')
        end = text.rfind('}') + 1
        if start >= 0 and end > start:
            return json.loads(text[start:end])
        return json.loads(text)
    except Exception as e:
        return {"sentiment": "Neutral", "theme": "Unknown", "summary": f"Error: {e}"}

def generate_executive_summary(results):
    sentiment_counts = Counter([r["sentiment"] for r in results])
    theme_breakdown = Counter([r["theme"] for r in results])
    
    return f"""EMPLOYEE ENGAGEMENT ANALYSIS
Generated: {datetime.now().strftime("%Y-%m-%d %H:%M")}

SENTIMENT:
- Positive: {sentiment_counts.get("Positive", 0)} ({sentiment_counts.get("Positive", 0)/len(results)*100:.1f}%)
- Negative: {sentiment_counts.get("Negative", 0)} ({sentiment_counts.get("Negative", 0)/len(results)*100:.1f}%)
- Neutral: {sentiment_counts.get("Neutral", 0)} ({sentiment_counts.get("Neutral", 0)/len(results)*100:.1f}%)

TOP THEMES:
{chr(10).join([f"- {theme}: {count} mentions" for theme, count in theme_breakdown.most_common(5)])}"""

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--survey-data', required=True)
    parser.add_argument('--comment-column', required=True)
    parser.add_argument('--output', default='outputs/engagement_report.json')
    args = parser.parse_args()
    
    print("Loading survey data...")
    df = pd.read_csv(args.survey_data)
    comments = df[args.comment_column].dropna().tolist()
    print(f"Found {len(comments)} comments\n")
    
    results = []
    for i, comment in enumerate(comments[:100], 1):
        print(f"[{i}/100] Analyzing...")
        result = analyze_comment(comment)
        result["comment_id"] = i
        results.append(result)
    
    summary = generate_executive_summary(results)
    final_report = {
        "survey_file": args.survey_data,
        "analysis_date": datetime.now().isoformat(),
        "total_comments": len(results),
        "executive_summary": summary,
        "detailed_results": results
    }
    
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(final_report, f, indent=2)
    print(f"\n✓ Report saved to: {args.output}")
    print(f"\n{summary}")

if __name__ == "__main__":
    main()
