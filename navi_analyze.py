#!/usr/bin/env python3
"""
NAVI WhatsApp Chat Analyzer

Generates JSON outputs following the ANALYZER_OUTPUT_SPEC.md specification:
1. Categorized Messages for UI
2. Scoring System (health metrics)
3. AI Agent Contexts
"""

import os
import sys
import json
import argparse
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from whatsapp_analyzer import (
    WhatsAppParser,
    SentimentAnalyzer,
    TopicAnalyzer,
    NAVIOutputGenerator,
    NAVIReportGenerator,
)


def main():
    parser = argparse.ArgumentParser(
        description='NAVI WhatsApp Chat Analyzer - Generate JSON outputs for NAVI UI'
    )
    parser.add_argument(
        '--chat', '-c',
        default='_chat.txt',
        help='Path to WhatsApp chat export file (default: _chat.txt)'
    )
    parser.add_argument(
        '--output', '-o',
        default='output/navi',
        help='Output directory for JSON files (default: output/navi)'
    )
    parser.add_argument(
        '--days', '-d',
        type=int,
        default=30,
        help='Days of history for message groups (default: 30)'
    )
    parser.add_argument(
        '--thiago-name',
        default='Thiago Alvarez',
        help='Full name for Thiago (default: Thiago Alvarez)'
    )
    parser.add_argument(
        '--daniela-name',
        default='Daniela Anderez',
        help='Full name for Daniela (default: Daniela Anderez)'
    )
    parser.add_argument(
        '--all-history',
        action='store_true',
        help='Include all message history (not just recent days)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--no-reports',
        action='store_true',
        help='Skip generating markdown reports'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("NAVI WhatsApp Chat Analyzer")
    print("=" * 60)
    print()

    # Resolve paths
    chat_file = os.path.abspath(args.chat)
    output_dir = os.path.abspath(args.output)

    if not os.path.exists(chat_file):
        print(f"Error: Chat file not found: {chat_file}")
        sys.exit(1)

    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Step 1: Parse the chat
    print("[1/5] Parsing WhatsApp chat...")
    parser_obj = WhatsAppParser(chat_file)
    df = parser_obj.parse()

    if args.verbose:
        print(f"  - Total messages: {len(df):,}")
        print(f"  - Participants: {parser_obj.get_participants()}")
        start, end = parser_obj.get_date_range()
        print(f"  - Date range: {start} to {end}")

    # Step 2: Run sentiment analysis
    print("[2/5] Running sentiment analysis...")
    sentiment_analyzer = SentimentAnalyzer()
    df = sentiment_analyzer.analyze_dataframe(df)

    # Step 3: Run topic analysis
    print("[3/5] Running topic analysis...")
    topic_analyzer = TopicAnalyzer()
    df = topic_analyzer.analyze_dataframe(df)

    # Step 4: Generate NAVI outputs
    print("[4/5] Generating NAVI outputs...")
    navi_gen = NAVIOutputGenerator(
        df,
        thiago_name=args.thiago_name,
        daniela_name=args.daniela_name
    )

    recent_days = None if args.all_history else args.days
    paths = navi_gen.save_outputs(output_dir, recent_days=recent_days or 30)

    print()
    print("=" * 60)
    print("Analysis complete!")
    print("=" * 60)
    print()
    print("Generated files:")
    for name, path in paths.items():
        size = os.path.getsize(path)
        print(f"  - {name}: {size:,} bytes")

    print()
    print(f"Output directory: {output_dir}")

    # Print summary
    print()
    print("Quick Summary:")
    print("-" * 40)

    # Load and display health score
    with open(paths['health_score.json'], 'r') as f:
        scoring = json.load(f)

    health = scoring.get('healthScore', {})
    print(f"  Health Score: {health.get('overall', 'N/A')}/10 ({health.get('label', 'N/A')})")

    weekly = scoring.get('weeklyStats', {})
    print(f"  Messages (last 7 days): {weekly.get('messagesExchanged', 'N/A'):,}")
    print(f"  Connection moments: {weekly.get('connectionMoments', 'N/A')}")
    print(f"  Most active topic: {weekly.get('mostActiveTopic', 'N/A')}")

    # Load and display task count
    with open(paths['message_groups.json'], 'r') as f:
        messages = json.load(f)

    tasks = messages.get('tasks', [])
    pending = len([t for t in tasks if t.get('status') in ('pending', 'urgent')])
    print(f"  Pending tasks: {pending}")

    # Step 5: Generate markdown reports
    if not args.no_reports:
        print()
        print("[5/5] Generating markdown reports...")

        # Load all outputs for report generation
        with open(paths['all_outputs.json'], 'r') as f:
            all_outputs = json.load(f)

        report_gen = NAVIReportGenerator(all_outputs)
        report_dir = os.path.join(output_dir, 'reports')
        report_paths = report_gen.save_reports(report_dir)

        print()
        print("Generated reports:")
        for name, path in report_paths.items():
            size = os.path.getsize(path)
            print(f"  - {name}: {size:,} bytes")

        print()
        print(f"Reports directory: {report_dir}")


if __name__ == "__main__":
    main()
