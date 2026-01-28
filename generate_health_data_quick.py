#!/usr/bin/env python3
"""
Generate health analysis data with weekly pulse and LLM-validated examples.
"""

import sys
import os
import json
import re
from datetime import datetime, timedelta

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

sys.path.insert(0, '/Users/thiagoalvarez/Claude_Code/Chat')

import pandas as pd
from whatsapp_analyzer import (
    WhatsAppParser,
    ScientificHealthScorer,
    RelationshipPatternAnalyzer,
    LLMRelationshipAnalyzer,
)


# Categories that represent NEGATIVE patterns (problems to fix)
NEGATIVE_CATEGORIES = {'contempt', 'criticism', 'defensiveness', 'stonewalling'}

# Categories that represent POSITIVE patterns (good behaviors)
POSITIVE_CATEGORIES = {'affection', 'repair', 'vulnerability', 'appreciation', 'support', 'commitment'}


def is_forwarded_or_quote(message_text: str) -> bool:
    """
    Detect if a message is likely forwarded or quoting someone else.

    Patterns that indicate forwards/quotes:
    - Contains "‎image omitted" or "‎audio omitted" (WhatsApp forward markers)
    - Starts with a name followed by colon (quoting someone)
    - Contains timestamps like "[12/11/25, 6:46:24 PM]"
    - Contains "encaminhei", "reencaminhei" (forwarded)
    - Contains "ele disse", "ela disse", "falou que" (quoting third party)
    - Contains "meu filho", "minha filha", "meu pai", etc. with certain patterns
    - Starts with greeting patterns like "Fala [Name]" (likely forwarded message from friend)
    """
    if not message_text:
        return False

    text = message_text.lower()

    # WhatsApp forward/omitted markers
    if '‎image omitted' in text or '‎audio omitted' in text or '‎video omitted' in text:
        return True

    # Embedded timestamps (forwarded messages often contain these)
    if re.search(r'\[\d{1,2}/\d{1,2}/\d{2,4},?\s+\d{1,2}:\d{2}', message_text):
        return True

    # Starts with a greeting + name (likely forwarded from friend)
    greeting_patterns = [
        r'^fala\s+\w+',  # "Fala Thiago..."
        r'^oi\s+\w+[,!]',  # "Oi Thiago,"
        r'^olá\s+\w+',  # "Olá Thiago"
        r'^e\s+aí\s+\w+',  # "E aí Thiago"
    ]
    for pattern in greeting_patterns:
        if re.search(pattern, text):
            return True

    # Explicit forward indicators
    forward_patterns = [
        r'\bencaminhei\b',
        r'\breencaminhei\b',
        r'\bencaminhado\b',
        r'\bfwd:\b',
        r'\bforward\b',
    ]
    for pattern in forward_patterns:
        if re.search(pattern, text):
            return True

    # Quoting third parties
    quote_patterns = [
        r'\bele\s+(?:disse|falou|mandou|escreveu|fala)\b',
        r'\bela\s+(?:disse|falou|mandou|escreveu|fala)\b',
        r'\beles\s+(?:disseram|falaram|mandaram)\b',
        r'\bfalou\s+(?:que|assim|isso)\b',
        r'\bmandou\s+(?:isso|essa)\b',
        r'\bme\s+mandou\b',
        r'\breceb[ei]\s+(?:isso|essa)\b',
        r'\bfalei\s+com\s+(?:teu|seu|meu)\s+(?:filho|filha)\b',  # "Falei com teu filho"
    ]
    for pattern in quote_patterns:
        if re.search(pattern, text):
            return True

    # Talking about third parties (child, parent, friend)
    # Only filter if combined with pronouns that indicate it's about them, not to them
    third_party_about = [
        r'\b(?:meu filho|minha filha)\s+(?:disse|falou|fez|está|esteve)\b',
        r'\bsobre\s+(?:meu filho|minha filha|ele|ela)\b',
        r'\bdele\s+(?:pq|porque|que)\b',
        r'\bdela\s+(?:pq|porque|que)\b',
        r'\b(?:teu|seu)\s+filho\b',  # "teu filho"
        r'\bnão\s+sou\s+eu\s+(?:pq|porque|que)\b',  # "não sou eu porque..." (talking about someone else)
        r'\bele\s+(?:prefere|quer|gosta|precisa)\b',  # "ele prefere que..."
        r'\bdado\s+tudo\s+isso.*(?:ele|ela)\b',  # "Dado tudo isso, ele..."
    ]
    for pattern in third_party_about:
        if re.search(pattern, text):
            return True

    return False


def is_about_relationship(message_text: str, participants: list) -> bool:
    """
    Check if a message is about the relationship between participants.
    Returns True if it seems to be direct communication between the couple.
    """
    if not message_text:
        return False

    text = message_text.lower()

    # Direct address patterns (good indicators of direct communication)
    direct_patterns = [
        r'\bamor\b',
        r'\bvocê\b',
        r'\bte\s+(?:amo|adoro|quero)\b',
        r'\bnós\b',
        r'\ba\s+gente\b',
        r'\bnosso\b',
        r'\bnossa\b',
    ]

    for pattern in direct_patterns:
        if re.search(pattern, text):
            return True

    # If no direct patterns and message is short, likely direct
    if len(message_text) < 50:
        return True

    return True  # Default to including if not clearly about third party


