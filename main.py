#!/usr/bin/env python3
"""
WhatsApp Chat Analyzer
Thiago Alvarez & Daniela Anderez

Main entry point for the chat analysis pipeline.
"""

import os
import sys
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from whatsapp_analyzer import (
    WhatsAppParser,
    ChatAnalyzer,
    ChatVisualizer,
    SentimentAnalyzer,
    TopicAnalyzer,
    ConflictDetector,
    format_duration
)


def generate_report(df, analyzer, sentiment_analyzer, topic_analyzer, conflict_detector, output_path):
    """Generate the markdown analysis report with 12-section format."""

    # Gather all data
    basic_stats = analyzer.get_basic_stats()
    period_stats = analyzer.get_messages_by_period()
    length_stats = analyzer.get_message_length_stats()
    response_stats = analyzer.get_response_time_stats()
    initiations = analyzer.get_conversation_initiations()
    streak_stats = analyzer.get_streak_stats()
    call_stats = analyzer.get_call_stats()
    media_stats = analyzer.get_media_stats()
    word_freq = analyzer.get_word_frequency(top_n=30)
    emoji_freq = analyzer.get_emoji_frequency(top_n=20)
    terms = analyzer.get_terms_of_endearment()
    te_amo = analyzer.get_te_amo_by_year()
    busiest = analyzer.get_busiest_day()
    longest_msg = analyzer.get_longest_message()
    yearly = analyzer.get_yearly_summary()
    sentiment_by_sender = sentiment_analyzer.get_sentiment_by_sender(df)

    # Topic analysis data
    topic_distribution = topic_analyzer.get_overall_topic_distribution(df)
    topics_by_sender = topic_analyzer.get_topics_by_sender(df)
    topic_evolution = topic_analyzer.get_topic_evolution_yearly(df)
    topic_initiators = topic_analyzer.get_topic_initiators(df)
    conversation_metrics = topic_analyzer.get_conversation_metrics(df)

    # Cross-analysis data
    sentiment_by_topic = analyzer.get_sentiment_by_topic()
    response_time_by_topic = analyzer.get_response_time_by_topic()
    topic_balance = analyzer.get_topic_balance()
    health_score = analyzer.get_communication_health_score()

    # Stress/conflict analysis data
    stress_causes = conflict_detector.get_stress_causes(df)
    stress_by_sender = conflict_detector.get_stress_by_sender(df)

    # Calculate total call time
    total_call_seconds = (
        call_stats['voice']['total_duration_seconds'] +
        call_stats['video']['total_duration_seconds']
    )

    # Get participants
    participants = list(basic_stats['messages_per_participant'].keys())

    # ========================================================================
    # PART 1: OVERVIEW & SUMMARY
    # ========================================================================

    report = f"""# WhatsApp Chat Analysis Report
## Thiago Alvarez & Daniela Anderez

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---

# Part 1: Overview & Summary

## 1. Executive Summary

| Metric | Value |
|--------|-------|
| **Total Messages** | {basic_stats['total_messages']:,} |
| **Date Range** | {basic_stats['date_range']['start'].strftime('%B %d, %Y')} - {basic_stats['date_range']['end'].strftime('%B %d, %Y')} |
| **Duration** | {basic_stats['date_range']['days']:,} days (~{basic_stats['date_range']['days']/365:.1f} years) |
| **Messages from Thiago** | {basic_stats['messages_per_participant'].get('Thiago Alvarez', 0):,} |
| **Messages from Daniela** | {basic_stats['messages_per_participant'].get('Daniela Anderez', 0):,} |

### Key Highlights
- **Longest messaging streak:** {streak_stats['longest']} consecutive days
- **Total calls made:** {call_stats['voice']['total'] + call_stats['video']['total']:,}
- **Total call time:** {format_duration(int(total_call_seconds))}
- **"Te amo" said:** {sum(te_amo.values()):,} times
- **Photos shared:** {media_stats['by_type'].get('image', 0):,}
- **Communication Health Score:** {health_score['overall_score']}/10

### 7-Year Journey Snapshot
"""

    # Add yearly summary
    for year in sorted(yearly.keys()):
        y = yearly[year]
        report += f"- **{year}:** {y['total_messages']:,} messages, {y['active_days']} active days\n"

    # ========================================================================
    # PART 2: COMMUNICATION PATTERNS
    # ========================================================================

    report += f"""

---

# Part 2: Communication Patterns

## 2. Volume & Activity

### Messages by Year

| Year | Total | Thiago | Daniela | Active Days |
|------|-------|--------|---------|-------------|
"""

    for year in sorted(yearly.keys()):
        y = yearly[year]
        thiago = y['by_sender'].get('Thiago Alvarez', 0)
        daniela = y['by_sender'].get('Daniela Anderez', 0)
        report += f"| {year} | {y['total_messages']:,} | {thiago:,} | {daniela:,} | {y['active_days']} |\n"

    report += f"""
### Message Types

| Type | Count | Percentage |
|------|-------|------------|
"""
    total_msgs = basic_stats['total_messages']
    for msg_type, count in sorted(basic_stats['message_types'].items(), key=lambda x: -x[1]):
        pct = (count / total_msgs * 100) if total_msgs > 0 else 0
        report += f"| {msg_type.title()} | {count:,} | {pct:.1f}% |\n"

    report += f"""
### Busiest Day Ever
- **Date:** {busiest['date']}
- **Messages:** {busiest['count']:,}

---

## 3. Conversation Dynamics

### Who Initiates Conversations
(After {initiations['gap_hours']} hours of silence)

| Person | Initiations | Percentage |
|--------|-------------|------------|
"""
    total_init = initiations['total']
    for sender, count in initiations['by_sender'].items():
        pct = (count / total_init * 100) if total_init > 0 else 0
        report += f"| {sender} | {count:,} | {pct:.1f}% |\n"

    report += f"""
### Response Times

| Person | Average | Median |
|--------|---------|--------|
"""
    for sender, stats in response_stats['by_sender'].items():
        avg_min = stats['mean'] / 60
        med_min = stats['median'] / 60
        report += f"| {sender} | {avg_min:.1f} min | {med_min:.1f} min |\n"

    report += f"""
### Messaging Streak
- **Longest streak:** {streak_stats['longest']} days
- **From:** {streak_stats['longest_start']} to {streak_stats['longest_end']}
- **Current streak:** {streak_stats['current']} days

---

## 4. Communication Styles

### Message Length

| Person | Avg Length | Max Length | Total Characters |
|--------|------------|------------|------------------|
"""
    for sender, stats in length_stats['by_sender'].items():
        report += f"| {sender.split()[0]} | {stats['mean']:.0f} chars | {stats['max']:,} | {stats['total_chars']:,} |\n"

    report += """
### Top 10 Emojis

| Rank | Emoji | Count |
|------|-------|-------|
"""
    for i, (emoji, count) in enumerate(emoji_freq['overall'][:10], 1):
        report += f"| {i} | {emoji} | {count:,} |\n"

    # ========================================================================
    # PART 3: TOPIC ANALYSIS (NEW - Conversation-Aware)
    # ========================================================================

    report += """

---

# Part 3: Topic Analysis (Conversation-Aware)

## 5. What You Talk About

### Overall Topic Distribution

| Topic | Percentage | Messages |
|-------|------------|----------|
"""

    # Add topic distribution with message counts
    sorted_topics = sorted(topic_distribution.items(), key=lambda x: x[1], reverse=True)
    text_count = len(df[df['type'] == 'text'])
    for topic, pct in sorted_topics:
        msg_count = int(text_count * pct / 100)
        report += f"| {topic.title()} | {pct:.1f}% | ~{msg_count:,} |\n"

    report += """
### Topics by Sender

"""
    for sender, topics in topics_by_sender.items():
        report += f"**{sender.split()[0]}:**\n"
        sorted_sender_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:6]
        for topic, pct in sorted_sender_topics:
            report += f"- {topic.title()}: {pct:.1f}%\n"
        report += "\n"

    # Conversation metrics
    report += """### Conversation Metrics by Topic

| Topic | Conversations | Avg Messages | Avg Duration |
|-------|---------------|--------------|--------------|
"""
    if conversation_metrics:
        sorted_metrics = sorted(conversation_metrics.items(),
                                key=lambda x: x[1]['conversation_count'], reverse=True)
        for topic, metrics in sorted_metrics:
            report += f"| {topic.title()} | {metrics['conversation_count']:,} | {metrics['avg_message_count']:.1f} | {metrics['avg_duration_minutes']:.0f} min |\n"

    report += """

---

## 6. Topic Evolution

### How Topics Changed Over 7 Years

"""
    if len(topic_evolution) > 0:
        # Show key evolution insights
        first_year = topic_evolution.iloc[0]['year']
        last_year = topic_evolution.iloc[-1]['year']

        report += f"**{first_year} vs {last_year}:**\n\n"

        for topic in ['relacionamento', 'trabalho', 'casa', 'viagem', 'lazer']:
            if f'{topic}_pct' in topic_evolution.columns:
                first_pct = topic_evolution.iloc[0][f'{topic}_pct']
                last_pct = topic_evolution.iloc[-1][f'{topic}_pct']
                change = last_pct - first_pct
                arrow = "↑" if change > 0 else "↓" if change < 0 else "→"
                report += f"- **{topic.title()}:** {first_pct:.1f}% → {last_pct:.1f}% ({arrow} {abs(change):.1f}%)\n"

    report += """

---

## 7. Topic Dynamics

### Who Initiates Which Topics

| Topic | Thiago | Daniela | Balance |
|-------|--------|---------|---------|
"""
    if topic_initiators:
        for topic in ['relacionamento', 'trabalho', 'casa', 'viagem', 'saude', 'financas', 'lazer', 'filhos']:
            if topic in topic_initiators and topic_initiators[topic]['total_initiations'] > 10:
                data = topic_initiators[topic]
                thiago_pct = data['percentages'].get('Thiago Alvarez', 0)
                daniela_pct = data['percentages'].get('Daniela Anderez', 0)
                balance = "Balanced" if abs(thiago_pct - 50) < 10 else ("Thiago" if thiago_pct > 50 else "Daniela")
                report += f"| {topic.title()} | {thiago_pct:.0f}% | {daniela_pct:.0f}% | {balance} |\n"

    report += """
### Topic Balance Score

| Topic | Thiago % | Daniela % | Balance Score |
|-------|----------|-----------|---------------|
"""
    if topic_balance:
        sorted_balance = sorted(topic_balance.items(),
                                key=lambda x: x[1]['total_messages'], reverse=True)[:8]
        for topic, data in sorted_balance:
            thiago_pct = data['by_sender'].get('Thiago Alvarez', {}).get('percentage', 0)
            daniela_pct = data['by_sender'].get('Daniela Anderez', {}).get('percentage', 0)
            balance = 100 - data['balance_score'] * 2  # Convert to 0-100 where 100 is perfect
            report += f"| {topic.title()} | {thiago_pct:.0f}% | {daniela_pct:.0f}% | {balance:.0f}/100 |\n"

    # ========================================================================
    # PART 4: EMOTIONAL ANALYSIS
    # ========================================================================

    report += """

---

# Part 4: Emotional Analysis

## 8. Sentiment by Topic

### Which Topics Make You Happy vs Stressed

| Topic | Avg Sentiment | Positive | Negative | Vibe |
|-------|---------------|----------|----------|------|
"""
    if sentiment_by_topic:
        sorted_sentiment = sorted(sentiment_by_topic.items(),
                                  key=lambda x: x[1]['avg_sentiment'], reverse=True)
        for topic, data in sorted_sentiment:
            vibe = "😊" if data['avg_sentiment'] > 0.15 else "😐" if data['avg_sentiment'] > -0.05 else "😟"
            report += f"| {topic.title()} | {data['avg_sentiment']:.3f} | {data['positive_count']:,} | {data['negative_count']:,} | {vibe} |\n"

    report += """
### Response Time by Topic

| Topic | Avg Response | Interpretation |
|-------|--------------|----------------|
"""
    if response_time_by_topic:
        sorted_rt = sorted(response_time_by_topic.items(),
                           key=lambda x: x[1]['avg_response_seconds'])
        for topic, data in sorted_rt[:8]:
            avg_min = data['avg_response_seconds'] / 60
            interp = "Very engaged" if avg_min < 3 else "Quick" if avg_min < 7 else "Normal" if avg_min < 15 else "Slower"
            report += f"| {topic.title()} | {avg_min:.1f} min | {interp} |\n"

    report += """

---

## 9. Stress & Conflict

### Overview
"""
    total_stressful = stress_causes.get('total_stressful', 0)
    stressful_pct = (total_stressful / text_count * 100) if text_count > 0 else 0

    report += f"""
- **Total stressful messages:** {total_stressful:,} ({stressful_pct:.1f}% of all text messages)

### Stress Causes by Topic

| Topic | % of Stressful Conversations |
|-------|------------------------------|
"""
    if stress_causes['topic_breakdown']:
        sorted_causes = sorted(stress_causes['topic_breakdown'].items(), key=lambda x: x[1], reverse=True)
        for topic, pct in sorted_causes:
            report += f"| {topic.title()} | {pct:.1f}% |\n"

    report += """
### Stress by Person

| Person | Avg Conflict Score | Stressful Messages |
|--------|-------------------|-------------------|
"""
    for sender, stats in stress_by_sender.items():
        report += f"| {sender.split()[0]} | {stats['avg_conflict_score']:.3f} | {stats['stressful_messages']:,} ({stats['stressful_percentage']:.1f}%) |\n"

    report += """

---

## 10. Affection & Connection

### "Te Amo" Over the Years

| Year | Count | Per Day |
|------|-------|---------|
"""
    for year, count in sorted(te_amo.items()):
        year_days = yearly.get(year, {}).get('active_days', 365)
        per_day = count / year_days if year_days > 0 else 0
        report += f"| {year} | {count} | {per_day:.2f} |\n"

    report += f"""
### Terms of Endearment

| Term | Count | Who Uses More |
|------|-------|---------------|
"""
    sorted_terms = sorted(terms['overall'].items(), key=lambda x: -x[1])[:12]
    for term, count in sorted_terms:
        thiago_count = terms['by_sender'].get('Thiago Alvarez', {}).get(term, 0)
        daniela_count = terms['by_sender'].get('Daniela Anderez', {}).get(term, 0)
        who = "Thiago" if thiago_count > daniela_count else "Daniela" if daniela_count > thiago_count else "Equal"
        report += f"| {term} | {count:,} | {who} |\n"

    # ========================================================================
    # PART 5: INSIGHTS & FUN FACTS
    # ========================================================================

    report += """

---

# Part 5: Insights & Fun Facts

## 11. Relationship Insights

### Communication Health Scorecard

"""
    report += f"**Overall Score: {health_score['overall_score']}/10**\n\n"
    report += "| Component | Score | Weight |\n"
    report += "|-----------|-------|--------|\n"

    component_names = {
        'response_symmetry': 'Response Symmetry',
        'topic_diversity': 'Topic Diversity',
        'sentiment_trend': 'Sentiment Trend',
        'affection_frequency': 'Affection Frequency',
        'frequency_trend': 'Conversation Trend',
    }
    for comp, score in health_score['components'].items():
        weight = health_score['weights'].get(comp, 0) * 100
        report += f"| {component_names.get(comp, comp)} | {score}/10 | {weight:.0f}% |\n"

    report += """
### Key Insights

"""
    # Generate dynamic insights
    if health_score['components']['response_symmetry'] > 8:
        report += "- **Response Symmetry:** You both respond equally - great communication balance!\n"
    if health_score['components']['topic_diversity'] > 7:
        report += "- **Topic Diversity:** Wide range of conversation topics - your relationship covers many aspects of life.\n"
    if health_score['components']['affection_frequency'] > 7:
        report += "- **Affection:** High frequency of loving expressions - emotional connection is strong.\n"

    # Find dominant topic initiator
    if topic_initiators:
        travel_init = topic_initiators.get('viagem', {})
        if travel_init.get('total_initiations', 0) > 50:
            thiago_travel = travel_init.get('percentages', {}).get('Thiago Alvarez', 50)
            if thiago_travel > 60:
                report += "- **Travel Planning:** Thiago tends to initiate travel conversations more often.\n"
            elif thiago_travel < 40:
                report += "- **Travel Planning:** Daniela tends to initiate travel conversations more often.\n"

    report += f"""

---

## 12. Fun Facts & Milestones

### Records & Achievements

- **Longest message ever:** {longest_msg['length']:,} characters by {longest_msg['sender'].split()[0]} on {longest_msg['date'].strftime('%B %d, %Y')}
- **Total "amor" mentions:** {terms['overall'].get('amor', 0):,}
- **Total years together:** {basic_stats['date_range']['days']/365:.1f} years
- **Average messages per day:** {basic_stats['total_messages'] / basic_stats['date_range']['days']:.1f}
- **Total characters typed:** {length_stats['by_sender'].get('Thiago Alvarez', {}).get('total_chars', 0) + length_stats['by_sender'].get('Daniela Anderez', {}).get('total_chars', 0):,}

### Call Statistics

| Type | Total | Completed | Missed | Total Duration |
|------|-------|-----------|--------|----------------|
| Voice | {call_stats['voice']['total']:,} | {call_stats['voice']['completed']:,} | {call_stats['voice']['missed']:,} | {format_duration(int(call_stats['voice']['total_duration_seconds']))} |
| Video | {call_stats['video']['total']:,} | {call_stats['video']['completed']:,} | {call_stats['video']['missed']:,} | {format_duration(int(call_stats['video']['total_duration_seconds']))} |

### Media Shared

| Type | Count |
|------|-------|
"""
    for media_type, count in sorted(media_stats['by_type'].items(), key=lambda x: -x[1]):
        report += f"| {media_type.title()} | {count:,} |\n"

    report += """

---

## Visualizations

All 35 visualizations have been saved to the `output/visualizations/` directory:

### Communication Patterns (1-6)
1. Messages per month (line chart)
2. Messages by year per person (stacked bar)
3. Activity heatmap (hour x day)
4. Message frequency per person (dual line)
5. Messages by day of week (bar)
6. Messages by hour (bar)

### Communication Styles (7-16)
7. Message length distribution (box plot)
8. Message length evolution (line)
9. Word cloud (combined)
10. Word cloud (Thiago)
11. Word cloud (Daniela)
12. Top 20 words (bar)
13. Top 15 emojis (bar)
14. Media type distribution (pie)
15. Media sharing trends (line)
16. Terms of endearment (bar)

### Sentiment & Time (17-23)
17. Sentiment over time (line)
18. Call duration trends (area)
19. Calendar heatmap (GitHub style)
20. Response time comparison (bar)
21. Messaging streak history (line)
22. Conversation initiations (pie)
23. "Te amo" by year (bar)

### Topic Analysis (24-29)
24. Topic distribution over time (stacked area)
25. Topics by sender (horizontal bar)
26. Overall topic distribution (pie)
27. Stress/conflict timeline (line)
28. Stress causes by topic (bar)
29. Stress by topic × day of week (heatmap)

### NEW: Conversation-Aware Analysis (30-35)
30. Sentiment by topic (grouped bar)
31. Topic initiators (horizontal stacked bar)
32. Topic evolution over years (multi-line)
33. Communication health scorecard (radar)
34. Conversation count by topic (bar)
35. Response time by topic (grouped bar)

---

*Report generated with WhatsApp Chat Analyzer - Conversation-Aware Edition*
"""

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"Report saved to: {output_path}")


