"""
Scientific Scoring Module

Implements a validated 4-dimension relationship health scoring framework
based on academic research from relationship science.

Framework Dimensions:
1. Connection Quality (30%) - Interpersonal Process Model
2. Relationship Maintenance (25%) - Stafford & Canary
3. Communication Health (25%) - Gottman's research
4. Partnership Dynamics (20%) - Equity Theory

LLM Enhancement (Phase 1):
- Optional Claude Opus 4.5 integration for maximum quality baseline
- LLM-powered response quality assessment (beyond word count)
- LLM-powered vulnerability depth scoring
- Cost tracking for future optimization

References:
- Gottman, J. M. (1994). What Predicts Divorce?
- Reis, H. T., & Shaver, P. (1988). Intimacy as an interpersonal process
- Stafford, L., & Canary, D. J. (1991). Maintenance strategies
- Funk, J. L., & Rogge, R. D. (2007). CSI
- Spanier, G. B. (1976). DAS
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING, Any
from dataclasses import dataclass, field
from collections import defaultdict
import pandas as pd
import numpy as np

from .pattern_detectors import (
    RelationshipPatternAnalyzer,
    PatternSummary,
    GottmanPatternDetector,
    PositivePatternDetector,
    ResponsivenessAnalyzer
)

if TYPE_CHECKING:
    from .llm_analyzer import LLMRelationshipAnalyzer


@dataclass
class DimensionScore:
    """Score for a single dimension with components."""
    score: float  # 0-100
    components: Dict[str, Dict] = field(default_factory=dict)
    insights: List[str] = field(default_factory=list)


@dataclass
class HealthScoreResult:
    """Complete health score result."""
    overall: float  # 0-100
    label: str  # Portuguese label
    label_en: str  # English label
    confidence: float  # 0-1
    trend: str  # e.g., "+3 vs last month"

    dimensions: Dict[str, DimensionScore] = field(default_factory=dict)
    insights: Dict = field(default_factory=dict)
    alerts: List[Dict] = field(default_factory=list)

    generated: str = field(default_factory=lambda: datetime.now().isoformat())


class ScientificHealthScorer:
    """
    Scientific health scoring using validated academic frameworks.

    Scale: 1-100 (granular)

    Dimensions:
    - Connection Quality (30%): Responsiveness, emotional expression, reciprocity
    - Relationship Maintenance (25%): Positivity, assurances, task-sharing, understanding
    - Communication Health (25%): Gentle startup, repairs, absence of contempt, engagement
    - Partnership Dynamics (20%): Equity, coordination, shared meaning
    """

    # Score labels (PT-BR and EN)
    SCORE_LABELS = {
        (85, 100): ('Florescente', 'Flourishing'),
        (70, 84): ('Saudável', 'Healthy'),
        (55, 69): ('Estável', 'Stable'),
        (40, 54): ('Atenção', 'Attention'),
        (25, 39): ('Preocupante', 'Concerning'),
        (0, 24): ('Crítico', 'Critical'),
    }

    # Dimension weights
    DIMENSION_WEIGHTS = {
        'connection_quality': 0.30,
        'relationship_maintenance': 0.25,
        'communication_health': 0.25,
        'partnership_dynamics': 0.20,
    }

    # Temporal weights
    TEMPORAL_WEIGHTS = {
        'recent_30d': 0.50,
        'medium_90d': 0.30,
        'longterm': 0.20,
    }

    def __init__(self, df: pd.DataFrame,
                 sender_col: str = 'sender',
                 message_col: str = 'message',
                 datetime_col: str = 'datetime',
                 person_a: str = None,
                 person_b: str = None,
                 llm_analyzer: 'LLMRelationshipAnalyzer' = None,
                 use_llm: bool = True):
        """
        Initialize scorer with chat data.

        Args:
            df: DataFrame with messages
            sender_col: Column name for sender
            message_col: Column name for message text
            datetime_col: Column name for timestamp
            person_a: First person's name
            person_b: Second person's name
            llm_analyzer: Optional LLM analyzer for enhanced scoring
            use_llm: If True and llm_analyzer provided, use LLM for quality assessments
        """
        self.df = df.copy()
        self.sender_col = sender_col
        self.message_col = message_col
        self.datetime_col = datetime_col

        # LLM enhancement
        self.llm_analyzer = llm_analyzer
        self.use_llm = use_llm and llm_analyzer is not None

        # Infer person names if not provided
        if person_a is None or person_b is None:
            senders = df[sender_col].unique()
            if len(senders) >= 2:
                self.person_a = senders[0]
                self.person_b = senders[1]
            else:
                self.person_a = senders[0] if len(senders) > 0 else 'Person A'
                self.person_b = 'Person B'
        else:
            self.person_a = person_a
            self.person_b = person_b

        # Initialize pattern analyzers (with LLM if enabled)
        self.pattern_analyzer = RelationshipPatternAnalyzer(
            llm_analyzer=llm_analyzer,
            use_llm=use_llm
        )
        self.positive_detector = PositivePatternDetector(
            llm_analyzer=llm_analyzer,
            use_llm=use_llm
        )
        self.responsiveness_analyzer = ResponsivenessAnalyzer()
        self.gottman_detector = GottmanPatternDetector(
            llm_analyzer=llm_analyzer,
            use_llm=use_llm
        )

        # Cache for computed values
        self._pattern_cache = {}

        # Store LLM analysis results
        self._llm_response_qualities: List[Dict] = []
        self._llm_vulnerability_depths: List[Dict] = []

    def _get_temporal_dfs(self) -> Dict[str, pd.DataFrame]:
        """Split DataFrame by temporal windows."""
        now = self.df[self.datetime_col].max()
        day_30 = now - timedelta(days=30)
        day_90 = now - timedelta(days=90)

        return {
            'recent_30d': self.df[self.df[self.datetime_col] >= day_30],
            'medium_90d': self.df[
                (self.df[self.datetime_col] >= day_90) &
                (self.df[self.datetime_col] < day_30)
            ],
            'longterm': self.df[self.df[self.datetime_col] < day_90],
            'all': self.df
        }

    def _get_label(self, score: float) -> Tuple[str, str]:
        """Get Portuguese and English labels for a score."""
        for (low, high), (pt, en) in self.SCORE_LABELS.items():
            if low <= score <= high:
                return pt, en
        return 'N/A', 'N/A'

    def calculate_connection_quality(self, df: pd.DataFrame = None) -> DimensionScore:
        """
        Calculate Connection Quality dimension (30%).

        Based on Interpersonal Process Model (Reis & Shaver).

        Components:
        - Responsiveness (40%): Quality of responses to partner
        - Emotional Expression (30%): Self-disclosure depth
        - Reciprocity (30%): Balance in emotional exchange
        """
        if df is None:
            df = self.df

        text_df = df[df['type'] == 'text'].copy() if 'type' in df.columns else df.copy()
        if len(text_df) == 0:
            return DimensionScore(score=50.0)

        # Prepare data
        text_df = text_df.sort_values(self.datetime_col)
        text_df['prev_message'] = text_df[self.message_col].shift(1)
        text_df['prev_sender'] = text_df[self.sender_col].shift(1)
        text_df['prev_time'] = text_df[self.datetime_col].shift(1)
        text_df['is_response'] = text_df[self.sender_col] != text_df['prev_sender']

        # Component 1: Responsiveness (40%)
        responsiveness_score = self._calc_responsiveness(text_df)

        # Component 2: Emotional Expression (30%)
        emotional_score = self._calc_emotional_expression(text_df)

        # Component 3: Reciprocity (30%)
        reciprocity_score = self._calc_reciprocity(text_df)

        # Calculate weighted score
        total_score = (
            responsiveness_score['score'] * 0.40 +
            emotional_score['score'] * 0.30 +
            reciprocity_score['score'] * 0.30
        )

        insights = []
        if responsiveness_score['score'] < 60:
            insights.append('Respostas poderiam ser mais elaboradas')
        if emotional_score['score'] >= 70:
            insights.append('Boa expressão emocional')
        if reciprocity_score['score'] >= 70:
            insights.append('Troca emocional equilibrada')

        return DimensionScore(
            score=round(total_score, 1),
            components={
                'responsiveness': responsiveness_score,
                'emotionalExpression': emotional_score,
                'reciprocity': reciprocity_score,
            },
            insights=insights
        )

    def _calc_responsiveness(self, df: pd.DataFrame) -> Dict:
        """
        Calculate responsiveness score.

        With LLM enhancement:
        - Assesses actual empathy, validation, and caring
        - Quality != word count ("Entendo, quer conversar?" can be high quality)
        - Based on Reis & Shaver's Interpersonal Process Model
        """
        responses = df[df['is_response'] == True].copy()
        if len(responses) == 0:
            return {'score': 50.0, 'insight': 'Dados insuficientes'}

        # Calculate response depth for each response
        response_scores = []
        llm_scores = []

        for _, row in responses.iterrows():
            text = str(row.get(self.message_col, ''))
            prev_text = str(row.get('prev_message', ''))
            prev_time = row.get('prev_time')
            curr_time = row.get(self.datetime_col)

            if pd.isna(prev_time) or pd.isna(curr_time):
                continue

            response_time = (curr_time - prev_time).total_seconds() / 60

            # Basic regex-based quality
            basic_quality = self.responsiveness_analyzer.calculate_response_quality(
                prev_text, text, response_time
            )

            # LLM-enhanced quality (if enabled and responding to emotional content)
            if self.use_llm and self.responsiveness_analyzer.is_emotional_message(prev_text):
                llm_quality = self.llm_analyzer.assess_response_quality(prev_text, text)

                # Store for analysis
                self._llm_response_qualities.append({
                    'original': prev_text[:50],
                    'response': text[:50],
                    'regex_score': basic_quality['score'],
                    'llm_score': llm_quality.overall_quality,
                    'understanding': llm_quality.understanding_score,
                    'validation': llm_quality.validation_score,
                    'caring': llm_quality.caring_score,
                    'is_dismissive': llm_quality.is_dismissive,
                })

                # Use LLM score for emotional responses (more accurate)
                response_scores.append(llm_quality.overall_quality)
                llm_scores.append(llm_quality.overall_quality)
            else:
                response_scores.append(basic_quality['score'])

        if not response_scores:
            return {'score': 50.0, 'insight': 'Dados insuficientes'}

        avg_score = np.mean(response_scores)

        # Enhanced insight with LLM data
        if llm_scores:
            avg_llm = np.mean(llm_scores)
            if avg_llm >= 80:
                insight = 'Respostas empáticas e validadoras'
            elif avg_llm >= 60:
                insight = 'Boa responsividade emocional'
            elif avg_llm >= 40:
                insight = 'Respostas adequadas, podem melhorar em validação'
            else:
                insight = 'Respostas poderiam ser mais empáticas e validadoras'

            return {
                'score': round(avg_score, 1),
                'insight': insight,
                'llmAssessed': len(llm_scores),
                'avgLlmScore': round(avg_llm, 1),
            }

        # Non-LLM insight
        if avg_score >= 80:
            insight = 'Respostas atenciosas e elaboradas'
        elif avg_score >= 60:
            insight = 'Respostas adequadas na maioria das vezes'
        else:
            insight = 'Respostas poderiam ser mais elaboradas'

        return {'score': round(avg_score, 1), 'insight': insight}

    def _calc_emotional_expression(self, df: pd.DataFrame) -> Dict:
        """
        Calculate emotional expression score.

        With LLM enhancement:
        - Assesses actual vulnerability depth (surface/moderate/deep)
        - Evaluates if disclosure invites reciprocity
        - Not all emotional disclosure is equal in intimacy value
        """
        text_df = df.copy()

        # Count emotional vocabulary usage (regex-based)
        emotional_patterns = PositivePatternDetector.DISCLOSURE_PATTERNS
        emotional_re = [re.compile(p, re.IGNORECASE) for p in emotional_patterns]

        emotional_count = 0
        emotional_messages = []
        total_messages = len(text_df)

        for idx, row in text_df.iterrows():
            text = str(row.get(self.message_col, ''))
            for pattern in emotional_re:
                if pattern.search(text):
                    emotional_count += 1
                    emotional_messages.append((idx, text))
                    break

        # Calculate percentage and base score
        if total_messages == 0:
            return {'score': 50.0, 'insight': 'Dados insuficientes'}

        emotional_rate = emotional_count / total_messages

        # Baseline: 5% emotional messages is healthy
        base_score = min(100, (emotional_rate / 0.05) * 70 + 30)

        # LLM-enhanced vulnerability depth assessment
        depth_scores = []
        if self.use_llm and emotional_messages:
            # Sample up to 20 emotional messages for LLM analysis
            sample_messages = emotional_messages[:20]

            for idx, text in sample_messages:
                # Get context from nearby messages
                context = self._get_message_context(text_df, idx)

                depth_result = self.llm_analyzer.analyze_vulnerability_depth(text, context)

                # Convert depth level to score
                depth_level_scores = {'surface': 30, 'moderate': 60, 'deep': 100}
                depth_scores.append(depth_result.depth_score)

                # Store for analysis
                self._llm_vulnerability_depths.append({
                    'text': text[:50],
                    'depth_level': depth_result.depth_level,
                    'depth_score': depth_result.depth_score,
                    'invites_reciprocity': depth_result.invites_reciprocity,
                    'topics': depth_result.topics,
                })

        # Count unique emotional words for vocabulary diversity
        emotional_words = set()
        for _, row in text_df.iterrows():
            text = str(row.get(self.message_col, '')).lower()
            words = ['sinto', 'medo', 'feliz', 'triste', 'ansioso', 'preocupado',
                     'nervoso', 'amor', 'saudade', 'alegria', 'frustrado']
            for word in words:
                if word in text:
                    emotional_words.add(word)

        diversity = len(emotional_words)

        # Calculate final score
        if depth_scores:
            avg_depth = np.mean(depth_scores)
            # Blend base score with depth quality
            final_score = (base_score * 0.4) + (avg_depth * 0.6)

            # Enhanced insight based on depth
            deep_count = sum(1 for d in self._llm_vulnerability_depths if d['depth_level'] == 'deep')
            if avg_depth >= 70:
                insight = 'Vulnerabilidade profunda e significativa'
            elif avg_depth >= 50:
                insight = 'Boa profundidade emocional'
            else:
                insight = 'Expressão emocional presente, pode aprofundar'

            return {
                'score': round(final_score, 1),
                'insight': insight,
                'diversityCount': diversity,
                'llmAssessed': len(depth_scores),
                'avgDepthScore': round(avg_depth, 1),
                'deepDisclosures': deep_count,
            }

        # Non-LLM insight
        if diversity >= 6:
            insight = 'Vocabulário emocional diverso'
        elif diversity >= 3:
            insight = 'Boa expressão emocional'
        else:
            insight = 'Expressão emocional limitada'

        return {
            'score': round(base_score, 1),
            'insight': insight,
            'diversityCount': diversity
        }

    def _get_message_context(self, df: pd.DataFrame, idx: int, window: int = 3) -> str:
        """Get context messages around a specific index."""
        try:
            # Get position in sorted dataframe
            sorted_df = df.sort_values(self.datetime_col)
            position = sorted_df.index.get_loc(idx)

            # Get previous messages
            start = max(0, position - window)
            context_df = sorted_df.iloc[start:position]

            context_msgs = []
            for _, row in context_df.iterrows():
                sender = row.get(self.sender_col, 'Unknown')
                msg = str(row.get(self.message_col, ''))[:100]
                context_msgs.append(f"{sender}: {msg}")

            return '\n'.join(context_msgs)
        except Exception:
            return ""

    def _calc_reciprocity(self, df: pd.DataFrame) -> Dict:
        """Calculate emotional reciprocity score."""
        # Count emotional expressions by each person
        emotional_by_person = defaultdict(int)

        emotional_patterns = (
            PositivePatternDetector.AFFECTION_PATTERNS +
            PositivePatternDetector.DISCLOSURE_PATTERNS
        )
        emotional_re = [re.compile(p, re.IGNORECASE) for p in emotional_patterns]

        for _, row in df.iterrows():
            text = str(row.get(self.message_col, ''))
            sender = row.get(self.sender_col)
            for pattern in emotional_re:
                if pattern.search(text):
                    emotional_by_person[sender] += 1
                    break

        counts = list(emotional_by_person.values())
        if len(counts) < 2 or sum(counts) == 0:
            return {'score': 50.0, 'insight': 'Dados insuficientes'}

        # Calculate balance (100 = perfect, 0 = one-sided)
        total = sum(counts)
        min_count = min(counts)
        max_count = max(counts)

        if max_count == 0:
            balance = 100
        else:
            balance = (min_count / max_count) * 100

        # Score: perfect balance = 100, imbalanced = lower
        score = 50 + (balance / 2)

        if balance >= 80:
            insight = 'Troca emocional equilibrada'
        elif balance >= 50:
            insight = 'Moderada reciprocidade emocional'
        else:
            insight = 'Expressão emocional desequilibrada'

        return {
            'score': round(score, 1),
            'insight': insight,
            'balance': f'{round(min_count/total*100)}/{round(max_count/total*100)}' if total > 0 else '50/50'
        }

    def calculate_relationship_maintenance(self, df: pd.DataFrame = None) -> DimensionScore:
        """
        Calculate Relationship Maintenance dimension (25%).

        Based on Stafford & Canary's Maintenance Behaviors.

        Components:
        - Positivity (35%): Cheerful, optimistic interactions
        - Assurances (25%): Expressions of commitment/love
        - Task Sharing (25%): Collaborative coordination
        - Understanding (15%): Empathy and validation
        """
        if df is None:
            df = self.df

        text_df = df[df['type'] == 'text'].copy() if 'type' in df.columns else df.copy()
        if len(text_df) == 0:
            return DimensionScore(score=50.0)

        # Component 1: Positivity (35%) - Gottman's 5:1 ratio
        positivity = self._calc_positivity(text_df)

        # Component 2: Assurances (25%)
        assurances = self._calc_assurances(text_df)

        # Component 3: Task Sharing (25%)
        task_sharing = self._calc_task_sharing(text_df)

        # Component 4: Understanding (15%)
        understanding = self._calc_understanding(text_df)

        # Calculate weighted score
        total_score = (
            positivity['score'] * 0.35 +
            assurances['score'] * 0.25 +
            task_sharing['score'] * 0.25 +
            understanding['score'] * 0.15
        )

        insights = []
        if positivity.get('ratio', 0) >= 5:
            insights.append('Proporção positivo/negativo excelente')
        if assurances['score'] >= 70:
            insights.append('Fortes expressões de compromisso')
        if task_sharing['score'] >= 70:
            insights.append('Boa distribuição de tarefas')

        return DimensionScore(
            score=round(total_score, 1),
            components={
                'positivity': positivity,
                'assurances': assurances,
                'taskSharing': task_sharing,
                'understanding': understanding,
            },
            insights=insights
        )

    def _calc_positivity(self, df: pd.DataFrame) -> Dict:
        """Calculate positivity score using Gottman's ratio."""
        summary = self.pattern_analyzer.analyze_conversation(
            df,
            sender_col=self.sender_col,
            message_col=self.message_col,
            datetime_col=self.datetime_col
        )

        ratio = summary.positive_ratio
        total_positive = summary.total_positive
        total_negative = summary.total_negative

        # Score based on ratio (5:1 = 100, 1:1 = 40, <1:1 = lower)
        if ratio >= 5.0:
            score = 100
        elif ratio >= 3.0:
            score = 70 + (ratio - 3.0) * 15  # 70-100
        elif ratio >= 1.0:
            score = 40 + (ratio - 1.0) * 15  # 40-70
        else:
            score = max(10, ratio * 40)  # 10-40

        return {
            'score': round(score, 1),
            'ratio': f'{ratio:.1f}:1',
            'positive': total_positive,
            'negative': total_negative,
            'insight': f'Proporção {ratio:.1f}:1 (meta: 5:1)'
        }

    def _calc_assurances(self, df: pd.DataFrame) -> Dict:
        """Calculate commitment assurances score."""
        assurance_patterns = PositivePatternDetector.ASSURANCE_PATTERNS
        affection_patterns = PositivePatternDetector.AFFECTION_PATTERNS

        all_patterns = assurance_patterns + affection_patterns
        patterns_re = [re.compile(p, re.IGNORECASE) for p in all_patterns]

        count = 0
        for _, row in df.iterrows():
            text = str(row.get(self.message_col, ''))
            for pattern in patterns_re:
                if pattern.search(text):
                    count += 1
                    break

        # Calculate per week
        total_days = (df[self.datetime_col].max() - df[self.datetime_col].min()).days
        weeks = max(total_days / 7, 1)
        per_week = count / weeks

        # Score: 10+ per week = 100, 5 = 70, 2 = 40
        if per_week >= 10:
            score = 100
        elif per_week >= 5:
            score = 70 + (per_week - 5) * 6
        elif per_week >= 2:
            score = 40 + (per_week - 2) * 10
        else:
            score = max(20, per_week * 20)

        return {
            'score': round(score, 1),
            'perWeek': round(per_week, 1),
            'insight': f'{round(per_week, 1)} expressões de compromisso/semana'
        }

    def _calc_task_sharing(self, df: pd.DataFrame) -> Dict:
        """Calculate task sharing balance score."""
        action_verbs = {
            'pagar', 'fazer', 'comprar', 'ligar', 'marcar', 'resolver',
            'buscar', 'levar', 'enviar', 'agendar', 'confirmar', 'cuidar'
        }

        task_by_person = defaultdict(int)

        for _, row in df.iterrows():
            text = str(row.get(self.message_col, '')).lower()
            sender = row.get(self.sender_col)
            if any(verb in text for verb in action_verbs):
                task_by_person[sender] += 1

        counts = list(task_by_person.values())
        if len(counts) < 2 or sum(counts) == 0:
            return {'score': 70.0, 'balance': '50/50', 'insight': 'Dados insuficientes'}

        total = sum(counts)
        min_count = min(counts)
        max_count = max(counts)

        # Calculate balance percentage
        min_pct = round(min_count / total * 100)
        max_pct = round(max_count / total * 100)

        # Score: 50/50 = 100, 60/40 = 80, 70/30 = 60
        balance_diff = abs(min_pct - 50)
        score = 100 - (balance_diff * 1.5)
        score = max(30, score)

        if balance_diff <= 10:
            insight = 'Distribuição equilibrada de tarefas'
        elif balance_diff <= 20:
            insight = 'Moderada assimetria nas tarefas'
        else:
            insight = 'Tarefas concentradas em uma pessoa'

        return {
            'score': round(score, 1),
            'balance': f'{min_pct}/{max_pct}',
            'insight': insight
        }

    def _calc_understanding(self, df: pd.DataFrame) -> Dict:
        """Calculate understanding/validation score."""
        understanding_patterns = PositivePatternDetector.UNDERSTANDING_PATTERNS
        support_patterns = PositivePatternDetector.SUPPORT_PATTERNS

        all_patterns = understanding_patterns + support_patterns
        patterns_re = [re.compile(p, re.IGNORECASE) for p in all_patterns]

        count = 0
        for _, row in df.iterrows():
            text = str(row.get(self.message_col, ''))
            for pattern in patterns_re:
                if pattern.search(text):
                    count += 1
                    break

        total = len(df)
        rate = count / total if total > 0 else 0

        # Score: 5% validation = 100, 2% = 60, 1% = 40
        score = min(100, (rate / 0.05) * 100)
        score = max(30, score)

        if rate >= 0.05:
            insight = 'Forte padrão de validação'
        elif rate >= 0.02:
            insight = 'Validação moderada'
        else:
            insight = 'Mais validação poderia fortalecer conexão'

        return {
            'score': round(score, 1),
            'rate': f'{rate*100:.1f}%',
            'insight': insight
        }

    def calculate_communication_health(self, df: pd.DataFrame = None) -> DimensionScore:
        """
        Calculate Communication Health dimension (25%).

        Based on Gottman's Four Horsemen (inverse).

        Components:
        - Gentle Startup (30%): Non-critical request framing
        - Repair Attempts (30%): Conflict de-escalation
        - Absence of Contempt (25%): Respect in disagreements
        - Engagement (15%): Active participation
        """
        if df is None:
            df = self.df

        text_df = df[df['type'] == 'text'].copy() if 'type' in df.columns else df.copy()
        if len(text_df) == 0:
            return DimensionScore(score=50.0)

        # Analyze patterns
        summary = self.pattern_analyzer.analyze_conversation(
            text_df,
            sender_col=self.sender_col,
            message_col=self.message_col,
            datetime_col=self.datetime_col
        )

        # Component 1: Gentle Startup (30%)
        gentle_startup = self._calc_gentle_startup(summary)

        # Component 2: Repair Attempts (30%)
        repairs = self._calc_repair_attempts(summary)

        # Component 3: Absence of Contempt (25%)
        no_contempt = self._calc_absence_contempt(summary)

        # Component 4: Engagement (15%)
        engagement = self._calc_engagement(text_df)

        # Calculate weighted score
        total_score = (
            gentle_startup['score'] * 0.30 +
            repairs['score'] * 0.30 +
            no_contempt['score'] * 0.25 +
            engagement['score'] * 0.15
        )

        insights = []
        if repairs['score'] >= 70:
            insights.append('Bons padrões de reparação')
        if no_contempt['score'] >= 80:
            insights.append('Comunicação respeitosa')

        return DimensionScore(
            score=round(total_score, 1),
            components={
                'gentleStartup': gentle_startup,
                'repairAttempts': repairs,
                'absenceOfContempt': no_contempt,
                'engagement': engagement,
            },
            insights=insights
        )

    def _calc_gentle_startup(self, summary: PatternSummary) -> Dict:
        """Calculate gentle startup score (inverse of criticism)."""
        criticism_count = summary.four_horsemen_counts.get('criticism', 0)

        # Score decreases with criticism
        # 0 criticisms = 100, 3 = 70, 5+ = 40
        if criticism_count == 0:
            score = 100
        elif criticism_count <= 2:
            score = 100 - (criticism_count * 15)
        elif criticism_count <= 5:
            score = 70 - ((criticism_count - 2) * 10)
        else:
            score = max(20, 40 - ((criticism_count - 5) * 5))

        if score >= 80:
            insight = 'Pedidos feitos de forma gentil'
        elif score >= 60:
            insight = 'Alguns padrões de crítica detectados'
        else:
            insight = 'Muita crítica - usar "Eu sinto..." em vez de "Você é..."'

        return {
            'score': round(score, 1),
            'criticismCount': criticism_count,
            'insight': insight
        }

    def _calc_repair_attempts(self, summary: PatternSummary) -> Dict:
        """Calculate repair attempts score."""
        repair_count = summary.positive_counts.get('repair_attempt', 0)
        total_negative = summary.total_negative

        # Calculate success rate if there are conflicts
        if total_negative > 0:
            repair_rate = repair_count / total_negative
            success_rate = min(100, repair_rate * 100)
        else:
            # No conflicts = base score
            success_rate = 80 if repair_count > 0 else 70

        # Score based on repair presence and rate
        if repair_count >= 5:
            score = min(100, 70 + (repair_count * 3))
        elif repair_count >= 2:
            score = 60 + (repair_count * 5)
        elif repair_count >= 1:
            score = 50 + (repair_count * 10)
        else:
            score = 50

        if score >= 80:
            insight = 'Fortes tentativas de reparação'
        elif score >= 60:
            insight = 'Reparações presentes'
        else:
            insight = 'Mais reparações poderiam ajudar na resolução de conflitos'

        return {
            'score': round(score, 1),
            'count': repair_count,
            'successRate': f'{round(success_rate)}%',
            'insight': insight
        }

    def _calc_absence_contempt(self, summary: PatternSummary) -> Dict:
        """Calculate absence of contempt score (most destructive horseman)."""
        contempt_count = summary.four_horsemen_counts.get('contempt', 0)

        # Any contempt is significant
        if contempt_count == 0:
            score = 100
            insight = 'Nenhum sinal de desprezo'
        elif contempt_count == 1:
            score = 70
            insight = 'Pouco desprezo detectado'
        elif contempt_count <= 3:
            score = 50
            insight = 'Desprezo presente - atenção recomendada'
        else:
            score = max(20, 30 - (contempt_count * 2))
            insight = 'Desprezo frequente - construir cultura de apreciação'

        return {
            'score': round(score, 1),
            'contemptCount': contempt_count,
            'insight': insight
        }

    def _calc_engagement(self, df: pd.DataFrame) -> Dict:
        """Calculate engagement score (inverse of stonewalling)."""
        # Calculate average response rate
        df_sorted = df.sort_values(self.datetime_col)
        df_sorted['prev_sender'] = df_sorted[self.sender_col].shift(1)
        df_sorted['prev_time'] = df_sorted[self.datetime_col].shift(1)

        responses = df_sorted[df_sorted[self.sender_col] != df_sorted['prev_sender']].copy()

        if len(responses) == 0:
            return {'score': 70.0, 'insight': 'Dados insuficientes'}

        # Calculate response times
        responses['response_time'] = (
            responses[self.datetime_col] - responses['prev_time']
        ).dt.total_seconds() / 60

        # Filter to reasonable response times (< 24 hours)
        valid_responses = responses[responses['response_time'] < 1440]

        if len(valid_responses) == 0:
            return {'score': 60.0, 'insight': 'Dados insuficientes'}

        avg_response = valid_responses['response_time'].mean()

        # Score based on response time
        # < 10min = 100, 30min = 80, 60min = 60, 2h+ = 40
        if avg_response < 10:
            score = 100
        elif avg_response < 30:
            score = 100 - ((avg_response - 10) * 1)
        elif avg_response < 60:
            score = 80 - ((avg_response - 30) * 0.67)
        elif avg_response < 120:
            score = 60 - ((avg_response - 60) * 0.33)
        else:
            score = max(30, 40 - ((avg_response - 120) * 0.05))

        return {
            'score': round(score, 1),
            'avgResponseMin': round(avg_response, 1),
            'insight': f'Tempo médio de resposta: {round(avg_response)}min'
        }

    def calculate_partnership_dynamics(self, df: pd.DataFrame = None) -> DimensionScore:
        """
        Calculate Partnership Dynamics dimension (20%).

        Based on Equity Theory and Interdependence.

        Components:
        - Equity (40%): Fair distribution of effort
        - Coordination (30%): Logistical efficiency
        - Shared Meaning (30%): Joint goals and values
        """
        if df is None:
            df = self.df

        text_df = df[df['type'] == 'text'].copy() if 'type' in df.columns else df.copy()
        if len(text_df) == 0:
            return DimensionScore(score=50.0)

        # Component 1: Equity (40%)
        equity = self._calc_equity(text_df)

        # Component 2: Coordination (30%)
        coordination = self._calc_coordination(text_df)

        # Component 3: Shared Meaning (30%)
        shared_meaning = self._calc_shared_meaning(text_df)

        # Calculate weighted score
        total_score = (
            equity['score'] * 0.40 +
            coordination['score'] * 0.30 +
            shared_meaning['score'] * 0.30
        )

        insights = []
        if equity['score'] >= 70:
            insights.append('Boa equidade na relação')
        if shared_meaning['score'] >= 70:
            insights.append('Forte senso de objetivos compartilhados')

        return DimensionScore(
            score=round(total_score, 1),
            components={
                'equity': equity,
                'coordination': coordination,
                'sharedMeaning': shared_meaning,
            },
            insights=insights
        )

    def _calc_equity(self, df: pd.DataFrame) -> Dict:
        """Calculate equity score (message volume + initiative balance)."""
        # Message volume balance
        msg_counts = df.groupby(self.sender_col).size()
        if len(msg_counts) < 2:
            return {'score': 70.0, 'insight': 'Dados insuficientes'}

        total = msg_counts.sum()
        min_pct = round(msg_counts.min() / total * 100)
        max_pct = round(msg_counts.max() / total * 100)

        # Initiative balance (who starts conversations)
        df_sorted = df.sort_values(self.datetime_col)
        df_sorted['time_diff'] = df_sorted[self.datetime_col].diff().dt.total_seconds() / 3600

        # Conversations start after 4+ hour gap
        initiations = df_sorted[
            (df_sorted['time_diff'].isna()) |
            (df_sorted['time_diff'] >= 4)
        ]

        init_counts = initiations.groupby(self.sender_col).size()
        if len(init_counts) >= 2:
            init_total = init_counts.sum()
            init_min_pct = round(init_counts.min() / init_total * 100)
        else:
            init_min_pct = 50

        # Combined balance score
        msg_balance = 100 - abs(min_pct - 50) * 2
        init_balance = 100 - abs(init_min_pct - 50) * 2

        score = (msg_balance * 0.6 + init_balance * 0.4)

        if score >= 80:
            insight = 'Participação equilibrada'
        elif score >= 60:
            insight = 'Moderada assimetria'
        else:
            insight = 'Participação desequilibrada'

        return {
            'score': round(score, 1),
            'messageBalance': f'{min_pct}/{max_pct}',
            'initiativeBalance': f'{init_min_pct}%',
            'insight': insight
        }

    def _calc_coordination(self, df: pd.DataFrame) -> Dict:
        """Calculate coordination score."""
        # Measure response consistency and task completion language
        completion_markers = {
            'feito', 'pago', 'pronto', 'resolvido', 'ok feito',
            'já fiz', 'combinado', 'confirmado'
        }

        task_words = {
            'pagar', 'fazer', 'comprar', 'ligar', 'marcar', 'resolver'
        }

        tasks_mentioned = 0
        tasks_completed = 0

        for _, row in df.iterrows():
            text = str(row.get(self.message_col, '')).lower()
            if any(word in text for word in task_words):
                tasks_mentioned += 1
            if any(marker in text for marker in completion_markers):
                tasks_completed += 1

        if tasks_mentioned == 0:
            return {'score': 70.0, 'insight': 'Poucas tarefas detectadas'}

        completion_rate = tasks_completed / tasks_mentioned
        score = min(100, 50 + (completion_rate * 50))

        if completion_rate >= 0.5:
            insight = 'Boa coordenação de tarefas'
        elif completion_rate >= 0.3:
            insight = 'Coordenação moderada'
        else:
            insight = 'Melhorar acompanhamento de tarefas'

        return {
            'score': round(score, 1),
            'completionRate': f'{round(completion_rate*100)}%',
            'tasksTotal': tasks_mentioned,
            'insight': insight
        }

    def _calc_shared_meaning(self, df: pd.DataFrame) -> Dict:
        """Calculate shared meaning score (future planning, shared references)."""
        future_patterns = PositivePatternDetector.FUTURE_PLANNING_PATTERNS
        future_re = [re.compile(p, re.IGNORECASE) for p in future_patterns]

        future_count = 0
        for _, row in df.iterrows():
            text = str(row.get(self.message_col, ''))
            for pattern in future_re:
                if pattern.search(text):
                    future_count += 1
                    break

        total_days = (df[self.datetime_col].max() - df[self.datetime_col].min()).days
        weeks = max(total_days / 7, 1)
        per_week = future_count / weeks

        # Score: 5+ per week = 100, 2 = 70, 0 = 40
        if per_week >= 5:
            score = 100
        elif per_week >= 2:
            score = 70 + (per_week - 2) * 10
        elif per_week >= 1:
            score = 50 + (per_week - 1) * 20
        else:
            score = 40 + (per_week * 10)

        if per_week >= 3:
            insight = 'Forte planejamento conjunto'
        elif per_week >= 1:
            insight = 'Planejamento moderado para o futuro'
        else:
            insight = 'Mais planejamento conjunto poderia fortalecer conexão'

        return {
            'score': round(score, 1),
            'perWeek': round(per_week, 1),
            'insight': insight
        }

    def calculate_overall_score(self) -> HealthScoreResult:
        """
        Calculate overall health score with all dimensions.

        Uses temporal weighting:
        - Recent (30 days): 50%
        - Medium-term (90 days): 30%
        - Long-term (all history): 20%
        """
        temporal_dfs = self._get_temporal_dfs()

        # Calculate scores for each temporal window
        temporal_scores = {}
        for period, weight in self.TEMPORAL_WEIGHTS.items():
            period_df = temporal_dfs.get(period, pd.DataFrame())
            if len(period_df) == 0:
                continue

            connection = self.calculate_connection_quality(period_df)
            maintenance = self.calculate_relationship_maintenance(period_df)
            communication = self.calculate_communication_health(period_df)
            partnership = self.calculate_partnership_dynamics(period_df)

            period_overall = (
                connection.score * self.DIMENSION_WEIGHTS['connection_quality'] +
                maintenance.score * self.DIMENSION_WEIGHTS['relationship_maintenance'] +
                communication.score * self.DIMENSION_WEIGHTS['communication_health'] +
                partnership.score * self.DIMENSION_WEIGHTS['partnership_dynamics']
            )

            temporal_scores[period] = {
                'overall': period_overall,
                'weight': weight,
                'connection': connection,
                'maintenance': maintenance,
                'communication': communication,
                'partnership': partnership,
            }

        # Calculate weighted overall score
        if not temporal_scores:
            return HealthScoreResult(
                overall=50.0,
                label='Dados Insuficientes',
                label_en='Insufficient Data',
                confidence=0.0,
                trend='N/A'
            )

        total_weight = sum(ts['weight'] for ts in temporal_scores.values())
        weighted_overall = sum(
            ts['overall'] * ts['weight']
            for ts in temporal_scores.values()
        ) / total_weight

        # Use recent period for detailed dimensions
        recent = temporal_scores.get('recent_30d', list(temporal_scores.values())[0])

        # Calculate trend
        recent_score = temporal_scores.get('recent_30d', {}).get('overall', weighted_overall)
        medium_score = temporal_scores.get('medium_90d', {}).get('overall')

        if medium_score:
            trend_diff = recent_score - medium_score
            trend = f'+{trend_diff:.0f}' if trend_diff >= 0 else f'{trend_diff:.0f}'
            trend += ' vs mês anterior'
        else:
            trend = 'Dados insuficientes para tendência'

        # Get labels
        label_pt, label_en = self._get_label(weighted_overall)

        # Calculate confidence based on data volume
        total_messages = len(self.df)
        if total_messages >= 1000:
            confidence = 0.95
        elif total_messages >= 500:
            confidence = 0.85
        elif total_messages >= 200:
            confidence = 0.75
        elif total_messages >= 50:
            confidence = 0.60
        else:
            confidence = 0.40

        # Compile insights
        all_insights = self._compile_insights(recent)

        # Compile alerts
        alerts = self._compile_alerts(recent)

        return HealthScoreResult(
            overall=round(weighted_overall, 1),
            label=label_pt,
            label_en=label_en,
            confidence=round(confidence, 2),
            trend=trend,
            dimensions={
                'connectionQuality': recent['connection'],
                'relationshipMaintenance': recent['maintenance'],
                'communicationHealth': recent['communication'],
                'partnershipDynamics': recent['partnership'],
            },
            insights=all_insights,
            alerts=alerts
        )

    def _compile_insights(self, recent: Dict) -> Dict:
        """Compile insights from dimension scores."""
        strengths = []
        opportunities = []

        # Analyze connection quality
        conn = recent['connection']
        if conn.score >= 70:
            strengths.append({
                'dimension': 'connectionQuality',
                'finding': 'Boa qualidade de conexão e responsividade',
                'evidence': conn.insights[0] if conn.insights else 'Pontuação alta em responsividade'
            })
        elif conn.score < 55:
            opportunities.append({
                'dimension': 'connectionQuality',
                'finding': 'Qualidade de resposta pode melhorar',
                'suggestion': 'Quando parceiro compartilha sentimentos, tente fazer perguntas de acompanhamento',
                'impact': 'Alto - preditor central de intimidade'
            })

        # Analyze maintenance
        maint = recent['maintenance']
        ratio = maint.components.get('positivity', {}).get('ratio', '0:1')
        if maint.score >= 70:
            strengths.append({
                'dimension': 'relationshipMaintenance',
                'finding': f'Proporção positivo/negativo de {ratio} próxima do ideal de 5:1',
                'evidence': 'Últimos 30 dias mostram positividade consistente'
            })

        # Analyze communication
        comm = recent['communication']
        if comm.score >= 70:
            strengths.append({
                'dimension': 'communicationHealth',
                'finding': 'Comunicação saudável sem padrões negativos',
                'evidence': 'Baixa presença dos Quatro Cavaleiros de Gottman'
            })
        elif comm.score < 55:
            # Check which horseman is problematic
            contempt = comm.components.get('absenceOfContempt', {})
            if contempt.get('contemptCount', 0) > 0:
                opportunities.append({
                    'dimension': 'communicationHealth',
                    'finding': 'Desprezo detectado - padrão mais destrutivo',
                    'suggestion': 'Construir cultura de apreciação com gratidão diária específica',
                    'impact': 'Crítico - preditor mais forte de dissolução'
                })

        # Analyze partnership
        partner = recent['partnership']
        if partner.score >= 70:
            strengths.append({
                'dimension': 'partnershipDynamics',
                'finding': 'Boa dinâmica de parceria e equidade',
                'evidence': 'Distribuição equilibrada de responsabilidades'
            })

        return {
            'strengths': strengths,
            'opportunities': opportunities
        }

    def _compile_alerts(self, recent: Dict) -> List[Dict]:
        """Compile alerts from pattern analysis."""
        alerts = []

        # Check communication for Four Horsemen
        comm = recent['communication']
        contempt_count = comm.components.get('absenceOfContempt', {}).get('contemptCount', 0)
        criticism_count = comm.components.get('gentleStartup', {}).get('criticismCount', 0)

        if contempt_count >= 2:
            alerts.append({
                'pattern': 'contempt',
                'frequency': f'{contempt_count} instâncias',
                'context': 'Detectado em conversas recentes',
                'antidote': 'Expressar gratidão específica diariamente'
            })

        if criticism_count >= 3:
            alerts.append({
                'pattern': 'criticism',
                'frequency': f'{criticism_count} instâncias nos últimos 7 dias',
                'context': 'Aparece durante coordenação de tarefas',
                'antidote': "Use 'Eu sinto...' em vez de 'Você sempre...'"
            })

        # Check positivity ratio
        maint = recent['maintenance']
        ratio_str = maint.components.get('positivity', {}).get('ratio', '5:1')
        try:
            ratio = float(ratio_str.split(':')[0])
            if ratio < 3:
                alerts.append({
                    'pattern': 'low_positivity_ratio',
                    'frequency': f'Proporção atual: {ratio_str}',
                    'context': 'Meta é 5:1 segundo pesquisa de Gottman',
                    'antidote': 'Aumentar expressões de carinho e gratidão'
                })
        except (ValueError, IndexError):
            pass

        return alerts

    def to_dict(self) -> Dict:
        """Convert health score result to dictionary for JSON output."""
        result = self.calculate_overall_score()

        output = {
            'healthScore': {
                'overall': result.overall,
                'label': result.label,
                'labelEn': result.label_en,
                'confidence': result.confidence,
                'trend': result.trend,

                'dimensions': {
                    name: {
                        'score': dim.score,
                        'components': dim.components,
                        'insights': dim.insights
                    }
                    for name, dim in result.dimensions.items()
                },

                'insights': result.insights,
                'alerts': result.alerts,
            },
            'generated': result.generated,
            'methodology': {
                'framework': 'Hybrid Gottman + Interpersonal Process Model + Maintenance Behaviors',
                'scale': '1-100',
                'temporalWeights': self.TEMPORAL_WEIGHTS,
                'dimensionWeights': self.DIMENSION_WEIGHTS,
                'references': [
                    'Gottman, J. M. (1994). What Predicts Divorce?',
                    'Reis, H. T., & Shaver, P. (1988). Intimacy as an interpersonal process',
                    'Stafford, L., & Canary, D. J. (1991). Maintenance strategies',
                ]
            }
        }

        # Add LLM analysis section if LLM was used
        if self.use_llm and self.llm_analyzer:
            output['llmAnalysis'] = self.llm_analyzer.get_analysis_summary()

            # Add LLM comparison data for pattern detectors
            gottman_llm = self.gottman_detector.get_llm_contempt_analysis()
            positive_llm = self.positive_detector.get_llm_repair_analysis()

            if gottman_llm or positive_llm:
                output['llmAnalysis']['patternDetectorAnalysis'] = {
                    'contemptDetections': gottman_llm[:10] if gottman_llm else [],
                    'repairValidations': positive_llm[:10] if positive_llm else [],
                }

            # Add scoring-level LLM analysis
            output['llmAnalysis']['scoringAnalysis'] = {
                'responseQualityAssessments': self._llm_response_qualities[:10],
                'vulnerabilityDepthAssessments': self._llm_vulnerability_depths[:10],
            }
        else:
            output['llmAnalysis'] = {
                'enabled': False,
                'reason': 'LLM analyzer not provided or disabled'
            }

        return output