def extract_examples_from_matches(matches, participants, max_per_category=5):
    """Extract example messages from pattern matches, organized by category with type labels."""
    examples = {
        'contempt': [],
        'criticism': [],
        'defensiveness': [],
        'stonewalling': [],
        'affection': [],
        'repair': [],
        'vulnerability': [],
        'appreciation': [],
        'support': [],
        'commitment': [],
    }

    for match in matches:
        # Skip if message looks like a forward or quote
        if is_forwarded_or_quote(match.message_text):
            continue

        # Map pattern names to categories
        category = None
        if match.horseman:
            category = match.horseman.lower()
        elif match.pattern_name:
            name = match.pattern_name.lower()
            if 'affection' in name or 'love' in name or 'carinho' in name:
                category = 'affection'
            elif 'repair' in name or 'sorry' in name or 'desculp' in name:
                category = 'repair'
            elif 'vulnerab' in name or 'fear' in name or 'medo' in name:
                category = 'vulnerability'
            elif 'appreciat' in name or 'thank' in name or 'obrigad' in name:
                category = 'appreciation'
            elif 'support' in name or 'apoio' in name:
                category = 'support'
            elif 'commit' in name or 'future' in name or 'futuro' in name:
                category = 'commitment'

        if category and category in examples and len(examples[category]) < max_per_category:
            if match.message_text and len(match.message_text) > 3:
                # Determine if this is a positive or negative pattern
                pattern_type = 'negative' if category in NEGATIVE_CATEGORIES else 'positive'

                examples[category].append({
                    'text': match.message_text[:200] + ('...' if len(match.message_text) > 200 else ''),
                    'sender': match.sender or 'Unknown',
                    'timestamp': match.timestamp.isoformat() if match.timestamp else None,
                    'evidence': match.evidence,
                    'type': pattern_type,
                })

    # Remove empty categories
    return {k: v for k, v in examples.items() if v}


