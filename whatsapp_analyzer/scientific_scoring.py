"""
Scientific Scoring Module

Implements a validated 4-dimension relationship health scoring framework
based on academic research from relationship science.

RESTRUCTURED Framework Dimensions (v2.0):
1. Emotional Connection (30%) - Interpersonal Process Model (Reis & Shaver)
   - Responsiveness (40%): Quality of responses to partner
   - Vulnerability (35%): Self-disclosure depth (DISCLOSURE_PATTERNS exclusive)
   - Attunement (25%): Active listening behaviors (ACTIVE_LISTENING exclusive)

2. Affection & Commitment (25%) - Stafford & Canary + Gottman
   - Expressed Affection (40%): AFFECTION_PATTERNS exclusive
   - Commitment Signals (35%): ASSURANCE + FUTURE_PLANNING exclusive
   - Appreciation (25%): GRATITUDE_PATTERNS exclusive

3. Communication Health (25%) - Gottman's Four Horsemen
   - Constructive Dialogue (30%): CRITICISM + DEFENSIVENESS inverse
   - Conflict Repair (30%): REPAIR_PATTERNS exclusive
   - Emotional Safety (25%): CONTEMPT + STONEWALLING inverse
   - Supportive Responses (15%): SUPPORT + UNDERSTANDING exclusive

4. Partnership Equity (20%) - Equity Theory
   - Contribution Balance (40%): Task sharing + initiative balance
   - Coordination (35%): Task completion tracking
   - Emotional Reciprocity (25%): Balance in emotional exchange

Pattern Ownership (Exclusive - No Overlaps):
- D1.Vulnerability: DISCLOSURE_PATTERNS
- D1.Attunement: ACTIVE_LISTENING_PATTERNS
- D2.Affection: AFFECTION_PATTERNS
- D2.Commitment: ASSURANCE_PATTERNS + FUTURE_PLANNING_PATTERNS
- D2.Appreciation: GRATITUDE_PATTERNS
- D3.Dialogue: CRITICISM_PATTERNS + DEFENSIVENESS_PATTERNS (inverse)
- D3.Repair: REPAIR_PATTERNS
- D3.Safety: CONTEMPT_PATTERNS + STONEWALLING (inverse)
- D3.Support: SUPPORT_PATTERNS + UNDERSTANDING_PATTERNS
- D4: action_verbs, completion_markers, balance metrics

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

    RESTRUCTURED Dimensions (v2.1 - No Pattern Overlaps, 30-Day Window):
    - Emotional Connection (30%): Responsiveness, vulnerability, attunement
    - Affection & Commitment (25%): Expressed affection, commitment signals, appreciation
    - Communication Health (25%): Constructive dialogue, conflict repair, emotional safety, support
    - Partnership Equity (20%): Contribution balance, coordination, emotional reciprocity

    Key Changes from v1.0:
    - v2.0: Restructured dimensions to eliminate pattern overlaps
    - v2.1: 30-day only scoring window for faster score responsiveness
    - Reciprocity moved from D1 to D4 as "Emotional Reciprocity"
    - Emotional Expression split: disclosure→D1.Vulnerability, affection→D2.Affection
    - Positivity ratio feeds into D4.Emotional Reciprocity (repairs excluded)
    - Task Sharing merged with Equity→D4.Contribution Balance
    - Shared Meaning merged with Assurances→D2.Commitment Signals
    - Four Horsemen consolidated into D3 sub-dimensions
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

    # Dimension weights (v2.0)
    DIMENSION_WEIGHTS = {
        'emotional_connection': 0.30,
        'affection_commitment': 0.25,
        'communication_health': 0.25,
        'partnership_equity': 0.20,
    }

    # Temporal window (v2.1 - Last 30 days only for faster score changes)
    SCORING_WINDOW_DAYS = 30

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

    def _get_scoring_df(self) -> pd.DataFrame:
        """
        Get DataFrame filtered to scoring window (last 30 days).

        v2.1: Only uses last 30 days for faster score responsiveness.
        Relationships should see score changes quickly as patterns change.
        """
        now = self.df[self.datetime_col].max()
        cutoff = now - timedelta(days=self.SCORING_WINDOW_DAYS)
        return self.df[self.df[self.datetime_col] >= cutoff]

    def _get_temporal_dfs(self) -> Dict[str, pd.DataFrame]:
        """Legacy method - returns only recent period for compatibility."""
        return {
            'recent_30d': self._get_scoring_df(),
            'all': self.df
        }

    def _get_label(self, score: float) -> Tuple[str, str]:
        """Get Portuguese and English labels for a score."""
        for (low, high), (pt, en) in self.SCORE_LABELS.items():
            if low <= score <= high:
                return pt, en
        return 'N/A', 'N/A'

    def calculate_emotional_connection(self, df: pd.DataFrame = None) -> DimensionScore:
        """
        Calculate Emotional Connection dimension (30%).

        Based on Interpersonal Process Model (Reis & Shaver).

        Components:
        - Responsiveness (40%): Quality of responses to partner
        - Vulnerability (35%): Self-disclosure depth (DISCLOSURE_PATTERNS exclusive)
        - Attunement (25%): Active listening behaviors (ACTIVE_LISTENING exclusive)

        Pattern Ownership:
        - Vulnerability: Uses DISCLOSURE_PATTERNS exclusively
        - Attunement: Uses ACTIVE_LISTENING_PATTERNS exclusively
        - Responsiveness: Response quality assessment (no pattern overlap)
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

        # Component 2: Vulnerability (35%) - DISCLOSURE_PATTERNS exclusive
        vulnerability_score = self._calc_vulnerability(text_df)

        # Component 3: Attunement (25%) - ACTIVE_LISTENING exclusive
        attunement_score = self._calc_attunement(text_df)

        # Calculate weighted score
        total_score = (
            responsiveness_score['score'] * 0.40 +
            vulnerability_score['score'] * 0.35 +
            attunement_score['score'] * 0.25
        )

        insights = []
        if responsiveness_score['score'] < 60:
            insights.append('Respostas poderiam ser mais empáticas')
        if vulnerability_score['score'] >= 70:
            insights.append('Boa vulnerabilidade emocional')
        if attunement_score['score'] >= 70:
            insights.append('Forte escuta ativa')

        return DimensionScore(
            score=round(total_score, 1),
            components={
                'responsiveness': responsiveness_score,
                'vulnerability': vulnerability_score,
                'attunement': attunement_score,
            },
            insights=insights
        )

    # Legacy alias for backwards compatibility
    def calculate_connection_quality(self, df: pd.DataFrame = None) -> DimensionScore:
        """Legacy alias for calculate_emotional_connection."""
        return self.calculate_emotional_connection(df)

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

    def _calc_vulnerability(self, df: pd.DataFrame) -> Dict:
        """
        Calculate vulnerability score (D1.Vulnerability).

        Uses DISCLOSURE_PATTERNS exclusively (no overlap with other dimensions).

        With LLM enhancement:
        - Assesses actual vulnerability depth (surface/moderate/deep)
        - Evaluates if disclosure invites reciprocity
        - Not all emotional disclosure is equal in intimacy value
        """
        text_df = df.copy()

        # EXCLUSIVE: Only DISCLOSURE_PATTERNS (not AFFECTION - that's D2)
        disclosure_patterns = PositivePatternDetector.DISCLOSURE_PATTERNS
        disclosure_re = [re.compile(p, re.IGNORECASE) for p in disclosure_patterns]

        disclosure_count = 0
        disclosure_messages = []
        total_messages = len(text_df)

        for idx, row in text_df.iterrows():
            text = str(row.get(self.message_col, ''))
            for pattern in disclosure_re:
                if pattern.search(text):
                    disclosure_count += 1
                    disclosure_messages.append((idx, text))
                    break

        # Calculate percentage and base score
        if total_messages == 0:
            return {'score': 50.0, 'insight': 'Dados insuficientes'}

        disclosure_rate = disclosure_count / total_messages

        # Baseline: 5% disclosure messages is healthy
        base_score = min(100, (disclosure_rate / 0.05) * 70 + 30)

        # LLM-enhanced vulnerability depth assessment
        depth_scores = []
        if self.use_llm and disclosure_messages:
            # Sample up to 20 disclosure messages for LLM analysis
            sample_messages = disclosure_messages[:20]

            for idx, text in sample_messages:
                # Get context from nearby messages
                context = self._get_message_context(text_df, idx)

                depth_result = self.llm_analyzer.analyze_vulnerability_depth(text, context)

                # Convert depth level to score
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
        vulnerability_words = ['sinto', 'medo', 'preocupado', 'ansioso', 'nervoso',
                               'triste', 'frustrado', 'inseguro', 'vulnerável']
        for _, row in text_df.iterrows():
            text = str(row.get(self.message_col, '')).lower()
            for word in vulnerability_words:
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
                insight = 'Vulnerabilidade presente, pode aprofundar'

            return {
                'score': round(final_score, 1),
                'insight': insight,
                'diversityCount': diversity,
                'llmAssessed': len(depth_scores),
                'avgDepthScore': round(avg_depth, 1),
                'deepDisclosures': deep_count,
            }

        # Non-LLM insight
        if diversity >= 5:
            insight = 'Vocabulário de vulnerabilidade diverso'
        elif diversity >= 2:
            insight = 'Boa expressão de vulnerabilidade'
        else:
            insight = 'Vulnerabilidade emocional limitada'

        return {
            'score': round(base_score, 1),
            'insight': insight,
            'diversityCount': diversity
        }

    # Legacy alias
    def _calc_emotional_expression(self, df: pd.DataFrame) -> Dict:
        """Legacy alias for _calc_vulnerability."""
        return self._calc_vulnerability(df)

    def _calc_attunement(self, df: pd.DataFrame) -> Dict:
        """
        Calculate attunement score (D1.Attunement).

        Uses ACTIVE_LISTENING_PATTERNS exclusively (no overlap with other dimensions).

        Attunement indicators:
        - Questions about partner's day/feelings
        - Follow-up questions
        - Showing interest in partner's experiences
        """
        # EXCLUSIVE: Only ACTIVE_LISTENING_PATTERNS
        listening_patterns = PositivePatternDetector.ACTIVE_LISTENING_PATTERNS
        listening_re = [re.compile(p, re.IGNORECASE) for p in listening_patterns]

        listening_count = 0
        total_messages = len(df)

        for _, row in df.iterrows():
            text = str(row.get(self.message_col, ''))
            for pattern in listening_re:
                if pattern.search(text):
                    listening_count += 1
                    break

        if total_messages == 0:
            return {'score': 50.0, 'insight': 'Dados insuficientes'}

        listening_rate = listening_count / total_messages

        # Baseline: 3% active listening is healthy
        score = min(100, (listening_rate / 0.03) * 70 + 30)
        score = max(30, score)

        if listening_rate >= 0.05:
            insight = 'Forte escuta ativa e interesse genuíno'
        elif listening_rate >= 0.02:
            insight = 'Boa sintonia com o parceiro'
        else:
            insight = 'Mais perguntas de interesse fortaleceriam conexão'

        return {
            'score': round(score, 1),
            'rate': f'{listening_rate*100:.1f}%',
            'count': listening_count,
            'insight': insight
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

    def _calc_emotional_reciprocity(self, df: pd.DataFrame) -> Dict:
        """
        Calculate emotional reciprocity score (D4.Emotional Reciprocity).

        Moved from D1 to D4 in v2.0.

        Measures the balance of positive emotional interactions.
        Uses the 5:1 ratio concept from Gottman, but EXCLUDES repair patterns
        (which are counted exclusively in D3.Conflict Repair).
        """
        summary = self.pattern_analyzer.analyze_conversation(
            df,
            sender_col=self.sender_col,
            message_col=self.message_col,
            datetime_col=self.datetime_col
        )

        # Get positive counts by person (for balance calculation)
        positive_by_person = defaultdict(int)
        negative_by_person = defaultdict(int)

        for match in summary.matches:
            sender = match.sender
            if sender is None:
                continue
            if match.pattern_type == 'positive':
                # EXCLUDE repairs from reciprocity (they're in D3)
                if match.pattern_name != 'repair_attempt':
                    positive_by_person[sender] += 1
            else:
                negative_by_person[sender] += 1

        # Calculate positive balance
        pos_counts = list(positive_by_person.values())
        if len(pos_counts) < 2 or sum(pos_counts) == 0:
            balance = 100
        else:
            min_pos = min(pos_counts)
            max_pos = max(pos_counts)
            balance = (min_pos / max_pos) * 100 if max_pos > 0 else 100

        # Calculate ratio (without repairs for this dimension)
        total_pos = sum(pos_counts)
        total_neg = sum(negative_by_person.values())
        ratio = total_pos / total_neg if total_neg > 0 else (total_pos if total_pos > 0 else 5.0)

        # Score based on both balance and ratio
        balance_score = 50 + (balance / 2)  # 50-100
        ratio_score = min(100, ratio / 5 * 100)  # 100 at 5:1

        # Combined score (60% ratio, 40% balance)
        score = ratio_score * 0.6 + balance_score * 0.4

        if ratio >= 5.0 and balance >= 70:
            insight = 'Excelente equilíbrio emocional positivo'
        elif ratio >= 3.0:
            insight = 'Boa reciprocidade emocional'
        elif ratio >= 1.0:
            insight = 'Reciprocidade pode melhorar'
        else:
            insight = 'Mais positividade mútua recomendada'

        return {
            'score': round(score, 1),
            'insight': insight,
            'ratio': f'{ratio:.1f}:1',
            'balance': f'{round(balance)}%',
            'positiveCount': total_pos,
            'negativeCount': total_neg
        }

    # Legacy alias (now uses the new method)
    def _calc_reciprocity(self, df: pd.DataFrame) -> Dict:
        """Legacy alias - redirects to _calc_emotional_reciprocity."""
        return self._calc_emotional_reciprocity(df)

    def calculate_affection_commitment(self, df: pd.DataFrame = None) -> DimensionScore:
        """
        Calculate Affection & Commitment dimension (25%).

        Based on Stafford & Canary's Maintenance Behaviors + Gottman's Fondness/Admiration.

        Components:
        - Expressed Affection (40%): AFFECTION_PATTERNS exclusive
        - Commitment Signals (35%): ASSURANCE + FUTURE_PLANNING exclusive
        - Appreciation (25%): GRATITUDE_PATTERNS exclusive

        Pattern Ownership (v2.0 - No Overlaps):
        - Affection: Uses AFFECTION_PATTERNS exclusively (not shared with D1)
        - Commitment: Uses ASSURANCE + FUTURE_PLANNING exclusively (merged from old D4.SharedMeaning)
        - Appreciation: Uses GRATITUDE_PATTERNS exclusively
        """
        if df is None:
            df = self.df

        text_df = df[df['type'] == 'text'].copy() if 'type' in df.columns else df.copy()
        if len(text_df) == 0:
            return DimensionScore(score=50.0)

        # Component 1: Expressed Affection (40%) - AFFECTION_PATTERNS exclusive
        affection = self._calc_expressed_affection(text_df)

        # Component 2: Commitment Signals (35%) - ASSURANCE + FUTURE_PLANNING exclusive
        commitment = self._calc_commitment_signals(text_df)

        # Component 3: Appreciation (25%) - GRATITUDE_PATTERNS exclusive
        appreciation = self._calc_appreciation(text_df)

        # Calculate weighted score
        total_score = (
            affection['score'] * 0.40 +
            commitment['score'] * 0.35 +
            appreciation['score'] * 0.25
        )

        insights = []
        if affection['score'] >= 70:
            insights.append('Forte expressão de afeto')
        if commitment['score'] >= 70:
            insights.append('Sinais claros de compromisso')
        if appreciation['score'] >= 70:
            insights.append('Cultura de apreciação estabelecida')

        return DimensionScore(
            score=round(total_score, 1),
            components={
                'expressedAffection': affection,
                'commitmentSignals': commitment,
                'appreciation': appreciation,
            },
            insights=insights
        )

    # Legacy alias for backwards compatibility
    def calculate_relationship_maintenance(self, df: pd.DataFrame = None) -> DimensionScore:
        """Legacy alias for calculate_affection_commitment."""
        return self.calculate_affection_commitment(df)

    def _calc_expressed_affection(self, df: pd.DataFrame) -> Dict:
        """
        Calculate expressed affection score (D2.Expressed Affection).

        Uses AFFECTION_PATTERNS exclusively (no overlap with other dimensions).
        """
        # EXCLUSIVE: Only AFFECTION_PATTERNS
        affection_patterns = PositivePatternDetector.AFFECTION_PATTERNS
        patterns_re = [re.compile(p, re.IGNORECASE) for p in affection_patterns]

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

        # Score: 15+ per week = 100, 7 = 70, 3 = 40
        if per_week >= 15:
            score = 100
        elif per_week >= 7:
            score = 70 + (per_week - 7) * 3.75
        elif per_week >= 3:
            score = 40 + (per_week - 3) * 7.5
        else:
            score = max(20, per_week * 13)

        if per_week >= 10:
            insight = 'Expressões frequentes de afeto'
        elif per_week >= 5:
            insight = 'Afeto presente regularmente'
        else:
            insight = 'Mais expressões de afeto fortaleceriam a conexão'

        return {
            'score': round(score, 1),
            'perWeek': round(per_week, 1),
            'count': count,
            'insight': insight
        }

    def _calc_commitment_signals(self, df: pd.DataFrame) -> Dict:
        """
        Calculate commitment signals score (D2.Commitment Signals).

        Uses ASSURANCE_PATTERNS + FUTURE_PLANNING_PATTERNS exclusively.
        Merged from old D4.SharedMeaning and D2.Assurances.
        """
        # EXCLUSIVE: ASSURANCE + FUTURE_PLANNING (merged)
        assurance_patterns = PositivePatternDetector.ASSURANCE_PATTERNS
        future_patterns = PositivePatternDetector.FUTURE_PLANNING_PATTERNS
        all_patterns = assurance_patterns + future_patterns
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

        # Score: 8+ per week = 100, 4 = 70, 2 = 40
        if per_week >= 8:
            score = 100
        elif per_week >= 4:
            score = 70 + (per_week - 4) * 7.5
        elif per_week >= 2:
            score = 40 + (per_week - 2) * 15
        else:
            score = max(20, per_week * 20)

        if per_week >= 5:
            insight = 'Fortes sinais de compromisso e futuro conjunto'
        elif per_week >= 2:
            insight = 'Compromisso demonstrado regularmente'
        else:
            insight = 'Mais sinais de compromisso fortaleceriam a relação'

        return {
            'score': round(score, 1),
            'perWeek': round(per_week, 1),
            'count': count,
            'insight': insight
        }

    def _calc_appreciation(self, df: pd.DataFrame) -> Dict:
        """
        Calculate appreciation score (D2.Appreciation).

        Uses GRATITUDE_PATTERNS exclusively.
        Key antidote for contempt (Gottman).
        """
        # EXCLUSIVE: Only GRATITUDE_PATTERNS
        gratitude_patterns = PositivePatternDetector.GRATITUDE_PATTERNS
        patterns_re = [re.compile(p, re.IGNORECASE) for p in gratitude_patterns]

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

        # Score: 7+ per week = 100, 3 = 70, 1 = 40
        if per_week >= 7:
            score = 100
        elif per_week >= 3:
            score = 70 + (per_week - 3) * 7.5
        elif per_week >= 1:
            score = 40 + (per_week - 1) * 15
        else:
            score = max(20, per_week * 40)

        if per_week >= 5:
            insight = 'Cultura de apreciação forte'
        elif per_week >= 2:
            insight = 'Gratidão expressada regularmente'
        else:
            insight = 'Mais apreciação constrói cultura positiva'

        return {
            'score': round(score, 1),
            'perWeek': round(per_week, 1),
            'count': count,
            'insight': insight
        }

    # Legacy methods (kept for backwards compatibility)
    def _calc_positivity(self, df: pd.DataFrame) -> Dict:
        """Legacy positivity score - now part of D4.Emotional Reciprocity."""
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
            score = 70 + (ratio - 3.0) * 15
        elif ratio >= 1.0:
            score = 40 + (ratio - 1.0) * 15
        else:
            score = max(10, ratio * 40)

        return {
            'score': round(score, 1),
            'ratio': f'{ratio:.1f}:1',
            'positive': total_positive,
            'negative': total_negative,
            'insight': f'Proporção {ratio:.1f}:1 (meta: 5:1)'
        }

    def _calc_assurances(self, df: pd.DataFrame) -> Dict:
        """Legacy alias - redirects to _calc_commitment_signals."""
        return self._calc_commitment_signals(df)

    def _calc_contribution_balance(self, df: pd.DataFrame) -> Dict:
        """
        Calculate contribution balance score (D4.Contribution Balance).

        Merged from old _calc_task_sharing and _calc_equity.
        Uses action_verbs exclusively (no pattern overlap).

        Measures:
        - Task mention balance between partners
        - Message volume balance
        - Conversation initiation balance
        """
        action_verbs = {
            'pagar', 'fazer', 'comprar', 'ligar', 'marcar', 'resolver',
            'buscar', 'levar', 'enviar', 'agendar', 'confirmar', 'cuidar'
        }

        # Task balance
        task_by_person = defaultdict(int)
        for _, row in df.iterrows():
            text = str(row.get(self.message_col, '')).lower()
            sender = row.get(self.sender_col)
            if any(verb in text for verb in action_verbs):
                task_by_person[sender] += 1

        task_counts = list(task_by_person.values())
        if len(task_counts) >= 2 and sum(task_counts) > 0:
            task_total = sum(task_counts)
            task_min_pct = round(min(task_counts) / task_total * 100)
            task_balance = 100 - abs(task_min_pct - 50) * 2
        else:
            task_balance = 70  # Default when insufficient data

        # Message volume balance
        msg_counts = df.groupby(self.sender_col).size()
        if len(msg_counts) >= 2:
            msg_total = msg_counts.sum()
            msg_min_pct = round(msg_counts.min() / msg_total * 100)
            msg_balance = 100 - abs(msg_min_pct - 50) * 2
        else:
            msg_balance = 70

        # Initiative balance (who starts conversations after 4h gap)
        df_sorted = df.sort_values(self.datetime_col)
        df_sorted['time_diff'] = df_sorted[self.datetime_col].diff().dt.total_seconds() / 3600
        initiations = df_sorted[
            (df_sorted['time_diff'].isna()) | (df_sorted['time_diff'] >= 4)
        ]
        init_counts = initiations.groupby(self.sender_col).size()
        if len(init_counts) >= 2:
            init_total = init_counts.sum()
            init_min_pct = round(init_counts.min() / init_total * 100)
            init_balance = 100 - abs(init_min_pct - 50) * 2
        else:
            init_balance = 70

        # Combined score (40% task, 35% message, 25% initiative)
        score = task_balance * 0.40 + msg_balance * 0.35 + init_balance * 0.25

        if score >= 80:
            insight = 'Contribuições muito equilibradas'
        elif score >= 60:
            insight = 'Contribuições razoavelmente equilibradas'
        else:
            insight = 'Assimetria nas contribuições'

        return {
            'score': round(score, 1),
            'taskBalance': f'{task_min_pct if len(task_counts) >= 2 else 50}%',
            'messageBalance': f'{msg_min_pct if len(msg_counts) >= 2 else 50}%',
            'initiativeBalance': f'{init_min_pct if len(init_counts) >= 2 else 50}%',
            'insight': insight
        }

    # Legacy aliases
    def _calc_task_sharing(self, df: pd.DataFrame) -> Dict:
        """Legacy alias - redirects to _calc_contribution_balance."""
        return self._calc_contribution_balance(df)

    def _calc_equity(self, df: pd.DataFrame) -> Dict:
        """Legacy alias - redirects to _calc_contribution_balance."""
        return self._calc_contribution_balance(df)

    def calculate_communication_health(self, df: pd.DataFrame = None) -> DimensionScore:
        """
        Calculate Communication Health dimension (25%).

        Based on Gottman's Four Horsemen (inverse) with consolidated structure.

        Components:
        - Constructive Dialogue (30%): CRITICISM + DEFENSIVENESS inverse
        - Conflict Repair (30%): REPAIR_PATTERNS exclusive
        - Emotional Safety (25%): CONTEMPT + STONEWALLING inverse
        - Supportive Responses (15%): SUPPORT + UNDERSTANDING exclusive

        Pattern Ownership (v2.0 - Consolidated Four Horsemen):
        - Constructive Dialogue: Inverse of CRITICISM + DEFENSIVENESS patterns
        - Conflict Repair: Uses REPAIR_PATTERNS exclusively
        - Emotional Safety: Inverse of CONTEMPT + STONEWALLING patterns
        - Supportive Responses: Uses SUPPORT + UNDERSTANDING exclusively
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

        # Component 1: Constructive Dialogue (30%) - CRITICISM + DEFENSIVENESS inverse
        constructive_dialogue = self._calc_constructive_dialogue(summary)

        # Component 2: Conflict Repair (30%) - REPAIR_PATTERNS exclusive
        conflict_repair = self._calc_conflict_repair(summary)

        # Component 3: Emotional Safety (25%) - CONTEMPT + STONEWALLING inverse
        emotional_safety = self._calc_emotional_safety(summary)

        # Component 4: Supportive Responses (15%) - SUPPORT + UNDERSTANDING exclusive
        supportive_responses = self._calc_supportive_responses(text_df)

        # Calculate weighted score
        total_score = (
            constructive_dialogue['score'] * 0.30 +
            conflict_repair['score'] * 0.30 +
            emotional_safety['score'] * 0.25 +
            supportive_responses['score'] * 0.15
        )

        insights = []
        if conflict_repair['score'] >= 70:
            insights.append('Bons padrões de reparação')
        if emotional_safety['score'] >= 80:
            insights.append('Comunicação emocionalmente segura')
        if constructive_dialogue['score'] >= 80:
            insights.append('Diálogo construtivo')

        return DimensionScore(
            score=round(total_score, 1),
            components={
                'constructiveDialogue': constructive_dialogue,
                'conflictRepair': conflict_repair,
                'emotionalSafety': emotional_safety,
                'supportiveResponses': supportive_responses,
            },
            insights=insights
        )

    def _calc_constructive_dialogue(self, summary: PatternSummary) -> Dict:
        """
        Calculate constructive dialogue score (D3.Constructive Dialogue).

        Inverse of CRITICISM + DEFENSIVENESS patterns.
        Consolidated from old _calc_gentle_startup.
        """
        criticism_count = summary.four_horsemen_counts.get('criticism', 0)
        defensiveness_count = summary.four_horsemen_counts.get('defensiveness', 0)
        total_negative = criticism_count + defensiveness_count

        # Score decreases with criticism and defensiveness
        # 0 = 100, 3 = 70, 6+ = 40
        if total_negative == 0:
            score = 100
        elif total_negative <= 2:
            score = 100 - (total_negative * 15)
        elif total_negative <= 5:
            score = 70 - ((total_negative - 2) * 10)
        else:
            score = max(20, 40 - ((total_negative - 5) * 4))

        if score >= 80:
            insight = 'Diálogo construtivo e não-defensivo'
        elif score >= 60:
            insight = 'Alguns padrões de crítica/defensividade'
        else:
            insight = 'Usar "Eu sinto..." e aceitar responsabilidade parcial'

        return {
            'score': round(score, 1),
            'criticismCount': criticism_count,
            'defensivenessCount': defensiveness_count,
            'insight': insight
        }

    def _calc_conflict_repair(self, summary: PatternSummary) -> Dict:
        """
        Calculate conflict repair score (D3.Conflict Repair).

        Uses REPAIR_PATTERNS exclusively.
        NOTE: Repairs are NOT counted in D4.Emotional Reciprocity to avoid double-counting.
        """
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
            insight = 'Mais reparações ajudariam na resolução de conflitos'

        return {
            'score': round(score, 1),
            'count': repair_count,
            'successRate': f'{round(success_rate)}%',
            'insight': insight
        }

    def _calc_emotional_safety(self, summary: PatternSummary) -> Dict:
        """
        Calculate emotional safety score (D3.Emotional Safety).

        Inverse of CONTEMPT + STONEWALLING patterns.
        Consolidated from old _calc_absence_contempt.

        Contempt is the most destructive pattern (Gottman).
        """
        contempt_count = summary.four_horsemen_counts.get('contempt', 0)
        stonewalling_count = summary.four_horsemen_counts.get('stonewalling', 0)

        # Contempt is weighted more heavily (most destructive)
        weighted_negative = contempt_count * 2 + stonewalling_count

        # Score: 0 = 100, contempt heavily penalized
        if weighted_negative == 0:
            score = 100
            insight = 'Ambiente emocionalmente seguro'
        elif contempt_count == 0 and stonewalling_count <= 2:
            score = 80
            insight = 'Pouco stonewalling detectado'
        elif contempt_count <= 1:
            score = 60
            insight = 'Desprezo detectado - atenção recomendada'
        elif contempt_count <= 3:
            score = 40
            insight = 'Desprezo presente - construir cultura de apreciação'
        else:
            score = max(20, 30 - (contempt_count * 3))
            insight = 'Desprezo frequente - intervenção urgente'

        return {
            'score': round(score, 1),
            'contemptCount': contempt_count,
            'stonewallingCount': stonewalling_count,
            'insight': insight
        }

    def _calc_supportive_responses(self, df: pd.DataFrame) -> Dict:
        """
        Calculate supportive responses score (D3.Supportive Responses).

        Uses SUPPORT_PATTERNS + UNDERSTANDING_PATTERNS exclusively.
        Merged from old _calc_understanding.
        """
        # EXCLUSIVE: SUPPORT + UNDERSTANDING patterns
        support_patterns = PositivePatternDetector.SUPPORT_PATTERNS
        understanding_patterns = PositivePatternDetector.UNDERSTANDING_PATTERNS
        all_patterns = support_patterns + understanding_patterns
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

        # Score: 5% support/understanding = 100, 2% = 60, 1% = 40
        score = min(100, (rate / 0.05) * 100)
        score = max(30, score)

        if rate >= 0.05:
            insight = 'Forte padrão de apoio e validação'
        elif rate >= 0.02:
            insight = 'Apoio moderado presente'
        else:
            insight = 'Mais apoio e validação fortaleceriam a conexão'

        return {
            'score': round(score, 1),
            'rate': f'{rate*100:.1f}%',
            'count': count,
            'insight': insight
        }

    # Legacy aliases for backwards compatibility
    def _calc_gentle_startup(self, summary: PatternSummary) -> Dict:
        """Legacy alias for _calc_constructive_dialogue."""
        return self._calc_constructive_dialogue(summary)

    def _calc_repair_attempts(self, summary: PatternSummary) -> Dict:
        """Legacy alias for _calc_conflict_repair."""
        return self._calc_conflict_repair(summary)

    def _calc_absence_contempt(self, summary: PatternSummary) -> Dict:
        """Legacy alias for _calc_emotional_safety."""
        return self._calc_emotional_safety(summary)

    def _calc_engagement(self, df: pd.DataFrame) -> Dict:
        """Calculate engagement score (response time analysis)."""
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

    def _calc_understanding(self, df: pd.DataFrame) -> Dict:
        """Legacy alias for _calc_supportive_responses."""
        return self._calc_supportive_responses(df)

    def calculate_partnership_equity(self, df: pd.DataFrame = None) -> DimensionScore:
        """
        Calculate Partnership Equity dimension (20%).

        Based on Equity Theory and Interdependence.

        Components:
        - Contribution Balance (40%): Task sharing + initiative balance (merged)
        - Coordination (35%): Task completion tracking
        - Emotional Reciprocity (25%): Balance in emotional exchange (moved from D1)

        Pattern Ownership (v2.0):
        - Contribution Balance: Uses action_verbs exclusively
        - Coordination: Uses completion_markers exclusively
        - Emotional Reciprocity: Uses positivity ratio (EXCLUDING repairs from D3)

        Key Changes:
        - Shared Meaning moved to D2.Commitment Signals (uses FUTURE_PLANNING)
        - Reciprocity moved here from D1 (was overlapping with D2)
        - Task Sharing merged with Equity into Contribution Balance
        """
        if df is None:
            df = self.df

        text_df = df[df['type'] == 'text'].copy() if 'type' in df.columns else df.copy()
        if len(text_df) == 0:
            return DimensionScore(score=50.0)

        # Component 1: Contribution Balance (40%) - merged Task Sharing + Equity
        contribution_balance = self._calc_contribution_balance(text_df)

        # Component 2: Coordination (35%)
        coordination = self._calc_coordination(text_df)

        # Component 3: Emotional Reciprocity (25%) - moved from D1
        emotional_reciprocity = self._calc_emotional_reciprocity(text_df)

        # Calculate weighted score
        total_score = (
            contribution_balance['score'] * 0.40 +
            coordination['score'] * 0.35 +
            emotional_reciprocity['score'] * 0.25
        )

        insights = []
        if contribution_balance['score'] >= 70:
            insights.append('Boa equidade nas contribuições')
        if coordination['score'] >= 70:
            insights.append('Coordenação eficiente')
        if emotional_reciprocity['score'] >= 70:
            insights.append('Reciprocidade emocional equilibrada')

        return DimensionScore(
            score=round(total_score, 1),
            components={
                'contributionBalance': contribution_balance,
                'coordination': coordination,
                'emotionalReciprocity': emotional_reciprocity,
            },
            insights=insights
        )

    # Legacy alias for backwards compatibility
    def calculate_partnership_dynamics(self, df: pd.DataFrame = None) -> DimensionScore:
        """Legacy alias for calculate_partnership_equity."""
        return self.calculate_partnership_equity(df)

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
        """
        Legacy method - Shared Meaning is now part of D2.Commitment Signals.

        In v2.0, FUTURE_PLANNING_PATTERNS are used exclusively by
        _calc_commitment_signals in the Affection & Commitment dimension.

        This method is kept for backwards compatibility but redirects to
        commitment signals calculation.
        """
        return self._calc_commitment_signals(df)

    def calculate_overall_score(self) -> HealthScoreResult:
        """
        Calculate overall health score with all dimensions.

        v2.1: Uses only last 30 days for faster score responsiveness.
        This allows scores to change quickly as relationship patterns evolve.

        Dimensions (v2.0):
        - Emotional Connection (30%)
        - Affection & Commitment (25%)
        - Communication Health (25%)
        - Partnership Equity (20%)
        """
        # Get last 30 days only
        scoring_df = self._get_scoring_df()

        if len(scoring_df) == 0:
            return HealthScoreResult(
                overall=50.0,
                label='Dados Insuficientes',
                label_en='Insufficient Data',
                confidence=0.0,
                trend='N/A'
            )

        # Calculate dimension scores for the scoring window
        emotional_connection = self.calculate_emotional_connection(scoring_df)
        affection_commitment = self.calculate_affection_commitment(scoring_df)
        communication = self.calculate_communication_health(scoring_df)
        partnership_equity = self.calculate_partnership_equity(scoring_df)

        # Calculate overall score
        overall_score = (
            emotional_connection.score * self.DIMENSION_WEIGHTS['emotional_connection'] +
            affection_commitment.score * self.DIMENSION_WEIGHTS['affection_commitment'] +
            communication.score * self.DIMENSION_WEIGHTS['communication_health'] +
            partnership_equity.score * self.DIMENSION_WEIGHTS['partnership_equity']
        )

        # Store for insights compilation
        recent = {
            'overall': overall_score,
            'emotionalConnection': emotional_connection,
            'affectionCommitment': affection_commitment,
            'communication': communication,
            'partnershipEquity': partnership_equity,
        }

        # Get labels
        label_pt, label_en = self._get_label(overall_score)

        # Calculate confidence based on messages in scoring window
        window_messages = len(scoring_df)
        if window_messages >= 500:
            confidence = 0.95
        elif window_messages >= 200:
            confidence = 0.85
        elif window_messages >= 100:
            confidence = 0.75
        elif window_messages >= 30:
            confidence = 0.60
        else:
            confidence = 0.40

        # Trend info (v2.1 - simplified)
        trend = f'Baseado nos últimos {self.SCORING_WINDOW_DAYS} dias'

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
                # v2.0 dimension names
                'emotionalConnection': recent['emotionalConnection'],
                'affectionCommitment': recent['affectionCommitment'],
                'communicationHealth': recent['communication'],
                'partnershipEquity': recent['partnershipEquity'],
            },
            insights=all_insights,
            alerts=alerts
        )

    def _compile_insights(self, recent: Dict) -> Dict:
        """Compile insights from dimension scores (v2.0 dimension names)."""
        strengths = []
        opportunities = []

        # Analyze emotional connection (v2.0)
        conn = recent['emotionalConnection']
        if conn.score >= 70:
            strengths.append({
                'dimension': 'emotionalConnection',
                'finding': 'Boa conexão emocional e responsividade',
                'evidence': conn.insights[0] if conn.insights else 'Pontuação alta em responsividade'
            })
        elif conn.score < 55:
            opportunities.append({
                'dimension': 'emotionalConnection',
                'finding': 'Qualidade de resposta pode melhorar',
                'suggestion': 'Quando parceiro compartilha sentimentos, tente fazer perguntas de acompanhamento',
                'impact': 'Alto - preditor central de intimidade'
            })

        # Analyze affection & commitment (v2.0)
        affection = recent['affectionCommitment']
        if affection.score >= 70:
            strengths.append({
                'dimension': 'affectionCommitment',
                'finding': 'Forte expressão de afeto e compromisso',
                'evidence': 'Últimos 30 dias mostram afeto consistente'
            })
        elif affection.score < 55:
            opportunities.append({
                'dimension': 'affectionCommitment',
                'finding': 'Expressões de afeto podem aumentar',
                'suggestion': 'Expressar gratidão específica e carinho regularmente',
                'impact': 'Médio - fortalece vínculo emocional'
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
            # Check which patterns are problematic
            safety = comm.components.get('emotionalSafety', {})
            if safety.get('contemptCount', 0) > 0:
                opportunities.append({
                    'dimension': 'communicationHealth',
                    'finding': 'Desprezo detectado - padrão mais destrutivo',
                    'suggestion': 'Construir cultura de apreciação com gratidão diária específica',
                    'impact': 'Crítico - preditor mais forte de dissolução'
                })

        # Analyze partnership equity (v2.0)
        partner = recent['partnershipEquity']
        if partner.score >= 70:
            strengths.append({
                'dimension': 'partnershipEquity',
                'finding': 'Boa equidade na parceria',
                'evidence': 'Distribuição equilibrada de responsabilidades'
            })
        elif partner.score < 55:
            opportunities.append({
                'dimension': 'partnershipEquity',
                'finding': 'Assimetria nas contribuições',
                'suggestion': 'Equilibrar tarefas e iniciativas',
                'impact': 'Médio - afeta senso de justiça'
            })

        return {
            'strengths': strengths,
            'opportunities': opportunities
        }

    def _compile_alerts(self, recent: Dict) -> List[Dict]:
        """Compile alerts from pattern analysis (v2.0 structure)."""
        alerts = []

        # Check communication for Four Horsemen (v2.0 component names)
        comm = recent['communication']

        # Check emotional safety (contempt + stonewalling)
        safety = comm.components.get('emotionalSafety', {})
        contempt_count = safety.get('contemptCount', 0)
        stonewalling_count = safety.get('stonewallingCount', 0)

        if contempt_count >= 2:
            alerts.append({
                'pattern': 'contempt',
                'frequency': f'{contempt_count} instâncias',
                'context': 'Detectado em conversas recentes',
                'antidote': 'Expressar gratidão específica diariamente'
            })

        # Check constructive dialogue (criticism + defensiveness)
        dialogue = comm.components.get('constructiveDialogue', {})
        criticism_count = dialogue.get('criticismCount', 0)
        defensiveness_count = dialogue.get('defensivenessCount', 0)

        if criticism_count >= 3:
            alerts.append({
                'pattern': 'criticism',
                'frequency': f'{criticism_count} instâncias',
                'context': 'Detectado durante coordenação de tarefas',
                'antidote': "Use 'Eu sinto...' em vez de 'Você sempre...'"
            })

        if defensiveness_count >= 3:
            alerts.append({
                'pattern': 'defensiveness',
                'frequency': f'{defensiveness_count} instâncias',
                'context': 'Detectado em discussões',
                'antidote': 'Aceite responsabilidade parcial mesmo que discorde'
            })

        # Check emotional reciprocity (v2.0 - now in partnershipEquity)
        partner = recent['partnershipEquity']
        reciprocity = partner.components.get('emotionalReciprocity', {})
        ratio_str = reciprocity.get('ratio', '5:1')
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
                'framework': 'NAVI v2.1 - Restructured Dimensions (30-Day Window)',
                'version': '2.1',
                'scale': '1-100',
                'scoringWindow': f'{self.SCORING_WINDOW_DAYS} days',
                'dimensionWeights': self.DIMENSION_WEIGHTS,
                'dimensionStructure': {
                    'emotionalConnection': {
                        'weight': 0.30,
                        'theory': 'Interpersonal Process Model (Reis & Shaver)',
                        'components': ['responsiveness', 'vulnerability', 'attunement']
                    },
                    'affectionCommitment': {
                        'weight': 0.25,
                        'theory': 'Stafford & Canary Maintenance + Gottman Fondness',
                        'components': ['expressedAffection', 'commitmentSignals', 'appreciation']
                    },
                    'communicationHealth': {
                        'weight': 0.25,
                        'theory': 'Gottman Four Horsemen (inverse)',
                        'components': ['constructiveDialogue', 'conflictRepair', 'emotionalSafety', 'supportiveResponses']
                    },
                    'partnershipEquity': {
                        'weight': 0.20,
                        'theory': 'Equity Theory + Interdependence',
                        'components': ['contributionBalance', 'coordination', 'emotionalReciprocity']
                    }
                },
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
