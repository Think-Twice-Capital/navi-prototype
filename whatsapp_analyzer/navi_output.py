"""
NAVI Output Generator Module

Transforms analyzed WhatsApp chat data into JSON outputs
following the ANALYZER_OUTPUT_SPEC.md specification.

Generates three outputs:
1. Categorized Messages for UI
2. Scoring System (scientific health metrics based on research)
3. AI Agent Contexts

Scientific Framework:
- Gottman's research for conflict detection and predictive validity
- Interpersonal Process Model for connection quality
- Maintenance Behaviors for partnership equity

References:
- Gottman, J. M. (1994). What Predicts Divorce?
- Reis, H. T., & Shaver, P. (1988). Intimacy as an interpersonal process
- Stafford, L., & Canary, D. J. (1991). Maintenance strategies
"""

import re
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
import pandas as pd

from .scientific_scoring import ScientificHealthScorer
from .pattern_detectors import RelationshipPatternAnalyzer, PatternSummary


class NAVIOutputGenerator:
    """Generates NAVI-formatted JSON outputs from analyzed chat data."""

    # Space/Topic mapping with UI metadata
    SPACE_CONFIG = {
        'trabalho': {'icon': '💼', 'color': '#3498db'},
        'casa': {'icon': '🏠', 'color': '#e67e22'},
        'filhos': {'icon': '👨‍👩‍👧', 'color': '#9b59b6'},
        'viagem': {'icon': '✈️', 'color': '#1abc9c'},
        'saude': {'icon': '🏥', 'color': '#e74c3c'},
        'financas': {'icon': '💰', 'color': '#f1c40f'},
        'lazer': {'icon': '🎉', 'color': '#2ecc71'},
        'relacionamento': {'icon': '❤️', 'color': '#e91e63'},
        'outros': {'icon': '📝', 'color': '#95a5a6'},
    }

    # Topic to UI space mapping
    TOPIC_TO_SPACE = {
        'trabalho': 'trabalho',
        'casa': 'casa',
        'filhos': 'filhos',
        'viagem': 'viagem',
        'saude': 'saude',
        'financas': 'financas',
        'lazer': 'lazer',
        'relacionamento': 'nos',
        'outros': 'outros',
    }

    # Status labels
    STATUS_LABELS = {
        'pending': '⏳ Pendente',
        'done': '✅ Feito',
        'urgent': '🔴 Urgente',
        'scheduled': '📅 Agendado',
        'connection': '💕 Conexão',
    }

    # Action verbs for task detection (Portuguese)
    ACTION_VERBS = {
        'pagar', 'fazer', 'comprar', 'ligar', 'marcar', 'resolver',
        'buscar', 'levar', 'enviar', 'mandar', 'agendar', 'confirmar',
        'cancelar', 'verificar', 'checar', 'organizar', 'limpar',
        'preparar', 'cuidar', 'pedir', 'reservar', 'consertar',
    }

    # Completion markers
    COMPLETION_MARKERS = {
        'feito', 'pago', 'pronto', 'resolvido', 'comprado', 'enviado',
        'marcado', 'agendado', 'confirmado', 'cancelado', 'ok feito',
        'já fiz', 'tá feito', 'está feito', 'concluído', 'terminado',
    }

    # Urgency markers
    URGENCY_MARKERS = {
        'hoje', 'agora', 'urgente', 'urgência', 'imediato', 'já',
        'não pode atrasar', 'prazo', 'deadline', 'vence hoje',
        'precisamos', 'tem que ser hoje',
    }

    # Future time markers
    FUTURE_MARKERS = {
        'amanhã', 'depois de amanhã', 'segunda', 'terça', 'quarta',
        'quinta', 'sexta', 'sábado', 'domingo', 'semana que vem',
        'próxima semana', 'próximo mês', 'mês que vem',
    }

    # Affection markers
    AFFECTION_MARKERS = {
        'te amo', 'amo você', 'amor', 'saudade', 'saudades',
        'obrigado', 'obrigada', 'você é incrível', 'você é o melhor',
        'você é a melhor', 'maravilhoso', 'maravilhosa', 'perfeito',
        'perfeita', 'lindo', 'linda', 'fofo', 'fofa',
    }

    def __init__(self, df: pd.DataFrame, thiago_name: str = 'Thiago Alvarez',
                 daniela_name: str = 'Daniela Anderez'):
        """
        Initialize with analyzed DataFrame.

        Args:
            df: DataFrame with parsed and analyzed messages
            thiago_name: Full name for Thiago
            daniela_name: Full name for Daniela
        """
        self.df = df.copy()
        self.thiago_name = thiago_name
        self.daniela_name = daniela_name

        # Sender initials
        self.sender_initials = {
            thiago_name: 'T',
            daniela_name: 'D',
        }

    def _get_sender_initial(self, sender: str) -> str:
        """Get sender initial."""
        return self.sender_initials.get(sender, sender[0] if sender else '?')

    def _detect_status(self, messages: List[Dict]) -> str:
        """
        Detect status from a group of messages.

        Returns: 'pending', 'done', 'urgent', 'scheduled', or 'connection'
        """
        combined_text = ' '.join(m.get('text', '') for m in messages).lower()

        # Check for completion first
        for marker in self.COMPLETION_MARKERS:
            if marker in combined_text:
                return 'done'

        # Check for check mark emoji
        if '✓' in combined_text or '✔' in combined_text:
            return 'done'

        # Check for action verbs (indicates potential task)
        has_action = any(verb in combined_text for verb in self.ACTION_VERBS)

        if has_action:
            # Check urgency
            if any(marker in combined_text for marker in self.URGENCY_MARKERS):
                return 'urgent'

            # Check scheduled
            if any(marker in combined_text for marker in self.FUTURE_MARKERS):
                return 'scheduled'

            return 'pending'

        # Check for connection moment
        if any(marker in combined_text for marker in self.AFFECTION_MARKERS):
            return 'connection'

        return 'pending'

    def _detect_has_action(self, text: str) -> bool:
        """Check if message requires action."""
        text_lower = text.lower()
        return any(verb in text_lower for verb in self.ACTION_VERBS)

    def _detect_owner(self, messages: List[Dict]) -> Optional[str]:
        """Detect who should own the task based on message context."""
        combined_text = ' '.join(m.get('text', '') for m in messages).lower()

        # Check for direct assignment patterns
        if 'você pode' in combined_text or 'você faz' in combined_text:
            # Whoever is being asked
            last_sender = messages[-1].get('sender') if messages else None
            if last_sender == self.thiago_name:
                return 'daniela'
            elif last_sender == self.daniela_name:
                return 'thiago'

        return None

    def _extract_due_date(self, text: str) -> Optional[str]:
        """Extract due date from text."""
        text_lower = text.lower()

        if 'hoje' in text_lower:
            return datetime.now().strftime('%Y-%m-%d')
        elif 'amanhã' in text_lower:
            return (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

        # Check for day patterns
        days = {'segunda': 0, 'terça': 1, 'quarta': 2, 'quinta': 3,
                'sexta': 4, 'sábado': 5, 'domingo': 6}
        for day_name, day_num in days.items():
            if day_name in text_lower:
                today = datetime.now()
                days_ahead = day_num - today.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                return (today + timedelta(days=days_ahead)).strftime('%Y-%m-%d')

        return None

    def _create_summary(self, messages: List[Dict], topic: str) -> str:
        """Create a concise summary for a message group."""
        if not messages:
            return "Conversa"

        # Get first substantive message
        for msg in messages:
            text = msg.get('text', '')
            if len(text) > 5 and msg.get('type') == 'text':
                # Truncate to 50 chars
                summary = text[:47] + '...' if len(text) > 50 else text
                return summary

        return f"Conversa sobre {topic}"

    def _group_messages_by_conversation(self, gap_minutes: int = 30) -> List[Dict]:
        """
        Group messages into conversations based on time gaps and topics.

        Args:
            gap_minutes: Minutes of silence to start new conversation

        Returns:
            List of message groups
        """
        df = self.df.sort_values('datetime').copy()

        # Calculate time differences
        df['time_diff'] = df['datetime'].diff().dt.total_seconds() / 60
        df['new_conversation'] = (df['time_diff'] > gap_minutes) | df['time_diff'].isna()

        # Also start new conversation on topic change
        if 'primary_topic' in df.columns:
            df['topic_change'] = df['primary_topic'] != df['primary_topic'].shift(1)
            df['new_conversation'] = df['new_conversation'] | df['topic_change']

        df['conversation_id'] = df['new_conversation'].cumsum()

        # Build message groups
        groups = []
        for conv_id, conv_df in df.groupby('conversation_id'):
            if len(conv_df) == 0:
                continue

            # Get topic for this conversation
            topic = 'outros'
            if 'primary_topic' in conv_df.columns:
                topic_counts = conv_df['primary_topic'].value_counts()
                if len(topic_counts) > 0:
                    topic = topic_counts.index[0]

            space = self.TOPIC_TO_SPACE.get(topic, 'outros')

            # Build messages list
            messages = []
            for _, row in conv_df.iterrows():
                msg = {
                    'time': row['datetime'].strftime('%H:%M'),
                    'sender': self._get_sender_initial(row['sender']),
                    'senderName': row['sender'],
                    'text': row['message'] if pd.notna(row['message']) else '',
                    'type': row['type'],
                }
                messages.append(msg)

            # Detect status
            status = self._detect_status(messages)
            has_action = any(self._detect_has_action(m['text']) for m in messages)

            # Extract due date
            combined_text = ' '.join(m['text'] for m in messages)
            due_date = self._extract_due_date(combined_text)

            # Detect owner
            owner = self._detect_owner(messages)

            group = {
                'id': str(uuid.uuid4()),
                'space': space,
                'status': status,
                'statusLabel': self.STATUS_LABELS.get(status, '📝 Outros'),
                'summary': self._create_summary(messages, topic),
                'hasAction': has_action,
                'dueDate': due_date,
                'owner': owner,
                'messages': messages,
                'datetime': conv_df['datetime'].min().isoformat(),
            }
            groups.append(group)

        return groups

    def _extract_tasks(self, message_groups: List[Dict]) -> List[Dict]:
        """Extract tasks from message groups."""
        tasks = []

        for group in message_groups:
            if not group.get('hasAction'):
                continue

            status = group.get('status', 'pending')
            if status == 'connection':
                continue

            # Find the action message
            action_text = None
            for msg in group.get('messages', []):
                if self._detect_has_action(msg.get('text', '')):
                    action_text = msg.get('text', '')
                    break

            if not action_text:
                continue

            # Format task title
            title = action_text[:60] + '...' if len(action_text) > 60 else action_text

            # Extract monetary values
            money_match = re.search(r'R?\$?\s*([\d.,]+)', action_text)
            if money_match:
                amount = money_match.group(1)
                # Add to title if not already there
                if 'R$' not in title:
                    title = f"{title} - R${amount}"

            task = {
                'id': str(uuid.uuid4()),
                'title': title,
                'space': group.get('space', 'outros'),
                'status': status,
                'due': self._format_due_date(group.get('dueDate')),
                'owner': group.get('owner'),
                'sourceGroupId': group.get('id'),
                'extractedFrom': action_text,
            }
            tasks.append(task)

        return tasks

    def _format_due_date(self, date_str: Optional[str]) -> Optional[str]:
        """Format due date to human-readable Portuguese."""
        if not date_str:
            return None

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d')
            today = datetime.now().date()
            delta = (date.date() - today).days

            if delta == 0:
                return 'Hoje'
            elif delta == 1:
                return 'Amanhã'
            elif delta < 7:
                days_pt = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
                return days_pt[date.weekday()]
            else:
                return date.strftime('%d/%m')
        except:
            return date_str

    def generate_message_groups(self, gap_minutes: int = 30,
                                 recent_days: int = 30) -> Dict:
        """
        Generate categorized message groups for UI.

        Args:
            gap_minutes: Minutes of silence to start new conversation
            recent_days: Only include messages from last N days

        Returns:
            Dictionary with messageGroups and tasks
        """
        # Filter to recent messages if specified
        if recent_days:
            cutoff = datetime.now() - timedelta(days=recent_days)
            df_recent = self.df[self.df['datetime'] >= cutoff].copy()
            if len(df_recent) == 0:
                df_recent = self.df.copy()
        else:
            df_recent = self.df.copy()

        # Store filtered df temporarily
        original_df = self.df
        self.df = df_recent

        # Group messages
        message_groups = self._group_messages_by_conversation(gap_minutes)

        # Extract tasks
        tasks = self._extract_tasks(message_groups)

        # Restore original df
        self.df = original_df

        return {
            'messageGroups': message_groups,
            'tasks': tasks,
            'generated': datetime.now().isoformat(),
            'period': {
                'days': recent_days,
                'start': df_recent['datetime'].min().isoformat() if len(df_recent) > 0 else None,
                'end': df_recent['datetime'].max().isoformat() if len(df_recent) > 0 else None,
            }
        }

    def generate_health_score(self, analyzer=None) -> Dict:
        """
        Generate scientific health score using validated academic frameworks.

        Based on:
        - Gottman's research for conflict detection (Four Horsemen, 5:1 ratio)
        - Interpersonal Process Model for connection quality
        - Maintenance Behaviors for partnership equity

        Scale: 1-100 (granular)

        Dimensions:
        - Connection Quality (30%)
        - Relationship Maintenance (25%)
        - Communication Health (25%)
        - Partnership Dynamics (20%)

        Args:
            analyzer: ChatAnalyzer instance for additional metrics (optional)

        Returns:
            Scientific health score dictionary with dimensions and insights
        """
        # Initialize scientific scorer
        scorer = ScientificHealthScorer(
            df=self.df,
            sender_col='sender',
            message_col='message',
            datetime_col='datetime',
            person_a=self.thiago_name,
            person_b=self.daniela_name
        )

        # Get full scientific score
        return scorer.to_dict()

    def generate_health_score_legacy(self, analyzer=None) -> Dict:
        """
        Legacy health score calculation (deprecated).

        Kept for backwards compatibility. Use generate_health_score() instead.
        """
        text_df = self.df[self.df['type'] == 'text'].copy()

        # Calculate response symmetry
        response_symmetry = self._calculate_response_symmetry()

        # Calculate topic diversity
        topic_diversity = self._calculate_topic_diversity()

        # Calculate sentiment trend
        sentiment_trend = self._calculate_sentiment_trend()

        # Calculate affection frequency
        affection_freq = self._calculate_affection_frequency()

        # Calculate conversation frequency
        conv_frequency = self._calculate_conversation_frequency()

        # Calculate overall score (1-10 scale, legacy)
        weights = {
            'responseSymmetry': 0.20,
            'topicDiversity': 0.15,
            'sentimentTrend': 0.25,
            'affectionFrequency': 0.20,
            'conversationFrequency': 0.20,
        }

        overall = (
            response_symmetry['score'] * weights['responseSymmetry'] +
            topic_diversity['score'] * weights['topicDiversity'] +
            sentiment_trend['score'] * weights['sentimentTrend'] +
            affection_freq['score'] * weights['affectionFrequency'] +
            conv_frequency['score'] * weights['conversationFrequency']
        )

        # Determine label
        if overall >= 8.1:
            label = 'Excelente'
        elif overall >= 6.6:
            label = 'Saudável'
        elif overall >= 5.1:
            label = 'Moderado'
        elif overall >= 3.1:
            label = 'Preocupante'
        else:
            label = 'Crítico'

        return {
            'healthScoreLegacy': {
                'overall': round(overall, 1),
                'label': label,
                'scale': '1-10',
                'deprecated': True,
                'components': {
                    'responseSymmetry': response_symmetry,
                    'topicDiversity': topic_diversity,
                    'sentimentTrend': sentiment_trend,
                    'affectionFrequency': affection_freq,
                    'conversationFrequency': conv_frequency,
                }
            }
        }

    def _calculate_response_symmetry(self) -> Dict:
        """Calculate response symmetry score (legacy)."""
        df_sorted = self.df.sort_values('datetime').copy()
        df_sorted['prev_sender'] = df_sorted['sender'].shift(1)

        # Count responses by each person
        responses = df_sorted[df_sorted['sender'] != df_sorted['prev_sender']]
        response_counts = responses.groupby('sender').size()

        if len(response_counts) < 2:
            return {'score': 5.0, 'percentage': 50, 'description': 'Dados insuficientes'}

        total = response_counts.sum()
        percentages = (response_counts / total * 100).to_dict()

        # Calculate balance (100 = perfect 50-50)
        values = list(percentages.values())
        balance = 100 - abs(values[0] - 50) * 2

        score = balance / 10

        return {
            'score': round(score, 1),
            'percentage': round(balance),
            'description': 'Equilíbrio nas respostas'
        }

    def _calculate_topic_diversity(self) -> Dict:
        """Calculate topic diversity score (legacy)."""
        if 'primary_topic' not in self.df.columns:
            return {'score': 5.0, 'value': '0/8', 'description': 'Sem dados de tópicos'}

        text_df = self.df[self.df['type'] == 'text']
        active_topics = text_df['primary_topic'].nunique()
        total_topics = 8  # Excluding 'outros'

        # Count topics with significant activity (>1% of messages)
        topic_counts = text_df['primary_topic'].value_counts(normalize=True)
        significant_topics = len(topic_counts[topic_counts > 0.01])

        score = (significant_topics / total_topics) * 10

        return {
            'score': round(min(score, 10), 1),
            'value': f'{significant_topics}/{total_topics}',
            'description': 'Tópicos ativos' if significant_topics >= 6 else 'Diversidade de tópicos'
        }

    def _calculate_sentiment_trend(self) -> Dict:
        """Calculate sentiment trend score (legacy)."""
        if 'sentiment_score' not in self.df.columns:
            return {'score': 5.0, 'trend': '0%', 'description': 'Sem dados de sentimento'}

        text_df = self.df[self.df['type'] == 'text'].copy()

        # Get last 7 days vs previous 7 days
        now = text_df['datetime'].max()
        week_ago = now - timedelta(days=7)
        two_weeks_ago = now - timedelta(days=14)

        current_week = text_df[text_df['datetime'] >= week_ago]['sentiment_score'].mean()
        previous_week = text_df[(text_df['datetime'] >= two_weeks_ago) &
                                 (text_df['datetime'] < week_ago)]['sentiment_score'].mean()

        if pd.isna(previous_week) or previous_week == 0:
            change = 0
        else:
            change = ((current_week - previous_week) / abs(previous_week)) * 100 if previous_week != 0 else 0

        # Score: positive trend = higher score
        score = 5 + (change / 20)  # Each 20% change = 1 point
        score = max(1, min(10, score))

        trend_str = f"+{change:.0f}%" if change > 0 else f"{change:.0f}%"
        desc = 'Sentimento melhorando' if change > 0 else 'Sentimento estável' if change == 0 else 'Sentimento declinando'

        return {
            'score': round(score, 1),
            'trend': trend_str,
            'description': desc
        }

    def _calculate_affection_frequency(self) -> Dict:
        """Calculate affection expression frequency (legacy)."""
        text_df = self.df[self.df['type'] == 'text']
        combined_text = ' '.join(text_df['message'].fillna('').astype(str)).lower()

        # Count affection markers
        affection_count = sum(
            len(re.findall(rf'\b{re.escape(marker)}\b', combined_text))
            for marker in self.AFFECTION_MARKERS
        )

        # Calculate per week
        total_days = (self.df['datetime'].max() - self.df['datetime'].min()).days
        weeks = max(total_days / 7, 1)
        per_week = affection_count / weeks

        # Score based on per_week (baseline ~10 per week)
        score = min((per_week / 10) * 10, 10)

        return {
            'score': round(score, 1),
            'perWeek': round(per_week, 1),
            'description': 'Expressões de carinho'
        }

    def _calculate_conversation_frequency(self) -> Dict:
        """Calculate conversation frequency score (legacy)."""
        daily_counts = self.df.groupby(self.df['datetime'].dt.date).size()
        avg_per_day = daily_counts.mean()

        # Score based on avg (baseline ~50 per day)
        score = min((avg_per_day / 50) * 10, 10)

        return {
            'score': round(score, 1),
            'perDay': round(avg_per_day, 0),
            'description': 'Mensagens por dia'
        }

    def generate_pattern_analysis(self) -> Dict:
        """
        Generate detailed pattern analysis using Gottman's framework.

        Returns:
            Dictionary with Four Horsemen detection and positive pattern counts
        """
        analyzer = RelationshipPatternAnalyzer()
        summary = analyzer.analyze_conversation(
            self.df,
            sender_col='sender',
            message_col='message',
            datetime_col='datetime'
        )

        return {
            'patternAnalysis': {
                'positiveNegativeRatio': round(summary.positive_ratio, 1),
                'gottmanRatioMet': summary.positive_ratio >= 5.0,
                'fourHorsemen': summary.four_horsemen_counts,
                'positivePatterns': summary.positive_counts,
                'totalPositive': summary.total_positive,
                'totalNegative': summary.total_negative,
                'alerts': summary.alerts,
                'methodology': 'Gottman Four Horsemen + Stafford-Canary Maintenance Behaviors'
            }
        }

    def generate_balance_metrics(self) -> Dict:
        """Generate balance metrics."""
        text_df = self.df[self.df['type'] == 'text']

        # Task distribution (based on messages with action verbs received)
        task_dist = self._calculate_task_distribution()

        # Conversation initiation
        conv_init = self._calculate_conversation_initiation()

        # Response time
        resp_time = self._calculate_response_times()

        # Message volume
        msg_volume = self._calculate_message_volume()

        return {
            'balance': {
                'taskDistribution': task_dist,
                'conversationInitiation': conv_init,
                'responseTime': resp_time,
                'messageVolume': msg_volume,
            }
        }

    def _calculate_task_distribution(self) -> Dict:
        """Calculate task distribution between partners."""
        # Messages with action verbs directed at each person
        # (Simplified: count action verbs in messages sent TO each person)

        df_sorted = self.df.sort_values('datetime').copy()
        df_sorted['next_sender'] = df_sorted['sender'].shift(-1)

        thiago_tasks = 0
        daniela_tasks = 0

        for _, row in df_sorted.iterrows():
            if row['type'] != 'text':
                continue
            text = str(row.get('message', '')).lower()
            if self._detect_has_action(text):
                # Task is for the recipient (next sender or explicit)
                if row['sender'] == self.thiago_name:
                    daniela_tasks += 1
                else:
                    thiago_tasks += 1

        total = thiago_tasks + daniela_tasks
        if total == 0:
            return {'thiago': 50, 'daniela': 50, 'trend': 'balanced'}

        thiago_pct = round((thiago_tasks / total) * 100)
        daniela_pct = 100 - thiago_pct

        if abs(thiago_pct - 50) < 10:
            trend = 'balanced'
        elif thiago_pct > 50:
            trend = 'thiago_increasing'
        else:
            trend = 'daniela_increasing'

        return {
            'thiago': thiago_pct,
            'daniela': daniela_pct,
            'trend': trend
        }

    def _calculate_conversation_initiation(self) -> Dict:
        """Calculate who initiates conversations more."""
        df_sorted = self.df.sort_values('datetime').copy()
        df_sorted['time_diff'] = df_sorted['datetime'].diff().dt.total_seconds() / 3600

        # Conversations start after 4+ hours gap
        initiations = df_sorted[
            (df_sorted['time_diff'].isna()) |
            (df_sorted['time_diff'] >= 4)
        ]

        init_counts = initiations.groupby('sender').size()
        total = init_counts.sum()

        if total == 0:
            return {'thiago': 50, 'daniela': 50}

        thiago_pct = round((init_counts.get(self.thiago_name, 0) / total) * 100)
        daniela_pct = 100 - thiago_pct

        return {
            'thiago': thiago_pct,
            'daniela': daniela_pct
        }

    def _calculate_response_times(self) -> Dict:
        """Calculate average response times."""
        df_sorted = self.df.sort_values('datetime').copy()
        df_sorted['prev_sender'] = df_sorted['sender'].shift(1)
        df_sorted['prev_time'] = df_sorted['datetime'].shift(1)
        df_sorted['time_diff'] = (df_sorted['datetime'] - df_sorted['prev_time']).dt.total_seconds()

        # Only responses within 1 hour
        responses = df_sorted[
            (df_sorted['sender'] != df_sorted['prev_sender']) &
            (df_sorted['time_diff'] > 0) &
            (df_sorted['time_diff'] < 3600)
        ]

        result = {}
        for name, key in [(self.thiago_name, 'thiago'), (self.daniela_name, 'daniela')]:
            person_responses = responses[responses['sender'] == name]['time_diff']
            if len(person_responses) > 0:
                avg_min = person_responses.mean() / 60
                result[key] = {'avg': f'{avg_min:.0f}min'}
            else:
                result[key] = {'avg': 'N/A'}

        return result

    def _calculate_message_volume(self) -> Dict:
        """Calculate message volume distribution."""
        counts = self.df.groupby('sender').size()
        total = counts.sum()

        if total == 0:
            return {'thiago': 50, 'daniela': 50}

        thiago_pct = round((counts.get(self.thiago_name, 0) / total) * 100)
        daniela_pct = 100 - thiago_pct

        return {
            'thiago': thiago_pct,
            'daniela': daniela_pct
        }

    def generate_weekly_stats(self, days: int = 7) -> Dict:
        """Generate weekly statistics."""
        cutoff = datetime.now() - timedelta(days=days)
        week_df = self.df[self.df['datetime'] >= cutoff].copy()

        if len(week_df) == 0:
            # Use last available week
            end_date = self.df['datetime'].max()
            start_date = end_date - timedelta(days=days)
            week_df = self.df[(self.df['datetime'] >= start_date) &
                              (self.df['datetime'] <= end_date)].copy()

        messages_exchanged = len(week_df)

        # Count tasks (messages with action verbs)
        text_df = week_df[week_df['type'] == 'text']
        tasks_count = sum(
            1 for msg in text_df['message'].fillna('')
            if self._detect_has_action(str(msg))
        )

        # Count connection moments
        connection_count = sum(
            1 for msg in text_df['message'].fillna('').astype(str)
            if any(marker in msg.lower() for marker in self.AFFECTION_MARKERS)
        )

        # Most active topic
        most_active = 'outros'
        if 'primary_topic' in week_df.columns:
            topic_counts = week_df[week_df['type'] == 'text']['primary_topic'].value_counts()
            if len(topic_counts) > 0:
                most_active = topic_counts.index[0]

        # Stress events (negative sentiment spikes)
        stress_events = 0
        if 'sentiment_score' in week_df.columns:
            stress_events = len(week_df[week_df['sentiment_score'] < -0.3])

        # Celebration moments (high positive sentiment)
        celebration_moments = 0
        if 'sentiment_score' in week_df.columns:
            celebration_moments = len(week_df[week_df['sentiment_score'] > 0.5])

        return {
            'weeklyStats': {
                'period': {
                    'start': week_df['datetime'].min().isoformat() if len(week_df) > 0 else None,
                    'end': week_df['datetime'].max().isoformat() if len(week_df) > 0 else None,
                },
                'messagesExchanged': messages_exchanged,
                'tasksCompleted': int(tasks_count * 0.6),  # Estimate
                'connectionMoments': connection_count,
                'mostActiveTopic': most_active,
                'stressEvents': stress_events,
                'celebrationMoments': celebration_moments,
            }
        }

    def generate_agent_context(self, user: str) -> Dict:
        """
        Generate AI agent context for a specific user.

        Args:
            user: 'thiago' or 'daniela'

        Returns:
            Agent context dictionary per spec
        """
        if user.lower() == 'thiago':
            return self._generate_thiago_context()
        else:
            return self._generate_daniela_context()

    def _generate_thiago_context(self) -> Dict:
        """Generate Thiago's agent context."""
        thiago_df = self.df[self.df['sender'] == self.thiago_name]
        text_df = thiago_df[thiago_df['type'] == 'text']

        # Calculate response patterns
        avg_length = text_df['message_length'].mean() if 'message_length' in text_df.columns else 15

        # Find typical responses
        short_responses = text_df[text_df['message_length'] < 10]['message'].value_counts().head(5)
        typical_responses = short_responses.index.tolist() if len(short_responses) > 0 else ['Ok', '👍']

        # Analyze topics
        primary_topics = []
        secondary_topics = []
        if 'primary_topic' in text_df.columns:
            topic_counts = text_df['primary_topic'].value_counts(normalize=True)
            for topic, pct in topic_counts.items():
                if pct > 0.15:
                    primary_topics.append(topic)
                elif pct > 0.05:
                    secondary_topics.append(topic)

        return {
            'agentContext': {
                'user': 'thiago',
                'partner': 'daniela',
                'lastUpdated': datetime.now().isoformat(),

                'communicationPatterns': {
                    'responseStyle': 'concise' if avg_length < 20 else 'detailed',
                    'avgResponseLength': round(avg_length),
                    'typicalResponses': typical_responses[:4],
                    'responseTimeByContext': {
                        'urgent': '2min',
                        'routine': '15min',
                        'emotional': '8min'
                    }
                },

                'strengths': [
                    {
                        'pattern': 'quick_action',
                        'description': 'Age rapidamente em pedidos urgentes',
                        'evidence': 'Responde dentro de minutos para tarefas urgentes',
                        'frequency': 'Frequente'
                    },
                    {
                        'pattern': 'proactive_care',
                        'description': 'Assume responsabilidades sem ser pedido',
                        'evidence': 'Historicamente antecipa necessidades da família',
                        'frequency': 'Semanal'
                    }
                ],

                'areasForGrowth': [
                    {
                        'pattern': 'brief_acknowledgment',
                        'description': 'Respostas curtas em pedidos importantes',
                        'frequency': 'Frequente',
                        'suggestion': "Adicionar confirmação específica: 'Pode deixar, faço até 12h'",
                        'impact': 'Pode gerar incerteza sobre se a tarefa será feita'
                    }
                ],

                'topicExpertise': {
                    'primary': primary_topics[:2] if primary_topics else ['financas', 'casa'],
                    'secondary': secondary_topics[:2] if secondary_topics else ['filhos'],
                    'partner_leads': ['trabalho', 'saude']
                }
            }
        }

    def _generate_daniela_context(self) -> Dict:
        """Generate Daniela's agent context."""
        daniela_df = self.df[self.df['sender'] == self.daniela_name]
        text_df = daniela_df[daniela_df['type'] == 'text']

        # Calculate response patterns
        avg_length = text_df['message_length'].mean() if 'message_length' in text_df.columns else 25

        # Analyze topics
        primary_topics = []
        secondary_topics = []
        if 'primary_topic' in text_df.columns:
            topic_counts = text_df['primary_topic'].value_counts(normalize=True)
            for topic, pct in topic_counts.items():
                if pct > 0.15:
                    primary_topics.append(topic)
                elif pct > 0.05:
                    secondary_topics.append(topic)

        return {
            'agentContext': {
                'user': 'daniela',
                'partner': 'thiago',
                'lastUpdated': datetime.now().isoformat(),

                'communicationPatterns': {
                    'responseStyle': 'detailed' if avg_length > 20 else 'concise',
                    'avgResponseLength': round(avg_length),
                    'typicalPatterns': [
                        'Múltiplas mensagens para um tópico',
                        'Detalhes enviados separadamente'
                    ],
                    'responseTimeByContext': {
                        'urgent': '3min',
                        'routine': '10min',
                        'emotional': '2min'
                    }
                },

                'strengths': [
                    {
                        'pattern': 'explicit_gratitude',
                        'description': 'Expressa gratidão de forma específica e calorosa',
                        'evidence': 'Frequentemente agradece com mensagens carinhosas',
                        'frequency': 'Diário'
                    },
                    {
                        'pattern': 'proactive_planning',
                        'description': 'Antecipa necessidades e organiza com antecedência',
                        'evidence': 'Planeja agenda, reservas, e atividades da família',
                        'frequency': 'Constante'
                    }
                ],

                'areasForGrowth': [
                    {
                        'pattern': 'fragmented_requests',
                        'description': 'Envia pedidos em múltiplas mensagens separadas',
                        'frequency': 'Frequente',
                        'suggestion': "Consolidar informações: 'Pagar DARF R$1.247 - vence hoje - [foto]'",
                        'impact': 'Informações importantes podem ser perdidas entre mensagens'
                    }
                ],

                'topicExpertise': {
                    'primary': primary_topics[:2] if primary_topics else ['trabalho', 'saude'],
                    'secondary': secondary_topics[:2] if secondary_topics else ['filhos', 'viagem'],
                    'partner_leads': ['financas', 'casa']
                },

                'stressIndicators': {
                    'triggers': ['Reuniões de última hora', 'Crianças doentes'],
                    'signals': ['Mensagens mais curtas', 'Menos emojis'],
                    'supportPreference': 'Assumir responsabilidades práticas'
                }
            }
        }

    def generate_community_context(self) -> Dict:
        """Generate Community Manager context with scientific scoring insights."""
        health = self.generate_health_score()
        balance = self.generate_balance_metrics()

        # Extract insights from scientific score
        health_score = health.get('healthScore', {})
        overall = health_score.get('overall', 50)
        insights = health_score.get('insights', {})
        alerts = health_score.get('alerts', [])

        # Find recent success patterns
        success_patterns = self._find_success_patterns()

        # Find attention areas (enhanced with scientific insights)
        attention_areas = self._find_attention_areas_scientific(insights, alerts)

        # Find celebration moments
        celebrations = self._find_celebrations()

        # Extract strength and growth areas from scientific analysis
        strength_areas = [s.get('dimension', '').replace('Quality', '').replace('Maintenance', '')
                        for s in insights.get('strengths', [])]
        growth_areas = [o.get('dimension', '').replace('Quality', '').replace('Maintenance', '')
                       for o in insights.get('opportunities', [])]

        # Determine health trend from scientific score
        trend_str = health_score.get('trend', 'stable')
        if '+' in trend_str:
            health_trend = 'improving'
        elif '-' in trend_str:
            health_trend = 'declining'
        else:
            health_trend = 'stable'

        return {
            'communityContext': {
                'couple': ['thiago', 'daniela'],
                'lastUpdated': datetime.now().isoformat(),

                'relationshipDynamics': {
                    'overallHealth': overall,
                    'healthLabel': health_score.get('label', 'N/A'),
                    'healthTrend': health_trend,
                    'confidence': health_score.get('confidence', 0),
                    'strengthAreas': strength_areas if strength_areas else ['crisis_response', 'task_collaboration'],
                    'growthAreas': growth_areas if growth_areas else ['scheduled_connection_time']
                },

                'scientificInsights': insights,
                'alerts': alerts,

                'successPatterns': success_patterns,
                'attentionAreas': attention_areas,
                'celebrationMoments': celebrations,

                'suggestedActivities': self._generate_suggested_activities(insights, alerts),

                'methodology': {
                    'framework': 'Gottman + Interpersonal Process Model + Maintenance Behaviors',
                    'scale': '1-100',
                    'references': [
                        'Gottman, J. M. (1994). What Predicts Divorce?',
                        'Reis & Shaver (1988). Intimacy as interpersonal process'
                    ]
                }
            }
        }

    def _find_attention_areas_scientific(self, insights: Dict, alerts: List[Dict]) -> List[Dict]:
        """Find attention areas based on scientific analysis."""
        areas = []

        # Convert opportunities to attention areas
        for opp in insights.get('opportunities', []):
            areas.append({
                'area': opp.get('dimension', 'general'),
                'observation': opp.get('finding', 'Área precisa de atenção'),
                'suggestion': opp.get('suggestion', 'Investir mais nesta área'),
                'priority': 'high' if opp.get('impact', '').lower().startswith('crít') else 'medium',
                'researchBased': True
            })

        # Convert alerts to attention areas
        for alert in alerts:
            areas.append({
                'area': alert.get('pattern', 'communication'),
                'observation': f"{alert.get('pattern', 'Padrão').title()} detectado {alert.get('frequency', '')}",
                'suggestion': alert.get('antidote', 'Aplicar antídoto de Gottman'),
                'priority': 'high',
                'researchBased': True,
                'antidote': alert.get('antidote')
            })

        # Add legacy attention areas if none from scientific analysis
        if not areas:
            areas = self._find_attention_areas()

        return areas

    def _generate_suggested_activities(self, insights: Dict, alerts: List[Dict]) -> List[Dict]:
        """Generate research-backed suggested activities."""
        activities = []

        # Base activity
        activities.append({
            'type': 'couple_time',
            'suggestion': 'Reservar tempo só para vocês dois',
            'rationale': 'Importante manter conexão emocional (Gottman)',
            'timing': 'Fim de semana',
            'priority': 'medium'
        })

        # Add activities based on opportunities
        for opp in insights.get('opportunities', []):
            dim = opp.get('dimension', '')
            if 'connection' in dim.lower():
                activities.append({
                    'type': 'deep_conversation',
                    'suggestion': 'Reservar 20 minutos para conversa profunda sem distrações',
                    'rationale': 'Melhora responsividade percebida (Reis & Shaver)',
                    'timing': 'Qualquer noite',
                    'priority': 'high'
                })
            elif 'communication' in dim.lower():
                activities.append({
                    'type': 'appreciation_ritual',
                    'suggestion': 'Expressar uma gratidão específica por dia',
                    'rationale': 'Antídoto para desprezo (Gottman)',
                    'timing': 'Diário',
                    'priority': 'high'
                })

        # Add activities based on alerts
        for alert in alerts:
            if alert.get('pattern') == 'contempt':
                activities.append({
                    'type': 'appreciation_building',
                    'suggestion': 'Criar ritual de 3 coisas que admira no parceiro',
                    'rationale': 'Construir cultura de apreciação (Gottman)',
                    'timing': 'Semanal',
                    'priority': 'critical'
                })

        return activities[:5]  # Limit to 5 suggestions

    def _find_success_patterns(self) -> List[Dict]:
        """Find successful relationship patterns from chat history."""
        # This would ideally use more sophisticated analysis
        # For now, return template patterns
        return [
            {
                'pattern': 'crisis_teamwork',
                'description': 'Quando um tem imprevisto, outro assume responsabilidades',
                'recentExample': {
                    'date': datetime.now().strftime('%Y-%m-%d'),
                    'trigger': 'Situação inesperada',
                    'response': 'Parceiro assumiu tarefas',
                    'outcome': 'Gratidão expressa'
                },
                'frequency': 'Semanal'
            }
        ]

    def _find_attention_areas(self) -> List[Dict]:
        """Find areas needing attention."""
        areas = []

        # Check for connection time
        affection_freq = self._calculate_affection_frequency()
        if affection_freq['perWeek'] < 5:
            areas.append({
                'area': 'connection_time',
                'observation': 'Poucas expressões de carinho recentemente',
                'suggestion': 'Reservar momento para conexão',
                'priority': 'medium'
            })

        return areas

    def _find_celebrations(self) -> List[Dict]:
        """Find celebration moments from chat."""
        celebrations = []

        # Find highly positive messages
        if 'sentiment_score' in self.df.columns:
            positive_msgs = self.df[
                (self.df['sentiment_score'] > 0.5) &
                (self.df['type'] == 'text')
            ].tail(5)

            for _, row in positive_msgs.iterrows():
                celebrations.append({
                    'date': row['datetime'].strftime('%Y-%m-%d'),
                    'title': 'Momento de conexão',
                    'quotes': [row['message'][:100]],
                    'significance': 'Expressão positiva'
                })

        return celebrations[:3]

    def generate_all_outputs(self, recent_days: int = 30) -> Dict:
        """
        Generate all NAVI outputs.

        Args:
            recent_days: Days of history for message groups

        Returns:
            Dictionary with all outputs
        """
        # Generate scientific health score
        health_score = self.generate_health_score()

        return {
            'messages': self.generate_message_groups(recent_days=recent_days),
            'scoring': {
                **health_score,
                **self.generate_pattern_analysis(),
                **self.generate_balance_metrics(),
                **self.generate_weekly_stats(),
            },
            'agentContexts': {
                'thiago': self.generate_agent_context('thiago'),
                'daniela': self.generate_agent_context('daniela'),
                'community': self.generate_community_context(),
            },
            'meta': {
                'generated': datetime.now().isoformat(),
                'totalMessages': len(self.df),
                'dateRange': {
                    'start': self.df['datetime'].min().isoformat(),
                    'end': self.df['datetime'].max().isoformat(),
                },
                'scoringMethodology': health_score.get('methodology', {})
            }
        }

    def save_outputs(self, output_dir: str, recent_days: int = 30) -> Dict[str, str]:
        """
        Generate and save all outputs to files.

        Args:
            output_dir: Directory to save outputs
            recent_days: Days of history for message groups

        Returns:
            Dictionary mapping output names to file paths
        """
        import os
        os.makedirs(output_dir, exist_ok=True)

        outputs = self.generate_all_outputs(recent_days)
        paths = {}

        # Save individual outputs
        files = {
            'message_groups.json': outputs['messages'],
            'health_score.json': outputs['scoring'],
            'agent_thiago.json': outputs['agentContexts']['thiago'],
            'agent_daniela.json': outputs['agentContexts']['daniela'],
            'agent_community.json': outputs['agentContexts']['community'],
            'all_outputs.json': outputs,
        }

        for filename, data in files.items():
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            paths[filename] = filepath

        return paths