def main(use_llm=True):
    print("Parsing WhatsApp chat...")
    parser = WhatsAppParser('/Users/thiagoalvarez/Claude_Code/Chat/_chat.txt')
    df = parser.parse()

    print(f"Parsed {len(df)} messages")
    print(f"Date range: {df['datetime'].min()} to {df['datetime'].max()}")

    participants = df['sender'].unique().tolist()
    print(f"Participants: {participants}")

    # Check if LLM is available for example validation (not for scoring - too slow)
    llm_analyzer = None
    if use_llm:
        try:
            if os.environ.get('ANTHROPIC_API_KEY'):
                print("\nLLM will be used for example validation (not scoring)...")
            else:
                print("\nNo ANTHROPIC_API_KEY found. Running without LLM validation.")
                use_llm = False
        except Exception as e:
            print(f"\nCould not check LLM availability: {e}")
            use_llm = False

    # Run scientific scoring WITHOUT LLM (fast, regex-only)
    # LLM is only used later to validate extracted examples
    print("Running scientific health scoring (regex-based)...")
    scorer = ScientificHealthScorer(
        df,
        sender_col='sender',
        message_col='message',
        datetime_col='datetime',
        llm_analyzer=None,  # Don't use LLM for scoring - too slow
        use_llm=False
    )

    result = scorer.to_dict()

    # Add metadata
    result['metadata'] = {
        'totalMessages': len(df),
        'dateRange': {
            'start': df['datetime'].min().isoformat(),
            'end': df['datetime'].max().isoformat(),
        },
        'participants': df['sender'].unique().tolist(),
        'generatedAt': datetime.now().isoformat(),
    }

    # Get pattern analysis (regex-only for speed)
    print("Running pattern analysis (regex-based)...")
    pattern_analyzer = RelationshipPatternAnalyzer(
        llm_analyzer=None,
        use_llm=False
    )

    # Calculate WEEKLY pulse (not daily)
    print("Calculating weekly pulse...")
    last_90_days = df[df['datetime'] >= (df['datetime'].max() - timedelta(days=90))].copy()

    # Group by week
    last_90_days['week'] = last_90_days['datetime'].dt.isocalendar().week
    last_90_days['year'] = last_90_days['datetime'].dt.isocalendar().year
    last_90_days['week_key'] = last_90_days['year'].astype(str) + '-W' + last_90_days['week'].astype(str).str.zfill(2)

    # Truly dismissive phrases that count as stonewalling
    truly_dismissive_stonewalling = ['tanto faz', 'como quiser', 'faz o que quiser', 'não me importa', 'dane-se', 'foda-se']

    # Use LLM for weekly positive pattern analysis
    weekly_llm_scores = {}
    if use_llm and os.environ.get('ANTHROPIC_API_KEY'):
        print("Analyzing weekly patterns with LLM...")
        import anthropic
        client = anthropic.Anthropic()

        # Get week keys and prepare data
        week_groups = list(last_90_days.groupby('week_key'))
        valid_weeks = [(k, df_week) for k, df_week in week_groups if len(df_week) >= 10]

        # Analyze last 12 weeks with LLM (batch into groups to reduce API calls)
        for week_key, week_df in valid_weeks[-12:]:
            # Sample messages from this week
            sample_size = min(30, len(week_df))
            sample_indices = [int(i * len(week_df) / sample_size) for i in range(sample_size)]
            sample_messages = week_df.iloc[sample_indices]

            messages_text = "\n".join([
                f"[{row['sender']}]: {row['message']}"
                for _, row in sample_messages.iterrows()
                if isinstance(row['message'], str) and len(row['message']) > 2
            ])

            prompt = f"""Analyze these WhatsApp messages from one week and count positive relationship patterns:

1. AFFECTION: Love expressions, caring, endearments ("te amo", "amor", "saudade", hearts)
2. SUPPORT: Emotional support, encouragement, being there for partner
3. APPRECIATION: Gratitude, thanks, acknowledging efforts
4. CONNECTION: Vulnerability, attunement, responsiveness to emotions

Messages:
{messages_text[:8000]}

Respond ONLY with JSON (no other text):
{{"positive_total": <number>, "affection": <number>, "support": <number>, "appreciation": <number>, "connection": <number>}}"""

            try:
                response = client.messages.create(
                    model="claude-sonnet-4-20250514",
                    max_tokens=200,
                    messages=[{"role": "user", "content": prompt}]
                )

                response_text = response.content[0].text
                import re as re_module
                json_match = re_module.search(r'\{[^}]+\}', response_text)
                if json_match:
                    llm_week = json.loads(json_match.group())
                    # Scale up from sample
                    scale = len(week_df) / sample_size
                    weekly_llm_scores[week_key] = {
                        'positive': int(llm_week.get('positive_total', 0) * scale),
                        'affection': int(llm_week.get('affection', 0) * scale),
                        'support': int(llm_week.get('support', 0) * scale),
                        'appreciation': int(llm_week.get('appreciation', 0) * scale),
                        'connection': int(llm_week.get('connection', 0) * scale),
                    }
            except Exception as e:
                print(f"  Week {week_key} LLM error: {e}")

        print(f"  LLM analyzed {len(weekly_llm_scores)} weeks")

    weekly_scores = []
    for week_key, week_df in last_90_days.groupby('week_key'):
        if len(week_df) < 10:
            continue

        week_summary = pattern_analyzer.analyze_conversation(
            week_df,
            sender_col='sender',
            message_col='message',
            datetime_col='datetime'
        )

        # Filter out false positives from the matches
        filtered_horsemen = {'criticism': 0, 'contempt': 0, 'defensiveness': 0, 'stonewalling': 0}
        filtered_negative = 0

        for match in week_summary.matches:
            # Skip forwarded/quoted messages
            if is_forwarded_or_quote(match.message_text):
                continue

            if match.horseman:
                horseman = match.horseman.lower()
                if horseman == 'stonewalling':
                    # Only count truly dismissive phrases as stonewalling
                    text_lower = match.message_text.lower().strip() if match.message_text else ''
                    if text_lower in truly_dismissive_stonewalling:
                        filtered_horsemen['stonewalling'] += 1
                        filtered_negative += 1
                elif horseman == 'contempt':
                    # Keep contempt only if not forwarded (already filtered above)
                    # Additional check: skip if it looks like quoting someone
                    text = match.message_text or ''
                    if not any(p in text.lower() for p in ['parabéns', 'grande coisa']):
                        filtered_horsemen['contempt'] += 1
                        filtered_negative += 1
                elif horseman in ['criticism', 'defensiveness']:
                    filtered_horsemen[horseman] += 1
                    filtered_negative += 1
            elif match.pattern_type == 'negative':
                filtered_negative += 1

        # Use LLM positive count if available, otherwise use regex
        if week_key in weekly_llm_scores:
            positive = weekly_llm_scores[week_key]['positive']
        else:
            positive = week_summary.total_positive

        # Use filtered negative count
        negative = filtered_negative
        ratio = positive / max(negative, 1)

        # Calculate score based on positive patterns (since negative is usually 0 now)
        # Use positive count per message as quality indicator
        positive_rate = positive / len(week_df) if len(week_df) > 0 else 0

        if positive_rate >= 0.15:  # 15%+ messages are positive
            score = 90 + min(positive_rate * 50, 10)
        elif positive_rate >= 0.10:
            score = 80 + (positive_rate - 0.10) * 200
        elif positive_rate >= 0.05:
            score = 65 + (positive_rate - 0.05) * 300
        elif positive_rate >= 0.02:
            score = 50 + (positive_rate - 0.02) * 500
        else:
            score = max(30, positive_rate * 2500)

        # Penalize for negative patterns (if any)
        score = max(20, score - (negative * 5))

        # Get week start date
        year, week = int(week_key.split('-W')[0]), int(week_key.split('-W')[1])
        try:
            week_start = datetime.strptime(f'{year}-W{week:02d}-1', '%Y-W%W-%w')
        except:
            # Fallback if strptime fails
            week_start = week_df['datetime'].min()

        weekly_scores.append({
            'weekKey': week_key,
            'weekStart': week_start.strftime('%Y-%m-%d'),
            'weekLabel': week_start.strftime('%d %b'),
            'score': round(min(100, score)),
            'messages': len(week_df),
            'positive': positive,
            'negative': negative,
            'ratio': round(ratio, 1),
            'positiveRate': round(positive_rate * 100, 1),
            'hasConflict': negative >= 3,
            'horsemen': filtered_horsemen,
            'llmAnalyzed': week_key in weekly_llm_scores,
        })

    result['weeklyPulse'] = weekly_scores[-12:]  # Last 12 weeks

    # Extract examples from 30-day window (same as scoring window)
    print("Extracting example messages from 30-day window...")
    last_30_days = df[df['datetime'] >= (df['datetime'].max() - timedelta(days=30))].copy()

    # Use LLM to analyze positive patterns (affection, commitment, appreciation)
    if use_llm and os.environ.get('ANTHROPIC_API_KEY'):
        print("Analyzing positive patterns with LLM...")
        import anthropic
        client = anthropic.Anthropic()

        # Sample messages for analysis (take ~100 messages spread across the period)
        sample_size = min(100, len(last_30_days))
        sample_indices = [int(i * len(last_30_days) / sample_size) for i in range(sample_size)]
        sample_messages = last_30_days.iloc[sample_indices]

        # Format messages for LLM
        messages_text = "\n".join([
            f"[{row['sender']}]: {row['message']}"
            for _, row in sample_messages.iterrows()
            if isinstance(row['message'], str) and len(row['message']) > 2
        ])

        prompt = f"""Analyze these WhatsApp messages between a couple and count the instances of:

1. AFFECTION: Expressions of love, caring, terms of endearment (e.g., "te amo", "amor", "saudade", "beijo", compliments, heart emojis, sweet messages)

2. COMMITMENT: References to shared future, planning together, "us/we" language, talking about their relationship positively (e.g., "juntos", "a gente vai", "nosso", planning trips/activities together)

3. APPRECIATION: Gratitude, thanks, acknowledging partner's efforts, positive feedback (e.g., "obrigado", "valeu", "que bom", recognizing help)

Messages to analyze:
{messages_text[:15000]}

Respond in JSON format:
{{
  "affection_count": <number>,
  "affection_examples": ["example1", "example2", "example3"],
  "commitment_count": <number>,
  "commitment_examples": ["example1", "example2", "example3"],
  "appreciation_count": <number>,
  "appreciation_examples": ["example1", "example2", "example3"],
  "analysis_notes": "brief observation about the couple's positive communication patterns"
}}"""

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            # Parse response
            response_text = response.content[0].text
            # Extract JSON from response
            import re as re_module
            json_match = re_module.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                # Clean up common JSON issues
                json_str = json_match.group()
                json_str = re_module.sub(r',\s*}', '}', json_str)
                json_str = re_module.sub(r',\s*]', ']', json_str)
                llm_positive = json.loads(json_str)

                # Calculate scores based on LLM counts
                # Scale up from sample to full 30 days
                scale_factor = len(last_30_days) / sample_size
                weeks = max((last_30_days['datetime'].max() - last_30_days['datetime'].min()).days / 7, 1)

                affection_count = int(llm_positive.get('affection_count', 0) * scale_factor)
                commitment_count = int(llm_positive.get('commitment_count', 0) * scale_factor)
                appreciation_count = int(llm_positive.get('appreciation_count', 0) * scale_factor)

                affection_per_week = affection_count / weeks
                commitment_per_week = commitment_count / weeks
                appreciation_per_week = appreciation_count / weeks

                print(f"  LLM detected: {affection_count} affection, {commitment_count} commitment, {appreciation_count} appreciation")

                # Update affectionCommitment dimension with LLM results
                if 'affectionCommitment' in result['healthScore']['dimensions']:
                    dim = result['healthScore']['dimensions']['affectionCommitment']

                    # Recalculate expressedAffection
                    if affection_per_week >= 15:
                        aff_score = 100
                    elif affection_per_week >= 7:
                        aff_score = 70 + (affection_per_week - 7) * 3.75
                    elif affection_per_week >= 3:
                        aff_score = 40 + (affection_per_week - 3) * 7.5
                    else:
                        aff_score = max(20, affection_per_week * 13)

                    dim['components']['expressedAffection'] = {
                        'score': round(aff_score, 1),
                        'perWeek': round(affection_per_week, 1),
                        'count': affection_count,
                        'insight': 'Expressões frequentes de afeto' if affection_per_week >= 10 else 'Afeto presente regularmente' if affection_per_week >= 5 else 'Mais expressões de afeto fortaleceriam a conexão',
                        'llmValidated': True,
                        'examples': llm_positive.get('affection_examples', [])[:3]
                    }

                    # Recalculate commitmentSignals
                    if commitment_per_week >= 8:
                        com_score = 100
                    elif commitment_per_week >= 4:
                        com_score = 70 + (commitment_per_week - 4) * 7.5
                    elif commitment_per_week >= 2:
                        com_score = 40 + (commitment_per_week - 2) * 15
                    else:
                        com_score = max(20, commitment_per_week * 20)

                    dim['components']['commitmentSignals'] = {
                        'score': round(com_score, 1),
                        'perWeek': round(commitment_per_week, 1),
                        'count': commitment_count,
                        'insight': 'Fortes sinais de compromisso' if commitment_per_week >= 5 else 'Compromisso demonstrado regularmente' if commitment_per_week >= 2 else 'Mais sinais de compromisso fortaleceriam a relação',
                        'llmValidated': True,
                        'examples': llm_positive.get('commitment_examples', [])[:3]
                    }

                    # Recalculate appreciation
                    if appreciation_per_week >= 10:
                        app_score = 100
                    elif appreciation_per_week >= 5:
                        app_score = 70 + (appreciation_per_week - 5) * 6
                    elif appreciation_per_week >= 2:
                        app_score = 40 + (appreciation_per_week - 2) * 10
                    else:
                        app_score = max(20, appreciation_per_week * 20)

                    dim['components']['appreciation'] = {
                        'score': round(app_score, 1),
                        'perWeek': round(appreciation_per_week, 1),
                        'count': appreciation_count,
                        'insight': 'Apreciação frequente e genuína' if appreciation_per_week >= 7 else 'Apreciação presente regularmente' if appreciation_per_week >= 3 else 'Mais apreciação constrói cultura positiva',
                        'llmValidated': True,
                        'examples': llm_positive.get('appreciation_examples', [])[:3]
                    }

                    # Recalculate dimension score
                    dim['score'] = round((aff_score + com_score + app_score) / 3, 1)
                    dim['llmAnalysisNotes'] = llm_positive.get('analysis_notes', '')

                    print(f"  Updated affectionCommitment score: {dim['score']}")

        except Exception as e:
            print(f"  LLM positive pattern analysis error: {e}")

    # LLM analysis for emotionalConnection dimension
    if use_llm and os.environ.get('ANTHROPIC_API_KEY'):
        print("Analyzing emotional connection patterns with LLM...")
        import anthropic
        client = anthropic.Anthropic()

        # Sample messages for analysis
        sample_size = min(100, len(last_30_days))
        sample_indices = [int(i * len(last_30_days) / sample_size) for i in range(sample_size)]
        sample_messages = last_30_days.iloc[sample_indices]

        messages_text = "\n".join([
            f"[{row['sender']}]: {row['message']}"
            for _, row in sample_messages.iterrows()
            if isinstance(row['message'], str) and len(row['message']) > 2
        ])

        prompt = f"""Analyze these WhatsApp messages between a couple and count instances of:

1. VULNERABILITY: Sharing fears, insecurities, emotional struggles, asking for emotional support, admitting mistakes/weaknesses (e.g., "estou com medo", "me sinto inseguro", "preciso de você", "estou triste", "não sei o que fazer")

2. ATTUNEMENT: Noticing and responding to partner's emotional state, checking in on feelings, showing they understand partner's emotions (e.g., "você parece triste", "sei que está difícil", "como você está se sentindo?", "percebi que...")

3. RESPONSIVENESS: Quick and engaged responses to emotional bids, following up on partner's concerns, showing active listening (e.g., responding thoughtfully to emotional messages, asking follow-up questions, validating feelings)

Messages to analyze:
{messages_text[:15000]}

Respond in JSON format:
{{
  "vulnerability_count": <number>,
  "vulnerability_examples": ["example1", "example2", "example3"],
  "attunement_count": <number>,
  "attunement_examples": ["example1", "example2", "example3"],
  "responsiveness_count": <number>,
  "responsiveness_examples": ["example1", "example2", "example3"],
  "analysis_notes": "brief observation about the couple's emotional connection patterns"
}}"""

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text
            import re as re_module
            json_match = re_module.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                # Clean up common JSON issues
                json_str = json_match.group()
                json_str = re_module.sub(r',\s*}', '}', json_str)  # Remove trailing commas
                json_str = re_module.sub(r',\s*]', ']', json_str)  # Remove trailing commas in arrays
                # Also handle unescaped quotes in strings
                try:
                    llm_emotional = json.loads(json_str)
                except json.JSONDecodeError:
                    # Try removing example arrays which often have parsing issues
                    json_str_simple = re_module.sub(r'"vulnerability_examples":\s*\[[^\]]*\]', '"vulnerability_examples": []', json_str)
                    json_str_simple = re_module.sub(r'"attunement_examples":\s*\[[^\]]*\]', '"attunement_examples": []', json_str_simple)
                    json_str_simple = re_module.sub(r'"responsiveness_examples":\s*\[[^\]]*\]', '"responsiveness_examples": []', json_str_simple)
                    llm_emotional = json.loads(json_str_simple)

                scale_factor = len(last_30_days) / sample_size
                weeks = max((last_30_days['datetime'].max() - last_30_days['datetime'].min()).days / 7, 1)

                vulnerability_count = int(llm_emotional.get('vulnerability_count', 0) * scale_factor)
                attunement_count = int(llm_emotional.get('attunement_count', 0) * scale_factor)
                responsiveness_count = int(llm_emotional.get('responsiveness_count', 0) * scale_factor)

                vulnerability_per_week = vulnerability_count / weeks
                attunement_per_week = attunement_count / weeks
                responsiveness_per_week = responsiveness_count / weeks

                print(f"  LLM detected: {vulnerability_count} vulnerability, {attunement_count} attunement, {responsiveness_count} responsiveness")

                if 'emotionalConnection' in result['healthScore']['dimensions']:
                    dim = result['healthScore']['dimensions']['emotionalConnection']

                    # Recalculate vulnerability score
                    if vulnerability_per_week >= 5:
                        vuln_score = 100
                    elif vulnerability_per_week >= 3:
                        vuln_score = 70 + (vulnerability_per_week - 3) * 15
                    elif vulnerability_per_week >= 1:
                        vuln_score = 40 + (vulnerability_per_week - 1) * 15
                    else:
                        vuln_score = max(20, vulnerability_per_week * 40)

                    dim['components']['vulnerability'] = {
                        'score': round(vuln_score, 1),
                        'perWeek': round(vulnerability_per_week, 1),
                        'count': vulnerability_count,
                        'insight': 'Alta abertura emocional' if vulnerability_per_week >= 4 else 'Vulnerabilidade presente' if vulnerability_per_week >= 2 else 'Mais abertura emocional fortaleceria a conexão',
                        'llmValidated': True,
                        'examples': llm_emotional.get('vulnerability_examples', [])[:3]
                    }

                    # Recalculate attunement score
                    if attunement_per_week >= 8:
                        att_score = 100
                    elif attunement_per_week >= 4:
                        att_score = 70 + (attunement_per_week - 4) * 7.5
                    elif attunement_per_week >= 2:
                        att_score = 40 + (attunement_per_week - 2) * 15
                    else:
                        att_score = max(20, attunement_per_week * 20)

                    dim['components']['attunement'] = {
                        'score': round(att_score, 1),
                        'perWeek': round(attunement_per_week, 1),
                        'count': attunement_count,
                        'insight': 'Alta sintonia emocional' if attunement_per_week >= 5 else 'Sintonização presente' if attunement_per_week >= 2 else 'Mais atenção às emoções do parceiro ajudaria',
                        'llmValidated': True,
                        'examples': llm_emotional.get('attunement_examples', [])[:3]
                    }

                    # Recalculate responsiveness score
                    if responsiveness_per_week >= 10:
                        resp_score = 100
                    elif responsiveness_per_week >= 5:
                        resp_score = 70 + (responsiveness_per_week - 5) * 6
                    elif responsiveness_per_week >= 2:
                        resp_score = 40 + (responsiveness_per_week - 2) * 10
                    else:
                        resp_score = max(20, responsiveness_per_week * 20)

                    dim['components']['responsiveness'] = {
                        'score': round(resp_score, 1),
                        'perWeek': round(responsiveness_per_week, 1),
                        'count': responsiveness_count,
                        'insight': 'Altamente responsivo' if responsiveness_per_week >= 7 else 'Boa responsividade' if responsiveness_per_week >= 3 else 'Mais engajamento nas respostas ajudaria',
                        'llmValidated': True,
                        'examples': llm_emotional.get('responsiveness_examples', [])[:3]
                    }

                    # Recalculate dimension score
                    dim['score'] = round((vuln_score + att_score + resp_score) / 3, 1)
                    dim['llmAnalysisNotes'] = llm_emotional.get('analysis_notes', '')

                    print(f"  Updated emotionalConnection score: {dim['score']}")

        except Exception as e:
            print(f"  LLM emotional connection analysis error: {e}")

    # LLM analysis for partnershipEquity dimension
    if use_llm and os.environ.get('ANTHROPIC_API_KEY'):
        print("Analyzing partnership equity patterns with LLM...")
        import anthropic
        client = anthropic.Anthropic()

        sample_size = min(100, len(last_30_days))
        sample_indices = [int(i * len(last_30_days) / sample_size) for i in range(sample_size)]
        sample_messages = last_30_days.iloc[sample_indices]

        messages_text = "\n".join([
            f"[{row['sender']}]: {row['message']}"
            for _, row in sample_messages.iterrows()
            if isinstance(row['message'], str) and len(row['message']) > 2
        ])

        prompt = f"""Analyze these WhatsApp messages between a couple and count instances of:

1. SHARED_DECISIONS: Joint decision-making, asking partner's opinion before deciding, "o que você acha?", "vamos decidir juntos", discussing options together

2. COORDINATION: Coordinating schedules, logistics, responsibilities, dividing tasks fairly, "eu faço X, você faz Y", planning together

3. EMOTIONAL_RECIPROCITY: Both partners initiating emotional conversations, both expressing care equally, balanced emotional give-and-take (note if one partner initiates more than the other)

4. CONTRIBUTION_BALANCE: References to sharing household/life responsibilities, acknowledging each other's contributions, fair division of labor

Messages to analyze:
{messages_text[:15000]}

Respond in JSON format:
{{
  "shared_decisions_count": <number>,
  "shared_decisions_examples": ["example1", "example2", "example3"],
  "coordination_count": <number>,
  "coordination_examples": ["example1", "example2", "example3"],
  "emotional_reciprocity_score": <0-100, where 100 means perfectly balanced>,
  "emotional_reciprocity_notes": "who initiates more and how balanced it is",
  "contribution_balance_count": <number>,
  "contribution_balance_examples": ["example1", "example2", "example3"],
  "analysis_notes": "brief observation about the couple's partnership dynamics"
}}"""

        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )

            response_text = response.content[0].text
            import re as re_module
            json_match = re_module.search(r'\{[\s\S]*\}', response_text)
            if json_match:
                # Clean up common JSON issues
                json_str = json_match.group()
                json_str = re_module.sub(r',\s*}', '}', json_str)
                json_str = re_module.sub(r',\s*]', ']', json_str)
                llm_equity = json.loads(json_str)

                scale_factor = len(last_30_days) / sample_size
                weeks = max((last_30_days['datetime'].max() - last_30_days['datetime'].min()).days / 7, 1)

                shared_decisions_count = int(llm_equity.get('shared_decisions_count', 0) * scale_factor)
                coordination_count = int(llm_equity.get('coordination_count', 0) * scale_factor)
                contribution_count = int(llm_equity.get('contribution_balance_count', 0) * scale_factor)
                emotional_reciprocity = llm_equity.get('emotional_reciprocity_score', 50)

                shared_per_week = shared_decisions_count / weeks
                coordination_per_week = coordination_count / weeks
                contribution_per_week = contribution_count / weeks

                print(f"  LLM detected: {shared_decisions_count} shared decisions, {coordination_count} coordination, reciprocity={emotional_reciprocity}")

                if 'partnershipEquity' in result['healthScore']['dimensions']:
                    dim = result['healthScore']['dimensions']['partnershipEquity']

                    # Recalculate contributionBalance score
                    if contribution_per_week >= 5:
                        contrib_score = 100
                    elif contribution_per_week >= 3:
                        contrib_score = 70 + (contribution_per_week - 3) * 15
                    elif contribution_per_week >= 1:
                        contrib_score = 40 + (contribution_per_week - 1) * 15
                    else:
                        contrib_score = max(20, contribution_per_week * 40)

                    dim['components']['contributionBalance'] = {
                        'score': round(contrib_score, 1),
                        'perWeek': round(contribution_per_week, 1),
                        'count': contribution_count,
                        'insight': 'Contribuições bem equilibradas' if contrib_score >= 70 else 'Balanço de contribuições razoável' if contrib_score >= 40 else 'Mais equilíbrio nas contribuições ajudaria',
                        'llmValidated': True,
                        'examples': llm_equity.get('contribution_balance_examples', [])[:3]
                    }

                    # Recalculate coordination score
                    if coordination_per_week >= 8:
                        coord_score = 100
                    elif coordination_per_week >= 4:
                        coord_score = 70 + (coordination_per_week - 4) * 7.5
                    elif coordination_per_week >= 2:
                        coord_score = 40 + (coordination_per_week - 2) * 15
                    else:
                        coord_score = max(20, coordination_per_week * 20)

                    dim['components']['coordination'] = {
                        'score': round(coord_score, 1),
                        'perWeek': round(coordination_per_week, 1),
                        'count': coordination_count,
                        'insight': 'Excelente coordenação' if coord_score >= 70 else 'Boa coordenação' if coord_score >= 40 else 'Mais coordenação fortaleceria a parceria',
                        'llmValidated': True,
                        'examples': llm_equity.get('coordination_examples', [])[:3]
                    }

                    # Emotional reciprocity comes directly from LLM assessment (0-100)
                    recip_score = min(100, max(20, emotional_reciprocity))

                    dim['components']['emotionalReciprocity'] = {
                        'score': round(recip_score, 1),
                        'insight': llm_equity.get('emotional_reciprocity_notes', 'Reciprocidade emocional analisada'),
                        'llmValidated': True,
                    }

                    # Shared decisions as additional component
                    if shared_per_week >= 5:
                        shared_score = 100
                    elif shared_per_week >= 3:
                        shared_score = 70 + (shared_per_week - 3) * 15
                    elif shared_per_week >= 1:
                        shared_score = 40 + (shared_per_week - 1) * 15
                    else:
                        shared_score = max(20, shared_per_week * 40)

                    dim['components']['sharedDecisions'] = {
                        'score': round(shared_score, 1),
                        'perWeek': round(shared_per_week, 1),
                        'count': shared_decisions_count,
                        'insight': 'Decisões tomadas em conjunto' if shared_score >= 70 else 'Algumas decisões conjuntas' if shared_score >= 40 else 'Mais decisões conjuntas fortaleceriam a parceria',
                        'llmValidated': True,
                        'examples': llm_equity.get('shared_decisions_examples', [])[:3]
                    }

                    # Recalculate dimension score
                    dim['score'] = round((contrib_score + coord_score + recip_score + shared_score) / 4, 1)
                    dim['llmAnalysisNotes'] = llm_equity.get('analysis_notes', '')

                    print(f"  Updated partnershipEquity score: {dim['score']}")

        except Exception as e:
            print(f"  LLM partnership equity analysis error: {e}")

    pattern_summary_30d = pattern_analyzer.analyze_conversation(
        last_30_days,
        sender_col='sender',
        message_col='message',
        datetime_col='datetime'
    )

    all_examples = extract_examples_from_matches(pattern_summary_30d.matches, participants)

    # Validate ALL negative matches with LLM (not just examples) to get accurate counts
    validated_examples = {}
    llm_validations = []
    validated_counts = {
        'contempt': 0,
        'criticism': 0,
        'defensiveness': 0,
        'stonewalling': 0,
    }

    # Initialize LLM analyzer now (only for validation)
    if use_llm and os.environ.get('ANTHROPIC_API_KEY'):
        print("Initializing LLM analyzer...")
        llm_analyzer = LLMRelationshipAnalyzer(
            model="claude-sonnet-4-20250514",
            analyze_all=False
        )

    if use_llm and llm_analyzer:
        # First, validate ALL negative pattern matches to get accurate counts
        print("Validating ALL negative pattern matches with LLM...")

        negative_matches = [m for m in pattern_summary_30d.matches
                          if m.horseman and m.horseman.lower() in NEGATIVE_CATEGORIES
                          and not is_forwarded_or_quote(m.message_text)]

        print(f"  Found {len(negative_matches)} negative matches to validate...")

        # Store validated examples directly
        validated_negative_examples = {cat: [] for cat in NEGATIVE_CATEGORIES}

        for match in negative_matches:
            category = match.horseman.lower()
            reasoning = None
            try:
                if category == 'contempt':
                    result_llm = llm_analyzer.detect_contempt(match.message_text, "")
                    is_valid = result_llm.is_contempt and result_llm.confidence >= 0.6
                    reasoning = result_llm.reasoning if is_valid else None
                elif category == 'stonewalling':
                    # Stonewalling is withdrawing from emotional communication
                    # "ok" alone is NOT stonewalling unless context shows partner needed emotional engagement
                    text_lower = match.message_text.lower().strip()

                    # Only these clearly dismissive phrases count as stonewalling
                    # "ok", "tá", "beleza" etc. are normal acknowledgments, NOT stonewalling
                    truly_dismissive = ['tanto faz', 'como quiser', 'faz o que quiser', 'não me importa', 'dane-se', 'foda-se']
                    is_valid = text_lower in truly_dismissive
                    reasoning = "Resposta evasiva e desinteressada" if is_valid else None
                elif category == 'criticism':
                    result_llm = llm_analyzer.detect_contempt(match.message_text, "")
                    # Criticism should not be contempt
                    is_valid = not result_llm.is_contempt
                    reasoning = "Crítica ao comportamento" if is_valid else None
                elif category == 'defensiveness':
                    result_llm = llm_analyzer.detect_contempt(match.message_text, "")
                    is_valid = not result_llm.is_contempt
                    reasoning = "Resposta defensiva" if is_valid else None
                else:
                    is_valid = False

                if is_valid:
                    validated_counts[category] += 1
                    # Store example (up to 5 per category)
                    if len(validated_negative_examples[category]) < 5:
                        validated_negative_examples[category].append({
                            'text': match.message_text[:200],
                            'sender': match.sender or 'Unknown',
                            'timestamp': match.timestamp.isoformat() if match.timestamp else None,
                            'evidence': match.evidence,
                            'type': 'negative',
                            'llmValidated': True,
                            'reasoning': reasoning,
                        })
                    llm_validations.append({
                        'category': category,
                        'text': match.message_text[:80] if match.message_text else '',
                        'isValid': True,
                    })
                else:
                    print(f"  Filtered: {category} - '{match.message_text[:50] if match.message_text else ''}...'")
            except Exception as e:
                print(f"  LLM error for {category}: {e}")

        print(f"  Validated counts: {validated_counts}")

        # Build final examples: validated negatives + original positives
        print("Building final examples...")
        for category, examples in all_examples.items():
            validated_examples[category] = []
            if category in NEGATIVE_CATEGORIES:
                # Use validated examples for negatives
                validated_examples[category] = validated_negative_examples.get(category, [])
            else:
                # Positive patterns - keep as-is
                for ex in examples:
                    ex['llmValidated'] = False
                    validated_examples[category].append(ex)

        # Remove empty categories
        all_examples = {k: v for k, v in validated_examples.items() if v}
    else:
        print("Skipping LLM validation (no API key)")
        # Just mark all as not validated
        for category, examples in all_examples.items():
            for ex in examples:
                ex['llmValidated'] = False
        # Keep original counts
        validated_counts = None

    # Add examples to dimensions in result
    if 'emotionalConnection' in result['healthScore']['dimensions']:
        result['healthScore']['dimensions']['emotionalConnection']['examples'] = {
            'vulnerability': all_examples.get('vulnerability', []),
            'support': all_examples.get('support', []),
        }

    if 'affectionCommitment' in result['healthScore']['dimensions']:
        result['healthScore']['dimensions']['affectionCommitment']['examples'] = {
            'affection': all_examples.get('affection', []),
            'appreciation': all_examples.get('appreciation', []),
            'commitment': all_examples.get('commitment', []),
        }

    if 'communicationHealth' in result['healthScore']['dimensions']:
        dim = result['healthScore']['dimensions']['communicationHealth']
        # Add examples to components (for horsemen detail view)
        if 'constructiveDialogue' in dim['components']:
            dim['components']['constructiveDialogue']['criticismExamples'] = all_examples.get('criticism', [])
            dim['components']['constructiveDialogue']['defensivenessExamples'] = all_examples.get('defensiveness', [])
            # Update counts with LLM-validated counts if available
            if validated_counts is not None:
                old_crit = dim['components']['constructiveDialogue'].get('criticismCount', 0)
                old_def = dim['components']['constructiveDialogue'].get('defensivenessCount', 0)
                new_crit = validated_counts.get('criticism', 0)
                new_def = validated_counts.get('defensiveness', 0)
                dim['components']['constructiveDialogue']['criticismCount'] = new_crit
                dim['components']['constructiveDialogue']['defensivenessCount'] = new_def
                # Recalculate constructiveDialogue score based on validated counts
                # Formula: 100 - (criticism * 15) - (defensiveness * 10), min 20
                new_score = max(20, 100 - (new_crit * 15) - (new_def * 10))
                dim['components']['constructiveDialogue']['score'] = new_score
                dim['components']['constructiveDialogue']['insight'] = "Diálogo construtivo e respeitoso" if new_score >= 70 else "Diálogo pode ser mais construtivo"

        if 'emotionalSafety' in dim['components']:
            dim['components']['emotionalSafety']['contemptExamples'] = all_examples.get('contempt', [])
            dim['components']['emotionalSafety']['stonewallingExamples'] = all_examples.get('stonewalling', [])
            # Update counts with LLM-validated counts if available
            if validated_counts is not None:
                old_cont = dim['components']['emotionalSafety'].get('contemptCount', 0)
                old_stone = dim['components']['emotionalSafety'].get('stonewallingCount', 0)
                new_cont = validated_counts.get('contempt', 0)
                new_stone = validated_counts.get('stonewalling', 0)
                dim['components']['emotionalSafety']['contemptCount'] = new_cont
                dim['components']['emotionalSafety']['stonewallingCount'] = new_stone
                # Recalculate emotionalSafety score based on validated counts
                # Contempt is most destructive (weight 20), stonewalling weight 10
                new_score = max(20, 100 - (new_cont * 20) - (new_stone * 10))
                dim['components']['emotionalSafety']['score'] = new_score
                dim['components']['emotionalSafety']['insight'] = "Ambiente emocionalmente seguro" if new_score >= 70 else "Segurança emocional pode melhorar"

        if 'conflictRepair' in dim['components']:
            dim['components']['conflictRepair']['repairExamples'] = all_examples.get('repair', [])

        # Recalculate communicationHealth dimension score
        if validated_counts is not None:
            comp = dim['components']
            scores = [
                comp.get('constructiveDialogue', {}).get('score', 50),
                comp.get('conflictRepair', {}).get('score', 50),
                comp.get('emotionalSafety', {}).get('score', 50),
                comp.get('supportiveResponses', {}).get('score', 50),
            ]
            dim['score'] = round(sum(scores) / len(scores), 1)

    # Recalculate overall score if we updated communicationHealth
    if validated_counts is not None:
        dims = result['healthScore']['dimensions']
        weights = {
            'emotionalConnection': 0.30,
            'affectionCommitment': 0.25,
            'communicationHealth': 0.25,
            'partnershipEquity': 0.20,
        }
        overall = sum(dims[k]['score'] * w for k, w in weights.items())
        result['healthScore']['overall'] = round(overall, 1)
        # Update label based on new score
        if overall >= 80:
            result['healthScore']['label'] = "Excelente"
        elif overall >= 65:
            result['healthScore']['label'] = "Saudável"
        elif overall >= 50:
            result['healthScore']['label'] = "Atenção"
        else:
            result['healthScore']['label'] = "Preocupante"

    # Add message volume
    result['messageVolume'] = df.groupby('sender').size().to_dict()

    # LLM analysis summary
    if use_llm and llm_analyzer:
        result['llmAnalysis'] = {
            'enabled': True,
            'model': 'claude-sonnet-4-20250514',
            'validations': llm_validations,
            'costSummary': llm_analyzer.get_analysis_summary(),
        }
    else:
        result['llmAnalysis'] = {
            'enabled': False,
            'reason': 'No ANTHROPIC_API_KEY set. Run with API key for LLM-validated examples.',
        }

    # Save to file
    output_path = '/Users/thiagoalvarez/Claude_Code/Chat/webapp/data/health_data.json'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    print(f"\nSaved health data to {output_path}")
    print(f"Overall score: {result['healthScore']['overall']}")
    print(f"Weekly data points: {len(weekly_scores)}")
    print(f"Examples extracted: {sum(len(v) for v in all_examples.values())} messages (after filtering)")
    for cat, examples in all_examples.items():
        if examples:
            validated_count = sum(1 for e in examples if e.get('llmValidated'))
            print(f"  - {cat}: {len(examples)} examples ({validated_count} LLM validated)")
    print(f"LLM validations performed: {len(llm_validations)}")

    return result


if __name__ == "__main__":
    result = main()
