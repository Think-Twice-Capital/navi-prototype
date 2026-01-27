"""
Pattern Detectors Module

Implements detection patterns based on relationship science research:
- Gottman's Four Horsemen (criticism, contempt, defensiveness, stonewalling)
- Positive relationship indicators (repair attempts, affection, support, etc.)
- Responsiveness and emotional expression patterns
- Communication health markers

LLM Enhancement (Phase 1):
- Optional LLM validation for contempt detection (catches sarcasm)
- Optional LLM validation for repair attempt authenticity
- Designed for maximum quality baseline with Claude Opus 4.5

References:
- Gottman, J. M. (1994). What Predicts Divorce?
- Reis, H. T., & Shaver, P. (1988). Intimacy as an interpersonal process
- Stafford, L., & Canary, D. J. (1991). Maintenance strategies
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple, Set, TYPE_CHECKING
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd

if TYPE_CHECKING:
    from .llm_analyzer import LLMRelationshipAnalyzer


@dataclass
class PatternMatch:
    """Represents a detected pattern in a message."""
    pattern_type: str  # 'positive' or 'negative'
    pattern_name: str  # e.g., 'criticism', 'repair_attempt'
    horseman: Optional[str] = None  # For Four Horsemen: 'criticism', 'contempt', 'defensiveness', 'stonewalling'
    score_impact: int = 0  # Points to add/subtract
    message_id: Optional[str] = None
    message_text: Optional[str] = None
    sender: Optional[str] = None
    timestamp: Optional[datetime] = None
    antidote: Optional[str] = None  # Research-backed suggestion
    evidence: Optional[str] = None  # The matched pattern/phrase


@dataclass
class PatternSummary:
    """Summary of detected patterns over a period."""
    total_positive: int = 0
    total_negative: int = 0
    positive_ratio: float = 0.0  # Gottman's 5:1 ratio target
    four_horsemen_counts: Dict[str, int] = field(default_factory=dict)
    positive_counts: Dict[str, int] = field(default_factory=dict)
    alerts: List[Dict] = field(default_factory=list)
    matches: List[PatternMatch] = field(default_factory=list)


class GottmanPatternDetector:
    """
    Detects Gottman's Four Horsemen and their antidotes.

    The Four Horsemen predict relationship dissolution with >90% accuracy:
    1. Criticism - Attacking partner's character
    2. Contempt - Showing superiority/disrespect
    3. Defensiveness - Playing victim, counter-attacking
    4. Stonewalling - Withdrawing, shutting down
    """

    # Criticism patterns (PT-BR)
    CRITICISM_PATTERNS = [
        r'\bvocê sempre\b',
        r'\bvocê nunca\b',
        r'\bpor que você não\b',
        r'\bvocê é\s+(?:tão\s+)?(?:preguiçoso|incompetente|burro|idiota|irresponsável)\b',
        r'\bvocê só\s+(?:pensa|liga|quer)\b',
        r'\bvocê não\s+(?:faz|ajuda|colabora)\s+nada\b',
        r'\bo problema é você\b',
        r'\bsempre a mesma coisa com você\b',
        r'\bvocê não muda\b',
        r'\bcansei de você\b',
        r'\bvocê não se importa\b',
        r'\bvocê é impossível\b',
    ]

    # Contempt patterns (PT-BR) - Most destructive horseman
    CONTEMPT_PATTERNS = [
        r'\bgrande coisa\b',
        r'\btanto faz\b',
        r'\bque seja\b',
        r'\bfoda[-\s]?se\b',
        r'\bcomo quiser\b',
        r'\bobviamente\b(?!.*obrigad)',  # Sarcastic "obviously"
        r'\bclaro que\s+(?:não|sim)\b',  # Sarcastic agreement/disagreement
        r'\bparabéns\b(?!.*aniversário|conquista)',  # Sarcastic congrats
        r'\bque surpresa\b',  # Sarcastic surprise
        r'\bvocê acha\s+(?:mesmo|que)\b.*\?',  # Dismissive questioning
        r'🙄',  # Eye roll emoji
        r'\bvocê é patético\b',
        r'\bque piada\b',
        r'\bai ai ai\b',
        r'\btá bom né\b',  # Dismissive
    ]

    # Defensiveness patterns (PT-BR)
    DEFENSIVENESS_PATTERNS = [
        r'\bmas você também\b',
        r'\bnão é minha culpa\b',
        r'\beu não fiz nada\b',
        r'\bvocê que\b.*(?:começou|fez|disse)',
        r'\be você\??\s*$',  # Counter-attacking
        r'\beu não tenho que\b',
        r'\bpor que eu\s+(?:tenho|deveria)\b',
        r'\bnão sou eu\b',
        r'\beu sempre\s+(?:faço|ajudo)\b',
        r'\bvocê está exagerando\b',
        r'\bnão foi isso que eu\b',
        r'\beu não disse isso\b',
        r'\bnão é bem assim\b',
    ]

    # Stonewalling indicators
    STONEWALLING_PHRASES = [
        r'\btanto faz\b',
        r'\bfaz o que você quiser\b',
        r'\bnão quero falar\b',
        r'\bme deixa\b',
        r'\besquece\b',
        r'\bchega\b$',
        r'\bok\b$',  # Minimal response to emotional content
        r'\btá\b$',  # Minimal response
        r'\bsei lá\b',
        r'\bpreciso de um tempo\b',
    ]

    # Antidotes (research-backed solutions)
    ANTIDOTES = {
        'criticism': {
            'name': 'Gentle Startup',
            'description': 'Use "Eu sinto..." em vez de "Você é..."',
            'examples': [
                'Eu me sinto sobrecarregado quando...',
                'Eu preciso de ajuda com...',
                'Eu ficaria feliz se pudéssemos...',
            ]
        },
        'contempt': {
            'name': 'Build Culture of Appreciation',
            'description': 'Expressar gratidão específica diariamente',
            'examples': [
                'Obrigado por ter feito...',
                'Eu admiro como você...',
                'Você é muito bom em...',
            ]
        },
        'defensiveness': {
            'name': 'Take Responsibility',
            'description': 'Aceitar responsabilidade, mesmo que parcial',
            'examples': [
                'Você tem razão sobre...',
                'Eu poderia ter...',
                'Desculpa, não percebi que...',
            ]
        },
        'stonewalling': {
            'name': 'Self-Soothing',
            'description': 'Fazer uma pausa de 20min e retornar à conversa',
            'examples': [
                'Preciso de um momento, mas quero continuar conversando',
                'Podemos falar sobre isso em 20 minutos?',
                'Estou me sentindo sobrecarregado, mas isso é importante',
            ]
        }
    }

    def __init__(self, llm_analyzer: 'LLMRelationshipAnalyzer' = None, use_llm: bool = False):
        """
        Initialize the Gottman pattern detector.

        Args:
            llm_analyzer: Optional LLM analyzer for nuanced detection
            use_llm: If True, use LLM to validate/enhance regex detections
        """
        # Compile patterns for efficiency
        self.criticism_re = [re.compile(p, re.IGNORECASE) for p in self.CRITICISM_PATTERNS]
        self.contempt_re = [re.compile(p, re.IGNORECASE) for p in self.CONTEMPT_PATTERNS]
        self.defensiveness_re = [re.compile(p, re.IGNORECASE) for p in self.DEFENSIVENESS_PATTERNS]
        self.stonewalling_re = [re.compile(p, re.IGNORECASE) for p in self.STONEWALLING_PHRASES]

        # LLM enhancement
        self.llm_analyzer = llm_analyzer
        self.use_llm = use_llm and llm_analyzer is not None

        # Track LLM analysis results for comparison
        self._llm_contempt_results: List[Dict] = []

    def detect_criticism(self, text: str) -> Optional[PatternMatch]:
        """Detect criticism patterns in text."""
        for pattern in self.criticism_re:
            match = pattern.search(text)
            if match:
                return PatternMatch(
                    pattern_type='negative',
                    pattern_name='criticism',
                    horseman='criticism',
                    score_impact=-5,
                    evidence=match.group(0),
                    antidote=self.ANTIDOTES['criticism']['description']
                )
        return None

    def detect_contempt(self, text: str, context: str = "") -> Optional[PatternMatch]:
        """
        Detect contempt patterns in text. Most destructive horseman.

        With LLM enhancement:
        - Regex provides initial detection
        - LLM validates and catches nuanced sarcasm
        - Reduces false positives (e.g., "Parabéns" genuine vs sarcastic)

        Args:
            text: Message text to analyze
            context: Previous messages for context (used by LLM)

        Returns:
            PatternMatch if contempt detected, None otherwise
        """
        regex_match = None
        regex_evidence = None

        # Step 1: Regex detection (fast)
        for pattern in self.contempt_re:
            match = pattern.search(text)
            if match:
                regex_match = match
                regex_evidence = match.group(0)
                break

        # Step 2: LLM validation/detection (if enabled)
        if self.use_llm:
            llm_result = self.llm_analyzer.detect_contempt(text, context)

            # Store for analysis
            self._llm_contempt_results.append({
                'text': text[:100],
                'regex_detected': regex_match is not None,
                'llm_detected': llm_result.is_contempt,
                'llm_confidence': llm_result.confidence,
                'llm_type': llm_result.contempt_type,
                'llm_reasoning': llm_result.reasoning,
            })

            # LLM is authoritative when enabled (higher accuracy)
            if llm_result.is_contempt and llm_result.confidence >= 0.6:
                # Map severity to score impact
                severity_scores = {'mild': -5, 'moderate': -8, 'severe': -10}
                score_impact = severity_scores.get(llm_result.severity, -8)

                return PatternMatch(
                    pattern_type='negative',
                    pattern_name='contempt',
                    horseman='contempt',
                    score_impact=score_impact,
                    evidence=f"[LLM: {llm_result.contempt_type}] {regex_evidence or text[:50]}",
                    antidote=self.ANTIDOTES['contempt']['description']
                )
            elif regex_match and not llm_result.is_contempt and llm_result.confidence >= 0.7:
                # LLM says regex was a false positive with high confidence
                return None

        # Step 3: Fall back to regex result if no LLM or LLM uncertain
        if regex_match:
            return PatternMatch(
                pattern_type='negative',
                pattern_name='contempt',
                horseman='contempt',
                score_impact=-8,  # Highest negative impact
                evidence=regex_evidence,
                antidote=self.ANTIDOTES['contempt']['description']
            )

        return None

    def get_llm_contempt_analysis(self) -> List[Dict]:
        """Get LLM contempt analysis results for comparison with regex."""
        return self._llm_contempt_results

    def detect_defensiveness(self, text: str) -> Optional[PatternMatch]:
        """Detect defensiveness patterns in text."""
        for pattern in self.defensiveness_re:
            match = pattern.search(text)
            if match:
                return PatternMatch(
                    pattern_type='negative',
                    pattern_name='defensiveness',
                    horseman='defensiveness',
                    score_impact=-4,
                    evidence=match.group(0),
                    antidote=self.ANTIDOTES['defensiveness']['description']
                )
        return None

    def detect_stonewalling(self, text: str,
                           response_time_minutes: Optional[float] = None,
                           is_after_conflict: bool = False) -> Optional[PatternMatch]:
        """
        Detect stonewalling patterns.

        Stonewalling is detected through:
        1. Minimal responses after emotional content
        2. Long response delays during conflict (>2 hours)
        3. Withdrawal phrases
        """
        # Check phrases
        for pattern in self.stonewalling_re:
            match = pattern.search(text)
            if match:
                return PatternMatch(
                    pattern_type='negative',
                    pattern_name='stonewalling',
                    horseman='stonewalling',
                    score_impact=-6,
                    evidence=match.group(0),
                    antidote=self.ANTIDOTES['stonewalling']['description']
                )

        # Check for long delay after conflict
        if is_after_conflict and response_time_minutes and response_time_minutes > 120:
            return PatternMatch(
                pattern_type='negative',
                pattern_name='stonewalling',
                horseman='stonewalling',
                score_impact=-6,
                evidence=f'Resposta demorada após conflito ({response_time_minutes:.0f}min)',
                antidote=self.ANTIDOTES['stonewalling']['description']
            )

        return None

    def detect_all(self, text: str,
                   response_time_minutes: Optional[float] = None,
                   is_after_conflict: bool = False,
                   context: str = "") -> List[PatternMatch]:
        """
        Detect all Four Horsemen patterns in text.

        Args:
            text: Message to analyze
            response_time_minutes: Time since previous message
            is_after_conflict: If this follows a conflict
            context: Previous messages for LLM context

        Returns:
            List of detected negative patterns
        """
        matches = []

        # Check each horseman
        criticism = self.detect_criticism(text)
        if criticism:
            matches.append(criticism)

        contempt = self.detect_contempt(text, context=context)
        if contempt:
            matches.append(contempt)

        defensiveness = self.detect_defensiveness(text)
        if defensiveness:
            matches.append(defensiveness)

        stonewalling = self.detect_stonewalling(text, response_time_minutes, is_after_conflict)
        if stonewalling:
            matches.append(stonewalling)

        return matches


class PositivePatternDetector:
    """
    Detects positive relationship patterns based on:
    - Gottman's repair attempts
    - Stafford & Canary's maintenance behaviors
    - Reis & Shaver's responsiveness model
    """

    # Repair attempt patterns (PT-BR)
    REPAIR_PATTERNS = [
        r'\bdesculpa\b',
        r'\bperdão\b',
        r'\bme perdoa\b',
        r'\bnão quis\s+(?:dizer|fazer|magoar)\b',
        r'\bfoi mal\b',
        r'\beu errei\b',
        r'\bvocê tem razão\b',
        r'\beu exagerei\b',
        r'\bpodemos recomeçar\b',
        r'\bvamos tentar de novo\b',
        r'\bnão vamos brigar\b',
        r'\beu te amo\b.*(?:desculpa|perdão)',  # Love + apology
        r'\bvamos resolver\b',
        r'😅.*(?:desculpa|perdão)',  # Humor + apology
        r'\bera brincadeira\b',
    ]

    # Affection expression patterns (PT-BR)
    AFFECTION_PATTERNS = [
        r'\bte amo\b',
        r'\bamo você\b',
        r'\bsaudade\b',
        r'\bsaudades\b',
        r'\bte adoro\b',
        r'\bmeu amor\b',
        r'\bquerido\b',
        r'\bquerida\b',
        r'\bfofo\b',
        r'\bfofa\b',
        r'\blindo\b',
        r'\blinda\b',
        r'\bmaravilhoso\b',
        r'\bmaravilhosa\b',
        r'❤️',
        r'💕',
        r'😘',
        r'😍',
        r'🥰',
        r'\bte quero\b',
        r'\bpaixão\b',
    ]

    # Gratitude patterns (PT-BR)
    GRATITUDE_PATTERNS = [
        r'\bobrigad[oa]\s+por\b',
        r'\bmuito obrigad[oa]\b',
        r'\bagradeço\b',
        r'\bvaleu\s+(?:por|pela|pelo)\b',
        r'\bque bom que você\b',
        r'\bvocê é o melhor\b',
        r'\bvocê é a melhor\b',
        r'\bnão sei o que faria sem você\b',
        r'\bsorte de ter você\b',
    ]

    # Supportive response patterns (PT-BR)
    SUPPORT_PATTERNS = [
        r'\bestou aqui\b',
        r'\bconte comigo\b',
        r'\bposso ajudar\b',
        r'\bo que você precisa\b',
        r'\bestou com você\b',
        r'\bvai ficar tudo bem\b',
        r'\bvocê consegue\b',
        r'\bacredito em você\b',
        r'\bentendo\b',
        r'\bque difícil\b',
        r'\bsinto muito\b',
        r'\bimagino como você\b',
        r'\bdeve ser difícil\b',
    ]

    # Future planning patterns (PT-BR) - Shared meaning
    FUTURE_PLANNING_PATTERNS = [
        r'\bvamos\s+(?:fazer|planejar|marcar)\b',
        r'\bnosso\s+(?:plano|projeto|futuro)\b',
        r'\bquando a gente\b',
        r'\bno futuro\b',
        r'\bjuntos\b',
        r'\bnossa\s+(?:casa|família|vida)\b',
        r'\bsonho\s+(?:nosso|com você)\b',
        r'\bquero\s+(?:envelhecer|ficar|estar)\s+com você\b',
    ]

    # Active listening patterns (PT-BR)
    ACTIVE_LISTENING_PATTERNS = [
        r'\bcomo foi\b',
        r'\bme conta\b',
        r'\bconte mais\b',
        r'\be aí\?',
        r'\bo que aconteceu\b',
        r'\bcomo você está\b',
        r'\btudo bem\?\s*$',
        r'\bquer conversar\b',
        r'\bestou ouvindo\b',
        r'\bsério\?\s+(?:me conta|e aí)\b',
    ]

    # Deep disclosure patterns (vulnerability markers)
    DISCLOSURE_PATTERNS = [
        r'\beu sinto\b',
        r'\bestou com medo\b',
        r'\btenho medo\b',
        r'\bestou preocupad[oa]\b',
        r'\bme sinto\b',
        r'\bestou ansios[oa]\b',
        r'\bestou triste\b',
        r'\bestou feliz\b',
        r'\bpreciso te contar\b',
        r'\bnunca contei\b',
        r'\bpra ser honest[oa]\b',
        r'\bna verdade\b.*(?:sinto|penso|acho)\b',
    ]

    # Understanding/validation patterns
    UNDERSTANDING_PATTERNS = [
        r'\bfaz sentido\b',
        r'\bentendo você\b',
        r'\bte entendo\b',
        r'\bvocê está cert[oa]\b',
        r'\bconcordo\b',
        r'\btem razão\b',
        r'\bisso é válido\b',
        r'\bé compreensível\b',
        r'\bnormal sentir\b',
    ]

    # Assurance patterns (commitment)
    ASSURANCE_PATTERNS = [
        r'\bsempre vou\b',
        r'\bnunca vou te deixar\b',
        r'\bestou aqui pra você\b',
        r'\bpode contar comigo\b',
        r'\bvou te apoiar\b',
        r'\bsomos um time\b',
        r'\bjuntos nisso\b',
        r'\bpra sempre\b',
        r'\bnão vou desistir\b',
    ]

    def __init__(self, llm_analyzer: 'LLMRelationshipAnalyzer' = None, use_llm: bool = False):
        """
        Initialize the positive pattern detector.

        Args:
            llm_analyzer: Optional LLM analyzer for repair validation
            use_llm: If True, use LLM to validate repair attempt authenticity
        """
        # Compile patterns
        self.repair_re = [re.compile(p, re.IGNORECASE) for p in self.REPAIR_PATTERNS]
        self.affection_re = [re.compile(p, re.IGNORECASE) for p in self.AFFECTION_PATTERNS]
        self.gratitude_re = [re.compile(p, re.IGNORECASE) for p in self.GRATITUDE_PATTERNS]
        self.support_re = [re.compile(p, re.IGNORECASE) for p in self.SUPPORT_PATTERNS]
        self.future_re = [re.compile(p, re.IGNORECASE) for p in self.FUTURE_PLANNING_PATTERNS]
        self.listening_re = [re.compile(p, re.IGNORECASE) for p in self.ACTIVE_LISTENING_PATTERNS]
        self.disclosure_re = [re.compile(p, re.IGNORECASE) for p in self.DISCLOSURE_PATTERNS]
        self.understanding_re = [re.compile(p, re.IGNORECASE) for p in self.UNDERSTANDING_PATTERNS]
        self.assurance_re = [re.compile(p, re.IGNORECASE) for p in self.ASSURANCE_PATTERNS]

        # LLM enhancement
        self.llm_analyzer = llm_analyzer
        self.use_llm = use_llm and llm_analyzer is not None

        # Track LLM repair validation results
        self._llm_repair_results: List[Dict] = []

    def _detect_pattern(self, text: str, patterns: List[re.Pattern],
                        name: str, score: int) -> Optional[PatternMatch]:
        """Generic pattern detection helper."""
        for pattern in patterns:
            match = pattern.search(text)
            if match:
                return PatternMatch(
                    pattern_type='positive',
                    pattern_name=name,
                    score_impact=score,
                    evidence=match.group(0)
                )
        return None

    def detect_repair_attempt(self, text: str, context: str = "") -> Optional[PatternMatch]:
        """
        Detect repair attempts (conflict de-escalation).

        With LLM enhancement:
        - Validates if repair is genuine vs blame-shifting
        - "Você tem razão, MAS você também..." = NOT a genuine repair
        - Adjusts score based on authenticity

        Args:
            text: Message text to analyze
            context: Conflict context for validation

        Returns:
            PatternMatch if repair detected, None otherwise
        """
        # Step 1: Regex detection
        regex_match = self._detect_pattern(text, self.repair_re, 'repair_attempt', +5)

        if regex_match is None:
            return None

        # Step 2: LLM validation (if enabled)
        if self.use_llm:
            llm_result = self.llm_analyzer.validate_repair_attempt(text, context)

            # Store for analysis
            self._llm_repair_results.append({
                'text': text[:100],
                'regex_detected': True,
                'llm_genuine': llm_result.is_genuine,
                'llm_confidence': llm_result.confidence,
                'has_blame_shifting': llm_result.has_blame_shifting,
                'responsibility_level': llm_result.responsibility_level,
                'llm_reasoning': llm_result.reasoning,
            })

            # Adjust score based on authenticity
            if llm_result.is_genuine and llm_result.confidence >= 0.6:
                # Genuine repair - full or enhanced points
                if llm_result.responsibility_level == 'full':
                    score = +7  # Extra points for full responsibility
                else:
                    score = +5  # Standard repair points
            elif llm_result.has_blame_shifting:
                # Fake repair that shifts blame - no points or negative
                score = -2  # Penalize blame-shifting disguised as repair
            else:
                # Uncertain - give partial credit
                score = +2

            return PatternMatch(
                pattern_type='positive' if score > 0 else 'negative',
                pattern_name='repair_attempt' if score > 0 else 'fake_repair',
                score_impact=score,
                evidence=f"[LLM: {llm_result.responsibility_level}] {regex_match.evidence}"
            )

        return regex_match

    def get_llm_repair_analysis(self) -> List[Dict]:
        """Get LLM repair validation results for analysis."""
        return self._llm_repair_results

    def detect_affection(self, text: str) -> Optional[PatternMatch]:
        """Detect affection expressions."""
        return self._detect_pattern(text, self.affection_re, 'affection', +3)

    def detect_gratitude(self, text: str) -> Optional[PatternMatch]:
        """Detect gratitude expressions."""
        return self._detect_pattern(text, self.gratitude_re, 'gratitude', +3)

    def detect_support(self, text: str) -> Optional[PatternMatch]:
        """Detect supportive responses."""
        return self._detect_pattern(text, self.support_re, 'support', +4)

    def detect_future_planning(self, text: str) -> Optional[PatternMatch]:
        """Detect future planning (shared meaning)."""
        return self._detect_pattern(text, self.future_re, 'future_planning', +3)

    def detect_active_listening(self, text: str) -> Optional[PatternMatch]:
        """Detect active listening behaviors."""
        return self._detect_pattern(text, self.listening_re, 'active_listening', +4)

    def detect_disclosure(self, text: str) -> Optional[PatternMatch]:
        """Detect emotional disclosure (vulnerability)."""
        return self._detect_pattern(text, self.disclosure_re, 'disclosure', +4)

    def detect_understanding(self, text: str) -> Optional[PatternMatch]:
        """Detect understanding/validation responses."""
        return self._detect_pattern(text, self.understanding_re, 'understanding', +3)

    def detect_assurance(self, text: str) -> Optional[PatternMatch]:
        """Detect commitment assurances."""
        return self._detect_pattern(text, self.assurance_re, 'assurance', +4)

    def detect_all(self, text: str, context: str = "") -> List[PatternMatch]:
        """
        Detect all positive patterns in text.

        Args:
            text: Message to analyze
            context: Previous messages for LLM context (used by repair validation)

        Returns:
            List of detected positive patterns
        """
        matches = []

        # Repair attempt needs context for LLM validation
        repair = self.detect_repair_attempt(text, context=context)
        if repair:
            matches.append(repair)

        # Other detectors (no LLM enhancement yet)
        simple_detectors = [
            self.detect_affection,
            self.detect_gratitude,
            self.detect_support,
            self.detect_future_planning,
            self.detect_active_listening,
            self.detect_disclosure,
            self.detect_understanding,
            self.detect_assurance,
        ]

        for detector in simple_detectors:
            match = detector(text)
            if match:
                matches.append(match)

        return matches


class ResponsivenessAnalyzer:
    """
    Analyzes perceived partner responsiveness based on Reis & Shaver's model.

    Responsiveness = Understanding + Validation + Caring

    Key indicators:
    - Response elaboration (depth)
    - Acknowledgment of emotional content
    - Follow-up questions
    - Response timing to emotional messages
    """

    # Emotional content markers
    EMOTIONAL_MARKERS = [
        r'\bestou\s+(?:triste|feliz|ansios[oa]|preocupad[oa]|nervos[oa]|com medo)\b',
        r'\bme sinto\b',
        r'\bsinto\s+(?:falta|saudade|medo|raiva)\b',
        r'\bestou\s+(?:chorando|muito|tão)\b',
        r'\bpreciso\s+(?:de você|conversar|desabafar)\b',
        r'\bnão aguento\b',
        r'\bestou mal\b',
        r'\bdia difícil\b',
        r'😢',
        r'😭',
        r'😔',
        r'😞',
    ]

    # Dismissive response markers
    DISMISSIVE_PATTERNS = [
        r'^ok$',
        r'^tá$',
        r'^hm+$',
        r'^ah$',
        r'^entendi$',
        r'^sei$',
        r'^blz$',
    ]

    def __init__(self):
        self.emotional_re = [re.compile(p, re.IGNORECASE) for p in self.EMOTIONAL_MARKERS]
        self.dismissive_re = [re.compile(p, re.IGNORECASE) for p in self.DISMISSIVE_PATTERNS]

    def is_emotional_message(self, text: str) -> bool:
        """Check if message contains emotional content."""
        for pattern in self.emotional_re:
            if pattern.search(text):
                return True
        return False

    def is_dismissive_response(self, text: str) -> bool:
        """Check if response is dismissive (minimal to emotional content)."""
        text = text.strip()
        for pattern in self.dismissive_re:
            if pattern.match(text):
                return True
        return len(text) < 5

    def calculate_response_quality(self,
                                   original_msg: str,
                                   response_msg: str,
                                   response_time_minutes: float) -> Dict:
        """
        Calculate response quality score.

        Returns dict with:
        - score: 0-100
        - is_emotional_context: bool
        - is_dismissive: bool
        - response_depth: 'deep', 'moderate', 'minimal'
        """
        is_emotional = self.is_emotional_message(original_msg)
        is_dismissive = self.is_dismissive_response(response_msg)

        # Calculate response depth
        word_count = len(response_msg.split())
        if word_count >= 15:
            depth = 'deep'
            depth_score = 100
        elif word_count >= 8:
            depth = 'moderate'
            depth_score = 70
        elif word_count >= 3:
            depth = 'minimal'
            depth_score = 40
        else:
            depth = 'minimal'
            depth_score = 20

        # Penalize dismissive responses to emotional content
        if is_emotional and is_dismissive:
            score = 20
        elif is_emotional:
            # Higher standards for emotional responses
            if response_time_minutes > 30:
                score = max(20, depth_score - 30)
            else:
                score = depth_score
        else:
            score = depth_score

        return {
            'score': score,
            'is_emotional_context': is_emotional,
            'is_dismissive': is_dismissive,
            'response_depth': depth,
            'word_count': word_count,
            'response_time_minutes': response_time_minutes
        }


class RelationshipPatternAnalyzer:
    """
    Main analyzer combining all pattern detectors.

    Provides comprehensive analysis based on:
    - Gottman's research (Four Horsemen, 5:1 ratio)
    - Interpersonal Process Model (responsiveness)
    - Maintenance Behaviors (Stafford & Canary)

    LLM Enhancement:
    - Optional LLM-powered contempt detection (catches sarcasm)
    - Optional LLM-powered repair validation (detects blame-shifting)
    - Designed for maximum quality baseline
    """

    def __init__(self, llm_analyzer: 'LLMRelationshipAnalyzer' = None, use_llm: bool = False):
        """
        Initialize the relationship pattern analyzer.

        Args:
            llm_analyzer: Optional LLM analyzer for enhanced detection
            use_llm: If True, use LLM for validation (higher accuracy, higher cost)
        """
        self.llm_analyzer = llm_analyzer
        self.use_llm = use_llm and llm_analyzer is not None

        self.gottman = GottmanPatternDetector(
            llm_analyzer=llm_analyzer,
            use_llm=use_llm
        )
        self.positive = PositivePatternDetector(
            llm_analyzer=llm_analyzer,
            use_llm=use_llm
        )
        self.responsiveness = ResponsivenessAnalyzer()

    def analyze_message(self, text: str,
                        sender: Optional[str] = None,
                        timestamp: Optional[datetime] = None,
                        response_time_minutes: Optional[float] = None,
                        is_after_conflict: bool = False,
                        previous_message: Optional[str] = None,
                        context: List[str] = None) -> List[PatternMatch]:
        """
        Analyze a single message for all patterns.

        Args:
            text: Message text to analyze
            sender: Who sent the message
            timestamp: When message was sent
            response_time_minutes: Time since previous message
            is_after_conflict: If this follows a conflict
            previous_message: The previous message (for context)
            context: List of recent messages for LLM context

        Returns:
            List of detected patterns with scores.
        """
        matches = []
        context_str = '\n'.join(context[-5:]) if context else (previous_message or "")

        # Detect negative patterns (Four Horsemen)
        horsemen = self.gottman.detect_all(
            text,
            response_time_minutes=response_time_minutes,
            is_after_conflict=is_after_conflict,
            context=context_str
        )
        for match in horsemen:
            match.sender = sender
            match.timestamp = timestamp
            match.message_text = text
            matches.append(match)

        # Detect positive patterns (with context for repair validation)
        positive = self.positive.detect_all(text, context=context_str)
        for match in positive:
            match.sender = sender
            match.timestamp = timestamp
            match.message_text = text
            matches.append(match)

        # Check for dismissive response to emotional content
        if previous_message and self.responsiveness.is_emotional_message(previous_message):
            if self.responsiveness.is_dismissive_response(text):
                # If LLM is enabled, get more nuanced assessment
                if self.use_llm and self.llm_analyzer:
                    quality = self.llm_analyzer.assess_response_quality(previous_message, text)
                    if quality.is_dismissive:
                        matches.append(PatternMatch(
                            pattern_type='negative',
                            pattern_name='dismissive_response',
                            score_impact=-3 if quality.overall_quality < 30 else -2,
                            sender=sender,
                            timestamp=timestamp,
                            message_text=text,
                            evidence=f'[LLM] {quality.reasoning[:50]}' if quality.reasoning else 'Resposta curta a conteúdo emocional'
                        ))
                else:
                    matches.append(PatternMatch(
                        pattern_type='negative',
                        pattern_name='dismissive_response',
                        score_impact=-2,
                        sender=sender,
                        timestamp=timestamp,
                        message_text=text,
                        evidence='Resposta curta a conteúdo emocional'
                    ))

        return matches

    def analyze_conversation(self, df: pd.DataFrame,
                            sender_col: str = 'sender',
                            message_col: str = 'message',
                            datetime_col: str = 'datetime') -> PatternSummary:
        """
        Analyze an entire conversation for patterns.

        Args:
            df: DataFrame with messages
            sender_col: Column name for sender
            message_col: Column name for message text
            datetime_col: Column name for timestamp

        Returns:
            PatternSummary with all detected patterns and statistics
        """
        summary = PatternSummary()
        summary.four_horsemen_counts = {
            'criticism': 0,
            'contempt': 0,
            'defensiveness': 0,
            'stonewalling': 0
        }

        df_sorted = df.sort_values(datetime_col).copy()
        df_sorted['prev_message'] = df_sorted[message_col].shift(1)
        df_sorted['prev_sender'] = df_sorted[sender_col].shift(1)
        df_sorted['prev_time'] = df_sorted[datetime_col].shift(1)

        # Track if we're in conflict context
        in_conflict = False
        conflict_decay = 0

        for idx, row in df_sorted.iterrows():
            text = str(row.get(message_col, ''))
            if not text or text == 'nan':
                continue

            sender = row.get(sender_col)
            timestamp = row.get(datetime_col)
            prev_msg = row.get('prev_message')
            prev_time = row.get('prev_time')

            # Calculate response time
            response_time = None
            if pd.notna(prev_time) and pd.notna(timestamp):
                response_time = (timestamp - prev_time).total_seconds() / 60

            # Analyze message
            matches = self.analyze_message(
                text,
                sender=sender,
                timestamp=timestamp,
                response_time_minutes=response_time,
                is_after_conflict=in_conflict,
                previous_message=str(prev_msg) if pd.notna(prev_msg) else None
            )

            # Update summary
            for match in matches:
                summary.matches.append(match)

                if match.pattern_type == 'positive':
                    summary.total_positive += 1
                    pattern_name = match.pattern_name
                    summary.positive_counts[pattern_name] = \
                        summary.positive_counts.get(pattern_name, 0) + 1
                else:
                    summary.total_negative += 1
                    if match.horseman:
                        summary.four_horsemen_counts[match.horseman] += 1
                        in_conflict = True
                        conflict_decay = 5  # Messages until conflict context clears

            # Decay conflict context
            if conflict_decay > 0:
                conflict_decay -= 1
                if conflict_decay == 0:
                    in_conflict = False

        # Calculate Gottman ratio
        if summary.total_negative > 0:
            summary.positive_ratio = summary.total_positive / summary.total_negative
        else:
            summary.positive_ratio = summary.total_positive if summary.total_positive > 0 else 5.0

        # Generate alerts for concerning patterns
        summary.alerts = self._generate_alerts(summary)

        return summary

    def _generate_alerts(self, summary: PatternSummary) -> List[Dict]:
        """Generate alerts for concerning patterns."""
        alerts = []

        # Check Gottman ratio
        if summary.positive_ratio < 5.0 and summary.total_negative > 0:
            alerts.append({
                'type': 'ratio_warning',
                'severity': 'high' if summary.positive_ratio < 3.0 else 'medium',
                'message': f'Proporção positivo/negativo de {summary.positive_ratio:.1f}:1 '
                          f'(meta: 5:1 segundo Gottman)',
                'recommendation': 'Aumentar expressões de carinho e gratidão'
            })

        # Check Four Horsemen
        for horseman, count in summary.four_horsemen_counts.items():
            if count >= 3:
                antidote = self.gottman.ANTIDOTES[horseman]
                alerts.append({
                    'type': 'horseman_warning',
                    'horseman': horseman,
                    'count': count,
                    'severity': 'high' if count >= 5 else 'medium',
                    'message': f'{horseman.title()} detectado {count} vezes',
                    'antidote': antidote['name'],
                    'recommendation': antidote['description']
                })

        # Special alert for contempt (most destructive)
        if summary.four_horsemen_counts.get('contempt', 0) >= 2:
            alerts.append({
                'type': 'critical_warning',
                'severity': 'critical',
                'message': 'Contempt é o preditor mais forte de dissolução do relacionamento',
                'recommendation': 'Priorizar construção de cultura de apreciação'
            })

        return alerts

    def calculate_communication_health_score(self, summary: PatternSummary) -> Dict:
        """
        Calculate communication health score from pattern summary.

        Based on:
        - Absence of Four Horsemen
        - Repair attempts
        - Positive to negative ratio
        """
        # Base score
        score = 70

        # Deduct for Four Horsemen
        horsemen_penalty = (
            summary.four_horsemen_counts.get('criticism', 0) * 2 +
            summary.four_horsemen_counts.get('contempt', 0) * 4 +  # Double penalty
            summary.four_horsemen_counts.get('defensiveness', 0) * 1.5 +
            summary.four_horsemen_counts.get('stonewalling', 0) * 2
        )
        score -= min(horsemen_penalty, 40)  # Max 40 point penalty

        # Bonus for repair attempts
        repair_count = summary.positive_counts.get('repair_attempt', 0)
        repair_bonus = min(repair_count * 2, 15)  # Max 15 point bonus
        score += repair_bonus

        # Bonus for good ratio
        if summary.positive_ratio >= 5.0:
            score += 10
        elif summary.positive_ratio >= 3.0:
            score += 5

        # Ensure score is in valid range
        score = max(0, min(100, score))

        return {
            'score': round(score),
            'ratio': round(summary.positive_ratio, 1),
            'horsemen_counts': summary.four_horsemen_counts,
            'repair_attempts': repair_count,
            'interpretation': self._interpret_comm_score(score)
        }

    def _interpret_comm_score(self, score: float) -> str:
        """Interpret communication health score."""
        if score >= 85:
            return 'Comunicação saudável com padrões positivos fortes'
        elif score >= 70:
            return 'Boa comunicação com espaço para melhorias'
        elif score >= 55:
            return 'Comunicação estável mas alguns padrões precisam atenção'
        elif score >= 40:
            return 'Padrões de comunicação preocupantes detectados'
        else:
            return 'Comunicação precisa de atenção urgente'
