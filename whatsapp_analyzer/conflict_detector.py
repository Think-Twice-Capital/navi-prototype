"""Conflict and Stress Detection Module for WhatsApp Chat Analysis"""

import re
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from collections import defaultdict


class ConflictDetector:
    """Detector for stress, conflict, and escalation patterns in Portuguese WhatsApp messages."""

    def __init__(self):
        """Initialize with Portuguese stress and conflict lexicons."""
        self.conflict_words = self._get_conflict_words()
        self.stress_words = self._get_stress_words()
        self.escalation_markers = self._get_escalation_markers()
        self.negative_words = self._get_negative_words()

    def _get_conflict_words(self) -> set:
        """Get words indicating conflict in Portuguese."""
        return {
            # Arguments
            'briga', 'brigar', 'brigando', 'brigamos', 'brigas', 'brigou',
            'discussao', 'discussão', 'discutir', 'discutindo', 'discutimos',
            'debate', 'desentendimento', 'desentender',
            # Anger
            'irritado', 'irritada', 'irritante', 'irritei', 'irritou',
            'nervoso', 'nervosa', 'nervo', 'nervosismo',
            'raiva', 'bravo', 'brava', 'furioso', 'furiosa',
            'puto', 'puta', 'putasso', 'putassa',
            # Hate
            'odio', 'ódio', 'odeio', 'odeia', 'odiar', 'detesto', 'detestar',
            'nojento', 'nojenta', 'nojo',
            # Problems
            'problema', 'problemas', 'complicado', 'complicada', 'dificil', 'difícil',
            'conflito', 'conflitos',
            # Blame
            'culpa', 'culpado', 'culpada', 'culpar',
            'errado', 'errada', 'erro', 'errei', 'errou',
            # Frustration
            'frustrado', 'frustrada', 'frustracao', 'frustração',
            'decepcionado', 'decepcionada', 'decepcao', 'decepção',
            # Betrayal
            'traicao', 'traição', 'traiu', 'mentira', 'mentiroso', 'mentirosa',
            # Insults (mild)
            'idiota', 'burro', 'burra', 'estupido', 'estúpido', 'estupida',
            'imbecil', 'ridiculo', 'ridículo', 'ridicula',
            # Separation
            'separar', 'separacao', 'terminar', 'acabou', 'fim',
            'chega', 'basta', 'cansei',
        }

    def _get_stress_words(self) -> set:
        """Get words indicating stress in Portuguese."""
        return {
            # Stress and anxiety
            'estresse', 'stress', 'estressado', 'estressada', 'estressar',
            'ansioso', 'ansiosa', 'ansiedade', 'angustia', 'angústia',
            'tenso', 'tensa', 'tensao', 'tensão',
            'nervoso', 'nervosa', 'agitado', 'agitada',
            # Worry
            'preocupado', 'preocupada', 'preocupar', 'preocupacao', 'preocupação',
            'aflito', 'aflita', 'aflicao', 'aflição',
            'apreensivo', 'apreensiva',
            # Exhaustion
            'cansado', 'cansada', 'cansaco', 'cansaço', 'exausto', 'exausta',
            'esgotado', 'esgotada', 'esgotamento',
            'sobrecarregado', 'sobrecarregada',
            # Overwhelm
            'nao aguento', 'não aguento', 'nao da', 'não dá',
            'nao consigo', 'não consigo', 'demais', 'pesado',
            # Pressure
            'pressao', 'pressão', 'pressionado', 'pressionada',
            'cobrado', 'cobrada', 'cobranca', 'cobrança',
            'urgente', 'urgencia', 'urgência', 'emergencia', 'emergência',
            'correria', 'loucura', 'caos', 'caotico', 'caótico',
            # Frustration
            'dificil', 'difícil', 'complicado', 'complicada',
            'impossivel', 'impossível', 'travado', 'travada',
            # Sadness overlap
            'triste', 'tristeza', 'desanimado', 'desanimada',
            'mal', 'pessimo', 'péssimo', 'pessima', 'péssima',
            # Health related stress
            'dor de cabeca', 'enxaqueca', 'insonia', 'insônia',
            'nao durmo', 'não durmo', 'sem dormir',
        }

    def _get_escalation_markers(self) -> set:
        """Get words that indicate escalation or intensity."""
        return {
            # Intensifiers
            'muito', 'muita', 'demais', 'extremamente', 'absurdamente',
            'completamente', 'totalmente', 'absolutamente',
            'super', 'mega', 'ultra', 'hiper',
            # Extremes
            'insuportavel', 'insuportável', 'inaceitavel', 'inaceitável',
            'inadmissivel', 'inadmissível', 'intoleravel', 'intolerável',
            'incrivel', 'incrível', 'absurdo', 'absurda',
            # Limits
            'limite', 'explodindo', 'explodir', 'pirar', 'pirando',
            'enlouquecer', 'enlouquecendo', 'surtar', 'surtando', 'surto',
            # Never/always
            'sempre', 'nunca', 'jamais', 'toda vez', 'cada vez',
            # Emphatic expressions
            'pelo amor', 'por favor', 'serio', 'sério', 'verdade',
            'juro', 'jura',
        }

    def _get_negative_words(self) -> set:
        """Get general negative words for context."""
        return {
            'nao', 'não', 'nem', 'nunca', 'ninguem', 'ninguém',
            'nada', 'nenhum', 'nenhuma', 'sem', 'mal',
            'pior', 'pessimo', 'péssimo', 'horrivel', 'horrível',
            'terrivel', 'terrível', 'ruim', 'ruins',
        }

    def _detect_caps_pattern(self, text: str) -> float:
        """Detect ALL CAPS usage as stress indicator."""
        if not text or len(text) < 3:
            return 0.0

        words = text.split()
        caps_words = [w for w in words if w.isupper() and len(w) > 1 and w.isalpha()]

        if len(words) == 0:
            return 0.0

        return len(caps_words) / len(words)

    def _detect_punctuation_pattern(self, text: str) -> float:
        """Detect excessive punctuation (!!! ???) as stress indicator."""
        if not text:
            return 0.0

        # Count sequences of repeated punctuation
        exclamation_pattern = re.findall(r'!{2,}', text)
        question_pattern = re.findall(r'\?{2,}', text)

        total_excessive = len(exclamation_pattern) + len(question_pattern)

        # Normalize by message length
        return min(total_excessive / max(1, len(text) / 50), 1.0)

    def _detect_short_angry_response(self, text: str, prev_messages: List[str] = None) -> float:
        """Detect short, potentially angry responses."""
        if not text:
            return 0.0

        words = text.split()
        word_count = len(words)

        # Very short messages with punctuation might indicate frustration
        if word_count <= 3:
            if '!' in text or '?' in text:
                return 0.5
            # Single word responses
            if word_count == 1:
                angry_responses = {'ok', 'tá', 'ta', 'sei', 'tanto', 'faz', 'foda', 'dane'}
                if text.lower().strip('.,!?') in angry_responses:
                    return 0.7
        return 0.0

    def analyze_text(self, text: str) -> Dict:
        """
        Analyze a single text message for conflict and stress.

        Args:
            text: Message text to analyze

        Returns:
            Dictionary with conflict_score, stress_score, escalation_level
        """
        if not text:
            return {
                'conflict_score': 0.0,
                'stress_score': 0.0,
                'escalation_level': 0.0,
                'is_stressful': False,
                'indicators': []
            }

        text_lower = text.lower()
        words = set(re.findall(r'\b\w+\b', text_lower))

        # Count matches
        conflict_matches = len(words.intersection(self.conflict_words))
        stress_matches = len(words.intersection(self.stress_words))
        escalation_matches = len(words.intersection(self.escalation_markers))
        negative_matches = len(words.intersection(self.negative_words))

        # Pattern-based detection
        caps_score = self._detect_caps_pattern(text)
        punctuation_score = self._detect_punctuation_pattern(text)
        short_angry_score = self._detect_short_angry_response(text)

        # Calculate scores (0-1 range)
        word_count = max(len(words), 1)

        conflict_score = min(conflict_matches / word_count * 3 + caps_score * 0.3, 1.0)
        stress_score = min(stress_matches / word_count * 3 + punctuation_score * 0.3, 1.0)
        escalation_level = min(
            escalation_matches / word_count * 2 +
            caps_score * 0.5 +
            punctuation_score * 0.5 +
            short_angry_score * 0.3,
            1.0
        )

        # Combine for overall stress assessment
        combined_score = (conflict_score * 0.4 + stress_score * 0.4 + escalation_level * 0.2)
        is_stressful = combined_score > 0.2

        # Collect indicators found
        indicators = []
        if conflict_matches > 0:
            indicators.append('conflict_words')
        if stress_matches > 0:
            indicators.append('stress_words')
        if escalation_matches > 0:
            indicators.append('escalation')
        if caps_score > 0.3:
            indicators.append('caps_usage')
        if punctuation_score > 0.3:
            indicators.append('excessive_punctuation')
        if short_angry_score > 0.3:
            indicators.append('short_response')

        return {
            'conflict_score': conflict_score,
            'stress_score': stress_score,
            'escalation_level': escalation_level,
            'is_stressful': is_stressful,
            'indicators': indicators
        }

    def analyze_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add conflict/stress detection columns to DataFrame.

        Args:
            df: DataFrame with 'message' column

        Returns:
            DataFrame with added conflict/stress columns
        """
        df = df.copy()

        # Initialize columns
        df['conflict_score'] = 0.0
        df['stress_score'] = 0.0
        df['escalation_level'] = 0.0
        df['is_stressful'] = False

        # Only analyze text messages
        text_mask = df['type'] == 'text'

        for idx in df[text_mask].index:
            message = df.loc[idx, 'message']
            result = self.analyze_text(message)

            df.loc[idx, 'conflict_score'] = result['conflict_score']
            df.loc[idx, 'stress_score'] = result['stress_score']
            df.loc[idx, 'escalation_level'] = result['escalation_level']
            df.loc[idx, 'is_stressful'] = result['is_stressful']

        return df

    def get_conflict_periods(self, df: pd.DataFrame, window_hours: int = 24) -> List[Dict]:
        """
        Identify high-conflict time periods.

        Args:
            df: DataFrame with conflict scores
            window_hours: Size of time window to analyze

        Returns:
            List of dictionaries describing conflict periods
        """
        text_df = df[df['type'] == 'text'].copy()

        if 'conflict_score' not in text_df.columns:
            return []

        # Group by date and calculate daily conflict levels
        daily = text_df.groupby('date').agg({
            'conflict_score': ['mean', 'max', 'sum'],
            'stress_score': ['mean', 'max', 'sum'],
            'is_stressful': 'sum'
        }).reset_index()

        daily.columns = ['date', 'conflict_mean', 'conflict_max', 'conflict_sum',
                         'stress_mean', 'stress_max', 'stress_sum', 'stressful_count']

        # Find high-conflict days (above 75th percentile)
        threshold = daily['conflict_mean'].quantile(0.75)
        high_conflict_days = daily[daily['conflict_mean'] > threshold]

        periods = []
        for _, row in high_conflict_days.iterrows():
            periods.append({
                'date': row['date'],
                'conflict_mean': row['conflict_mean'],
                'conflict_max': row['conflict_max'],
                'stress_mean': row['stress_mean'],
                'stressful_messages': int(row['stressful_count'])
            })

        return sorted(periods, key=lambda x: x['conflict_mean'], reverse=True)[:20]

    def get_stress_causes(self, df: pd.DataFrame, topic_analyzer=None) -> Dict:
        """
        Cross-reference conflicts with topics to identify stress causes.

        Args:
            df: DataFrame with conflict and topic columns
            topic_analyzer: Optional TopicAnalyzer instance

        Returns:
            Dictionary with stress cause analysis
        """
        text_df = df[(df['type'] == 'text') & (df['is_stressful'] == True)].copy()

        if len(text_df) == 0:
            return {
                'topic_breakdown': {},
                'temporal_patterns': {},
                'total_stressful': 0
            }

        results = {
            'total_stressful': len(text_df),
            'topic_breakdown': {},
            'temporal_patterns': {
                'by_day_of_week': {},
                'by_hour': {},
                'by_month': {}
            }
        }

        # Topic breakdown (if topic columns exist)
        if 'primary_topic' in text_df.columns:
            topic_counts = text_df['primary_topic'].value_counts()
            total = len(text_df)
            results['topic_breakdown'] = {
                topic: (count / total * 100)
                for topic, count in topic_counts.items()
            }

        # Temporal patterns
        if 'day_of_week_num' in text_df.columns:
            day_names = ['Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado', 'Domingo']
            day_counts = text_df['day_of_week_num'].value_counts()
            results['temporal_patterns']['by_day_of_week'] = {
                day_names[i]: count for i, count in day_counts.items()
            }

        if 'hour' in text_df.columns:
            hour_counts = text_df['hour'].value_counts().sort_index()
            results['temporal_patterns']['by_hour'] = hour_counts.to_dict()

        if 'datetime' in text_df.columns:
            text_df['month'] = text_df['datetime'].dt.month
            month_counts = text_df['month'].value_counts().sort_index()
            month_names = {
                1: 'Jan', 2: 'Fev', 3: 'Mar', 4: 'Abr', 5: 'Mai', 6: 'Jun',
                7: 'Jul', 8: 'Ago', 9: 'Set', 10: 'Out', 11: 'Nov', 12: 'Dez'
            }
            results['temporal_patterns']['by_month'] = {
                month_names[m]: count for m, count in month_counts.items()
            }

        return results

    def get_stress_by_sender(self, df: pd.DataFrame) -> Dict[str, Dict]:
        """
        Get stress statistics by sender.

        Args:
            df: DataFrame with stress columns

        Returns:
            Dictionary mapping sender to stress statistics
        """
        text_df = df[df['type'] == 'text']

        results = {}
        for sender in df['sender'].unique():
            sender_df = text_df[text_df['sender'] == sender]
            if len(sender_df) == 0:
                continue

            stressful_count = sender_df['is_stressful'].sum()
            total = len(sender_df)

            results[sender] = {
                'avg_conflict_score': sender_df['conflict_score'].mean(),
                'avg_stress_score': sender_df['stress_score'].mean(),
                'stressful_messages': int(stressful_count),
                'stressful_percentage': (stressful_count / total * 100) if total > 0 else 0,
                'max_conflict_score': sender_df['conflict_score'].max(),
                'max_stress_score': sender_df['stress_score'].max(),
            }

        return results

    def get_stress_over_time(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Get monthly stress/conflict trends.

        Args:
            df: DataFrame with stress columns

        Returns:
            DataFrame with monthly stress data
        """
        text_df = df[df['type'] == 'text'].copy()
        text_df['month_period'] = text_df['datetime'].dt.to_period('M')

        monthly = text_df.groupby('month_period').agg({
            'conflict_score': 'mean',
            'stress_score': 'mean',
            'escalation_level': 'mean',
            'is_stressful': 'sum'
        }).reset_index()

        monthly.columns = ['month_period', 'avg_conflict', 'avg_stress',
                           'avg_escalation', 'stressful_count']

        return monthly.sort_values('month_period')

    def get_stress_by_topic_and_day(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Get stress distribution by topic and day of week (for heatmap).

        Args:
            df: DataFrame with stress and topic columns

        Returns:
            DataFrame suitable for heatmap visualization
        """
        text_df = df[(df['type'] == 'text') & (df['is_stressful'] == True)].copy()

        if 'primary_topic' not in text_df.columns or len(text_df) == 0:
            return pd.DataFrame()

        # Cross-tabulate topic and day of week
        day_names = ['Segunda', 'Terca', 'Quarta', 'Quinta', 'Sexta', 'Sabado', 'Domingo']

        # Create pivot table
        pivot = pd.crosstab(text_df['primary_topic'], text_df['day_of_week_num'])

        # Rename columns to day names
        pivot.columns = [day_names[i] for i in pivot.columns]

        return pivot
