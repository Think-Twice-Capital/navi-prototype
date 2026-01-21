"""Chat Statistics Analyzer Module"""

import pandas as pd
import numpy as np
from datetime import timedelta
from typing import Dict, List, Tuple, Optional
from collections import Counter

from .utils import (
    format_duration,
    count_words,
    count_emojis,
    calculate_streak,
    clean_text
)


class ChatAnalyzer:
    """Analyzer for WhatsApp chat statistics."""

    def __init__(self, df: pd.DataFrame):
        """Initialize analyzer with parsed DataFrame."""
        self.df = df.copy()
        self.participants = df['sender'].unique().tolist()

        # Pre-calculate common metrics
        self._text_messages = df[df['type'] == 'text'].copy()

    def get_basic_stats(self) -> Dict:
        """Get basic chat statistics."""
        stats = {
            'total_messages': len(self.df),
            'date_range': {
                'start': self.df['datetime'].min(),
                'end': self.df['datetime'].max(),
                'days': (self.df['datetime'].max() - self.df['datetime'].min()).days
            },
            'participants': self.participants,
            'messages_per_participant': self.df.groupby('sender').size().to_dict(),
            'message_types': self.df['type'].value_counts().to_dict(),
        }
        return stats

    def get_messages_by_period(self) -> Dict:
        """Get message counts by various time periods."""
        return {
            'by_year': self.df.groupby('year').size().to_dict(),
            'by_month': self.df.groupby([self.df['datetime'].dt.to_period('M')]).size().to_dict(),
            'by_day_of_week': self.df.groupby('day_of_week_num').size().to_dict(),
            'by_hour': self.df.groupby('hour').size().to_dict(),
            'by_year_sender': self.df.groupby(['year', 'sender']).size().unstack(fill_value=0).to_dict(),
        }

    def get_activity_heatmap_data(self) -> pd.DataFrame:
        """Get data for hour x day of week heatmap."""
        return self.df.groupby(['day_of_week_num', 'hour']).size().unstack(fill_value=0)

    def get_messages_per_person_over_time(self) -> Dict:
        """Get monthly message counts per person."""
        monthly = self.df.copy()
        monthly['month_period'] = monthly['datetime'].dt.to_period('M')

        result = {}
        for sender in self.participants:
            sender_data = monthly[monthly['sender'] == sender]
            counts = sender_data.groupby('month_period').size()
            result[sender] = counts.to_dict()

        return result

    def get_message_length_stats(self) -> Dict:
        """Get message length statistics."""
        text_msgs = self._text_messages

        stats = {
            'overall': {
                'mean': text_msgs['message_length'].mean(),
                'median': text_msgs['message_length'].median(),
                'std': text_msgs['message_length'].std(),
                'max': text_msgs['message_length'].max(),
                'min': text_msgs['message_length'].min(),
            },
            'by_sender': {}
        }

        for sender in self.participants:
            sender_msgs = text_msgs[text_msgs['sender'] == sender]
            stats['by_sender'][sender] = {
                'mean': sender_msgs['message_length'].mean(),
                'median': sender_msgs['message_length'].median(),
                'std': sender_msgs['message_length'].std(),
                'max': sender_msgs['message_length'].max(),
                'total_chars': sender_msgs['message_length'].sum(),
            }

        return stats

    def get_response_time_stats(self) -> Dict:
        """Calculate response time statistics."""
        df_sorted = self.df.sort_values('datetime').copy()
        df_sorted['prev_sender'] = df_sorted['sender'].shift(1)
        df_sorted['prev_time'] = df_sorted['datetime'].shift(1)
        df_sorted['time_diff'] = (df_sorted['datetime'] - df_sorted['prev_time']).dt.total_seconds()

        # Only consider responses (different sender) within 1 hour
        responses = df_sorted[
            (df_sorted['sender'] != df_sorted['prev_sender']) &
            (df_sorted['time_diff'] > 0) &
            (df_sorted['time_diff'] < 3600)
        ]

        stats = {'by_sender': {}}

        for sender in self.participants:
            sender_responses = responses[responses['sender'] == sender]['time_diff']
            if len(sender_responses) > 0:
                stats['by_sender'][sender] = {
                    'mean': sender_responses.mean(),
                    'median': sender_responses.median(),
                    'p95': sender_responses.quantile(0.95) if len(sender_responses) > 1 else sender_responses.mean(),
                    'count': len(sender_responses),
                }

        return stats

    def get_conversation_initiations(self, gap_hours: int = 8) -> Dict:
        """Count who initiates conversations (after specified gap)."""
        df_sorted = self.df.sort_values('datetime').copy()
        df_sorted['prev_time'] = df_sorted['datetime'].shift(1)
        df_sorted['time_diff'] = (df_sorted['datetime'] - df_sorted['prev_time']).dt.total_seconds() / 3600

        # First message or messages after gap
        initiations = df_sorted[
            (df_sorted['time_diff'].isna()) |
            (df_sorted['time_diff'] >= gap_hours)
        ]

        return {
            'total': len(initiations),
            'by_sender': initiations.groupby('sender').size().to_dict(),
            'gap_hours': gap_hours
        }

    def get_streak_stats(self) -> Dict:
        """Calculate messaging streak statistics."""
        dates = self.df['date'].tolist()
        return calculate_streak(dates)

    def get_call_stats(self) -> Dict:
        """Get call statistics."""
        voice_calls = self.df[self.df['type'].isin(['voice_call', 'missed_voice'])]
        video_calls = self.df[self.df['type'].isin(['video_call', 'missed_video'])]

        # Get call durations
        completed_voice = self.df[
            (self.df['type'] == 'voice_call') &
            (self.df['call_duration_seconds'].notna())
        ]
        completed_video = self.df[
            (self.df['type'] == 'video_call') &
            (self.df['call_duration_seconds'].notna())
        ]

        stats = {
            'voice': {
                'total': len(voice_calls),
                'completed': len(completed_voice),
                'missed': len(self.df[self.df['type'] == 'missed_voice']),
                'total_duration_seconds': completed_voice['call_duration_seconds'].sum() if len(completed_voice) > 0 else 0,
                'avg_duration_seconds': completed_voice['call_duration_seconds'].mean() if len(completed_voice) > 0 else 0,
            },
            'video': {
                'total': len(video_calls),
                'completed': len(completed_video),
                'missed': len(self.df[self.df['type'] == 'missed_video']),
                'total_duration_seconds': completed_video['call_duration_seconds'].sum() if len(completed_video) > 0 else 0,
                'avg_duration_seconds': completed_video['call_duration_seconds'].mean() if len(completed_video) > 0 else 0,
            }
        }

        # Add call trends over time
        all_calls = self.df[self.df['type'].str.contains('call', case=False, na=False)]
        if len(all_calls) > 0:
            stats['by_month'] = all_calls.groupby(
                all_calls['datetime'].dt.to_period('M')
            ).agg({
                'call_duration_seconds': ['count', 'sum']
            }).to_dict()

        return stats

    def get_media_stats(self) -> Dict:
        """Get media sharing statistics."""
        media_types = ['image', 'video', 'audio', 'document', 'sticker', 'gif']

        stats = {
            'total': len(self.df[self.df['type'].isin(media_types)]),
            'by_type': {},
            'by_sender': {},
        }

        for media_type in media_types:
            count = len(self.df[self.df['type'] == media_type])
            if count > 0:
                stats['by_type'][media_type] = count

        for sender in self.participants:
            sender_media = self.df[
                (self.df['sender'] == sender) &
                (self.df['type'].isin(media_types))
            ]
            stats['by_sender'][sender] = {
                'total': len(sender_media),
                'by_type': sender_media['type'].value_counts().to_dict()
            }

        return stats

    def get_word_frequency(self, top_n: int = 50) -> Dict:
        """Get word frequency analysis."""
        text_messages = self._text_messages['message'].tolist()

        overall_words = count_words(text_messages)

        result = {
            'overall': overall_words.most_common(top_n),
            'by_sender': {}
        }

        for sender in self.participants:
            sender_msgs = self._text_messages[
                self._text_messages['sender'] == sender
            ]['message'].tolist()
            sender_words = count_words(sender_msgs)
            result['by_sender'][sender] = sender_words.most_common(top_n)

        return result

    def get_emoji_frequency(self, top_n: int = 30) -> Dict:
        """Get emoji frequency analysis."""
        all_messages = self.df['message'].tolist()
        overall_emojis = count_emojis(all_messages)

        result = {
            'overall': overall_emojis.most_common(top_n),
            'by_sender': {}
        }

        for sender in self.participants:
            sender_msgs = self.df[self.df['sender'] == sender]['message'].tolist()
            sender_emojis = count_emojis(sender_msgs)
            result['by_sender'][sender] = sender_emojis.most_common(top_n)

        return result

    def get_terms_of_endearment(self) -> Dict:
        """Count terms of endearment in Portuguese."""
        terms = {
            'amor': r'\bamor\b',
            'te amo': r'\bte\s+amo\b',
            'te adoro': r'\bte\s+adoro\b',
            'querido/a': r'\bquerid[oa]\b',
            'meu bem': r'\bmeu\s+bem\b',
            'saudades': r'\bsaudades?\b',
            'lindo/a': r'\blind[oa]\b',
            'fofo/a': r'\bfof[oa]\b',
            'bebê': r'\bbeb[êe]\b',
            'meu amor': r'\bmeu\s+amor\b',
            'coração': r'\bcora[çc][ãa]o\b',
            'princesa': r'\bprincesa\b',
            'anjo': r'\banjo\b',
            'vida': r'\bvida\b',
            'neném': r'\bnen[ée]m\b',
        }

        results = {'overall': {}, 'by_sender': {}}

        all_text = ' '.join(self.df['message'].str.lower().fillna(''))

        for term, pattern in terms.items():
            import re
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            if matches:
                results['overall'][term] = len(matches)

        for sender in self.participants:
            sender_text = ' '.join(
                self.df[self.df['sender'] == sender]['message'].str.lower().fillna('')
            )
            results['by_sender'][sender] = {}
            for term, pattern in terms.items():
                import re
                matches = re.findall(pattern, sender_text, re.IGNORECASE)
                if matches:
                    results['by_sender'][sender][term] = len(matches)

        return results

    def get_te_amo_by_year(self) -> Dict:
        """Get 'te amo' counts by year."""
        import re
        pattern = r'\bte\s+amo\b'

        results = {}
        for year in self.df['year'].unique():
            year_msgs = self.df[self.df['year'] == year]['message'].str.lower().fillna('')
            count = sum(len(re.findall(pattern, msg, re.IGNORECASE)) for msg in year_msgs)
            results[year] = count

        return dict(sorted(results.items()))

    def get_busiest_day(self) -> Dict:
        """Find the busiest day in chat history."""
        daily_counts = self.df.groupby('date').size()
        busiest_date = daily_counts.idxmax()
        busiest_count = daily_counts.max()

        return {
            'date': busiest_date,
            'count': busiest_count,
            'messages': self.df[self.df['date'] == busiest_date][['datetime', 'sender', 'message']].to_dict('records')
        }

    def get_longest_message(self) -> Dict:
        """Find the longest message."""
        text_msgs = self._text_messages
        if text_msgs.empty:
            return None

        longest_idx = text_msgs['message_length'].idxmax()
        longest = text_msgs.loc[longest_idx]

        return {
            'sender': longest['sender'],
            'date': longest['datetime'],
            'length': longest['message_length'],
            'message': longest['message'][:500] + '...' if len(longest['message']) > 500 else longest['message']
        }

    def get_yearly_summary(self) -> Dict:
        """Get summary statistics for each year."""
        years = sorted(self.df['year'].unique())
        summary = {}

        for year in years:
            year_df = self.df[self.df['year'] == year]
            year_text = year_df[year_df['type'] == 'text']

            summary[year] = {
                'total_messages': len(year_df),
                'text_messages': len(year_text),
                'media_count': len(year_df[year_df['type'].isin(['image', 'video', 'audio', 'document'])]),
                'calls': len(year_df[year_df['type'].str.contains('call', case=False, na=False)]),
                'by_sender': year_df.groupby('sender').size().to_dict(),
                'active_days': year_df['date'].nunique(),
            }

        return summary

    def get_daily_activity_data(self) -> pd.DataFrame:
        """Get daily message counts for calendar heatmap."""
        return self.df.groupby('date').size().reset_index(name='count')

    def get_message_length_over_time(self) -> pd.DataFrame:
        """Get average message length by month."""
        text_msgs = self._text_messages.copy()
        text_msgs['month_period'] = text_msgs['datetime'].dt.to_period('M')

        return text_msgs.groupby(['month_period', 'sender'])['message_length'].mean().unstack(fill_value=0)

    def get_sentiment_by_topic(self) -> Dict:
        """
        Get average sentiment score per topic.

        Returns:
            Dictionary mapping topics to sentiment stats
        """
        if 'sentiment_score' not in self.df.columns or 'primary_topic' not in self.df.columns:
            return {}

        text_df = self._text_messages

        results = {}
        for topic in text_df['primary_topic'].unique():
            topic_msgs = text_df[text_df['primary_topic'] == topic]
            if len(topic_msgs) > 0:
                results[topic] = {
                    'avg_sentiment': topic_msgs['sentiment_score'].mean(),
                    'std_sentiment': topic_msgs['sentiment_score'].std(),
                    'positive_count': len(topic_msgs[topic_msgs['sentiment_score'] > 0.1]),
                    'negative_count': len(topic_msgs[topic_msgs['sentiment_score'] < -0.1]),
                    'neutral_count': len(topic_msgs[(topic_msgs['sentiment_score'] >= -0.1) &
                                                     (topic_msgs['sentiment_score'] <= 0.1)]),
                    'total_messages': len(topic_msgs),
                }

        return results

    def get_response_time_by_topic(self) -> Dict:
        """
        Get average response time per topic.

        Returns:
            Dictionary mapping topics to response time stats
        """
        if 'primary_topic' not in self.df.columns:
            return {}

        df_sorted = self.df.sort_values('datetime').copy()
        df_sorted['prev_sender'] = df_sorted['sender'].shift(1)
        df_sorted['prev_time'] = df_sorted['datetime'].shift(1)
        df_sorted['time_diff'] = (df_sorted['datetime'] - df_sorted['prev_time']).dt.total_seconds()

        # Only consider responses (different sender) within 1 hour
        responses = df_sorted[
            (df_sorted['sender'] != df_sorted['prev_sender']) &
            (df_sorted['time_diff'] > 0) &
            (df_sorted['time_diff'] < 3600)
        ]

        results = {}
        for topic in responses['primary_topic'].unique():
            topic_responses = responses[responses['primary_topic'] == topic]['time_diff']
            if len(topic_responses) > 0:
                results[topic] = {
                    'avg_response_seconds': topic_responses.mean(),
                    'median_response_seconds': topic_responses.median(),
                    'response_count': len(topic_responses),
                }

        # Also break down by sender within topic
        for topic in results:
            results[topic]['by_sender'] = {}
            topic_df = responses[responses['primary_topic'] == topic]
            for sender in self.participants:
                sender_responses = topic_df[topic_df['sender'] == sender]['time_diff']
                if len(sender_responses) > 0:
                    results[topic]['by_sender'][sender] = {
                        'avg_response_seconds': sender_responses.mean(),
                        'median_response_seconds': sender_responses.median(),
                    }

        return results

    def get_topic_balance(self) -> Dict:
        """
        Get message contribution percentage per sender per topic.

        Returns:
            Dictionary mapping topics to sender balance stats
        """
        if 'primary_topic' not in self.df.columns:
            return {}

        text_df = self._text_messages

        results = {}
        for topic in text_df['primary_topic'].unique():
            topic_msgs = text_df[text_df['primary_topic'] == topic]
            total = len(topic_msgs)

            if total > 0:
                sender_counts = topic_msgs.groupby('sender').size()
                results[topic] = {
                    'total_messages': total,
                    'by_sender': {},
                    'balance_score': 0,
                }

                for sender in self.participants:
                    count = sender_counts.get(sender, 0)
                    pct = (count / total * 100)
                    results[topic]['by_sender'][sender] = {
                        'count': count,
                        'percentage': pct
                    }

                # Calculate balance score (0 = perfectly balanced, 100 = completely one-sided)
                if len(self.participants) == 2:
                    pcts = [results[topic]['by_sender'][p]['percentage'] for p in self.participants]
                    # Balance score: 0 means 50-50, 50 means 100-0
                    results[topic]['balance_score'] = abs(pcts[0] - 50)

        return results

    def get_communication_health_score(self, sentiment_analyzer=None, topic_analyzer=None) -> Dict:
        """
        Calculate a composite communication health score (1-10).

        Components:
        - Response symmetry (both respond equally)
        - Topic diversity
        - Sentiment trend (positive trajectory)
        - Affection expression frequency
        - Conversation frequency trend

        Returns:
            Dictionary with overall score and component breakdown
        """
        scores = {}

        # 1. Response Symmetry Score (0-10)
        response_stats = self.get_response_time_stats()
        if response_stats['by_sender'] and len(response_stats['by_sender']) == 2:
            response_counts = [s['count'] for s in response_stats['by_sender'].values()]
            total_responses = sum(response_counts)
            if total_responses > 0:
                balance = min(response_counts) / max(response_counts) if max(response_counts) > 0 else 0
                scores['response_symmetry'] = balance * 10
            else:
                scores['response_symmetry'] = 5.0
        else:
            scores['response_symmetry'] = 5.0

        # 2. Topic Diversity Score (0-10)
        if 'primary_topic' in self.df.columns:
            text_df = self._text_messages
            topic_counts = text_df['primary_topic'].value_counts(normalize=True)
            # Calculate entropy-based diversity
            from math import log2
            entropy = 0
            for pct in topic_counts:
                if pct > 0:
                    entropy -= pct * log2(pct)
            max_entropy = log2(9)  # 9 topics
            scores['topic_diversity'] = (entropy / max_entropy) * 10 if max_entropy > 0 else 5.0
        else:
            scores['topic_diversity'] = 5.0

        # 3. Sentiment Trend Score (0-10)
        if 'sentiment_score' in self.df.columns:
            text_df = self._text_messages.copy()
            text_df['year'] = text_df['datetime'].dt.year
            yearly_sentiment = text_df.groupby('year')['sentiment_score'].mean()

            if len(yearly_sentiment) >= 2:
                # Compare last 2 years sentiment trend
                recent_years = sorted(yearly_sentiment.index)[-2:]
                trend = yearly_sentiment[recent_years[-1]] - yearly_sentiment[recent_years[-2]]
                # Score: improving sentiment = higher score
                scores['sentiment_trend'] = min(max((trend + 0.2) / 0.4 * 10, 0), 10)
            else:
                avg_sentiment = text_df['sentiment_score'].mean()
                scores['sentiment_trend'] = min(max((avg_sentiment + 0.5) / 1.0 * 10, 0), 10)
        else:
            scores['sentiment_trend'] = 5.0

        # 4. Affection Frequency Score (0-10)
        terms = self.get_terms_of_endearment()
        total_messages = len(self._text_messages)
        if total_messages > 0 and terms['overall']:
            total_affection = sum(terms['overall'].values())
            affection_rate = total_affection / total_messages * 100
            # Score based on affection rate (aim for ~5% as healthy)
            scores['affection_frequency'] = min(affection_rate / 5 * 10, 10)
        else:
            scores['affection_frequency'] = 5.0

        # 5. Conversation Frequency Trend (0-10)
        text_df = self._text_messages.copy()
        text_df['year'] = text_df['datetime'].dt.year
        yearly_counts = text_df.groupby('year').size()

        if len(yearly_counts) >= 2:
            recent_years = sorted(yearly_counts.index)[-2:]
            recent_count = yearly_counts[recent_years[-1]]
            prev_count = yearly_counts[recent_years[-2]]
            if prev_count > 0:
                change_rate = (recent_count - prev_count) / prev_count
                # Stable or growing is good, declining is not as good
                scores['frequency_trend'] = min(max((change_rate + 0.5) / 1.0 * 10, 3), 10)
            else:
                scores['frequency_trend'] = 5.0
        else:
            scores['frequency_trend'] = 5.0

        # Calculate overall score (weighted average)
        weights = {
            'response_symmetry': 0.20,
            'topic_diversity': 0.15,
            'sentiment_trend': 0.25,
            'affection_frequency': 0.25,
            'frequency_trend': 0.15,
        }

        overall = sum(scores[k] * weights[k] for k in scores)

        return {
            'overall_score': round(overall, 1),
            'components': {k: round(v, 1) for k, v in scores.items()},
            'weights': weights
        }