def main():
    """Main entry point."""
    print("=" * 60)
    print("WhatsApp Chat Analyzer")
    print("Thiago Alvarez & Daniela Anderez")
    print("=" * 60)
    print()

    # Configuration
    chat_file = "/Users/thiagoalvarez/Claude_Code/Chat/_chat.txt"
    output_dir = "/Users/thiagoalvarez/Claude_Code/Chat/output"
    viz_dir = os.path.join(output_dir, "visualizations")

    # Ensure output directories exist
    os.makedirs(viz_dir, exist_ok=True)

    # Step 1: Parse the chat
    print("\n[1/7] Parsing WhatsApp chat...")
    parser = WhatsAppParser(chat_file)
    df = parser.parse()

    print(f"\nParticipants: {parser.get_participants()}")
    print(f"Date range: {parser.get_date_range()}")

    # Step 2: Run sentiment analysis
    print("\n[2/7] Running sentiment analysis...")
    sentiment_analyzer = SentimentAnalyzer()
    df = sentiment_analyzer.analyze_dataframe(df)

    # Step 3: Run topic analysis
    print("\n[3/7] Running topic analysis...")
    topic_analyzer = TopicAnalyzer()
    df = topic_analyzer.analyze_dataframe(df)

    # Step 4: Run conflict/stress detection
    print("\n[4/7] Running stress/conflict detection...")
    conflict_detector = ConflictDetector()
    df = conflict_detector.analyze_dataframe(df)

    # Step 5: Create analyzer
    print("\n[5/7] Analyzing statistics...")
    analyzer = ChatAnalyzer(df)

    # Print basic stats
    stats = analyzer.get_basic_stats()
    print(f"\nTotal messages: {stats['total_messages']:,}")
    for sender, count in stats['messages_per_participant'].items():
        print(f"  - {sender}: {count:,}")

    # Step 6: Generate visualizations
    print("\n[6/7] Generating visualizations...")
    visualizer = ChatVisualizer(df, viz_dir)
    viz_paths = visualizer.generate_all(analyzer, sentiment_analyzer, topic_analyzer, conflict_detector)
    print(f"\nGenerated {len(viz_paths)} visualizations")

    # Step 7: Generate report
    print("\n[7/7] Generating report...")
    report_path = os.path.join(output_dir, "report.md")
    generate_report(df, analyzer, sentiment_analyzer, topic_analyzer, conflict_detector, report_path)

    print("\n" + "=" * 60)
    print("Analysis complete!")
    print("=" * 60)
    print(f"\nOutput files:")
    print(f"  - Report: {report_path}")
    print(f"  - Visualizations: {viz_dir}/")
    print(f"\nTotal visualizations: {len(viz_paths)}")


if __name__ == "__main__":
    main()
