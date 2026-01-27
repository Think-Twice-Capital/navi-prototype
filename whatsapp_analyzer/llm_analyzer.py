"""
LLM-Enhanced Relationship Analyzer

Provides nuanced analysis of relationship patterns using Claude Opus 4.5.
This module establishes a quality baseline for understanding complex
communication patterns that regex-based detection cannot capture.

Strategy:
- Phase 1: Maximum quality with Claude Opus 4.5 (every message)
- Phase 2 (future): Cost optimization based on accuracy comparison

Research Foundation:
- Gottman's Four Horsemen and Sound Relationship House
- Interpersonal Process Model (Reis & Shaver)
- Relationship Maintenance Behaviors (Stafford & Canary)
"""

import json
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import anthropic


# Cost per million tokens for different models (as of 2024)
MODEL_COSTS = {
    'claude-opus-4-5-20250514': {'input': 15.00, 'output': 75.00},
    'claude-sonnet-4-20250514': {'input': 3.00, 'output': 15.00},
    'claude-3-5-haiku-20241022': {'input': 0.25, 'output': 1.25},
}


@dataclass
class AnalysisCost:
    """Cost tracking for a single LLM analysis."""
    input_tokens: int
    output_tokens: int
    model: str
    analysis_type: str  # contempt, response_quality, repair, etc.
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def cost_usd(self) -> float:
        """Calculate estimated cost in USD."""
        costs = MODEL_COSTS.get(self.model, {'input': 15.00, 'output': 75.00})
        return (
            (self.input_tokens / 1_000_000) * costs['input'] +
            (self.output_tokens / 1_000_000) * costs['output']
        )


class CostTracker:
    """Tracks LLM API usage and costs for analysis optimization."""

    def __init__(self):
        self.analyses: List[AnalysisCost] = []
        self._costs_by_type: Dict[str, List[AnalysisCost]] = defaultdict(list)

    def log_analysis(self, cost: AnalysisCost) -> None:
        """Log a completed analysis with its costs."""
        self.analyses.append(cost)
        self._costs_by_type[cost.analysis_type].append(cost)

    def get_total_cost(self) -> float:
        """Get total cost in USD across all analyses."""
        return sum(a.cost_usd for a in self.analyses)

    def get_total_tokens(self) -> Tuple[int, int]:
        """Get total input and output tokens."""
        input_tokens = sum(a.input_tokens for a in self.analyses)
        output_tokens = sum(a.output_tokens for a in self.analyses)
        return input_tokens, output_tokens

    def get_cost_by_type(self) -> Dict[str, Dict[str, Any]]:
        """Get cost breakdown by analysis type."""
        result = {}
        for analysis_type, costs in self._costs_by_type.items():
            total_input = sum(c.input_tokens for c in costs)
            total_output = sum(c.output_tokens for c in costs)
            total_cost = sum(c.cost_usd for c in costs)
            result[analysis_type] = {
                'count': len(costs),
                'input_tokens': total_input,
                'output_tokens': total_output,
                'cost_usd': round(total_cost, 4),
            }
        return result

    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive cost report."""
        input_tokens, output_tokens = self.get_total_tokens()
        return {
            'totalCost': {
                'inputTokens': input_tokens,
                'outputTokens': output_tokens,
                'estimatedUSD': round(self.get_total_cost(), 4),
            },
            'analysisBreakdown': self.get_cost_by_type(),
            'totalAnalyses': len(self.analyses),
        }


@dataclass
class ContemptResult:
    """Result of contempt/sarcasm detection."""
    is_contempt: bool
    confidence: float  # 0.0-1.0
    contempt_type: str  # sarcasm, mockery, dismissive, superiority, none
    reasoning: str
    severity: str  # mild, moderate, severe

    def to_dict(self) -> Dict:
        return {
            'is_contempt': self.is_contempt,
            'confidence': self.confidence,
            'type': self.contempt_type,
            'reasoning': self.reasoning,
            'severity': self.severity,
        }


@dataclass
class ResponseQuality:
    """Result of response quality assessment."""
    understanding_score: int  # 0-100
    validation_score: int  # 0-100
    caring_score: int  # 0-100
    overall_quality: int  # 0-100
    is_dismissive: bool
    reasoning: str

    def to_dict(self) -> Dict:
        return {
            'understanding_score': self.understanding_score,
            'validation_score': self.validation_score,
            'caring_score': self.caring_score,
            'overall_quality': self.overall_quality,
            'is_dismissive': self.is_dismissive,
            'reasoning': self.reasoning,
        }


@dataclass
class RepairResult:
    """Result of repair attempt authenticity check."""
    is_genuine: bool
    confidence: float  # 0.0-1.0
    responsibility_level: str  # none, partial, full
    has_blame_shifting: bool
    reasoning: str

    def to_dict(self) -> Dict:
        return {
            'is_genuine': self.is_genuine,
            'confidence': self.confidence,
            'responsibility_level': self.responsibility_level,
            'has_blame_shifting': self.has_blame_shifting,
            'reasoning': self.reasoning,
        }


@dataclass
class VulnerabilityResult:
    """Result of vulnerability depth assessment."""
    depth_level: str  # surface, moderate, deep
    depth_score: int  # 0-100
    invites_reciprocity: bool
    topics: List[str]  # emotional topics disclosed
    reasoning: str

    def to_dict(self) -> Dict:
        return {
            'depth_level': self.depth_level,
            'depth_score': self.depth_score,
            'invites_reciprocity': self.invites_reciprocity,
            'topics': self.topics,
            'reasoning': self.reasoning,
        }


@dataclass
class SharedMeaningResult:
    """Result of shared meaning/future planning assessment."""
    commitment_level: str  # casual, moderate, strong
    commitment_score: int  # 0-100
    timeframe: str  # immediate, near_future, long_term
    goal_alignment: bool
    reasoning: str

    def to_dict(self) -> Dict:
        return {
            'commitment_level': self.commitment_level,
            'commitment_score': self.commitment_score,
            'timeframe': self.timeframe,
            'goal_alignment': self.goal_alignment,
            'reasoning': self.reasoning,
        }


@dataclass
class MessageAnalysis:
    """Comprehensive analysis result for a single message."""
    message_id: Optional[str]
    message_text: str
    sender: Optional[str]
    timestamp: Optional[datetime]

    contempt: Optional[ContemptResult] = None
    response_quality: Optional[ResponseQuality] = None
    repair: Optional[RepairResult] = None
    vulnerability: Optional[VulnerabilityResult] = None
    shared_meaning: Optional[SharedMeaningResult] = None

    def to_dict(self) -> Dict:
        result = {
            'message_id': self.message_id,
            'message_text': self.message_text[:100] + '...' if len(self.message_text) > 100 else self.message_text,
            'sender': self.sender,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
        }
        if self.contempt:
            result['contempt'] = self.contempt.to_dict()
        if self.response_quality:
            result['response_quality'] = self.response_quality.to_dict()
        if self.repair:
            result['repair'] = self.repair.to_dict()
        if self.vulnerability:
            result['vulnerability'] = self.vulnerability.to_dict()
        if self.shared_meaning:
            result['shared_meaning'] = self.shared_meaning.to_dict()
        return result


class LLMRelationshipAnalyzer:
    """
    LLM-powered analysis for nuanced relationship patterns.

    Uses Claude Opus 4.5 for maximum quality baseline. All messages are
    analyzed to establish accuracy metrics before optimizing for cost.

    Key Analysis Types:
    1. Contempt & Sarcasm Detection - highest impact on relationship outcomes
    2. Response Quality - empathy, validation, caring assessment
    3. Repair Attempt Authenticity - genuine vs blame-shifting apologies
    4. Vulnerability Depth - emotional disclosure quality
    5. Shared Meaning - future planning and commitment level
    """

    # Prompts based on validated relationship research
    CONTEMPT_PROMPT = """You are an expert relationship therapist trained in Gottman's research.

Analyze this message for contempt - the most destructive relationship pattern.

Message: "{text}"
Context (previous messages): "{context}"

Contempt indicators include:
- Sarcasm or mockery
- Eye-rolling language or dismissive tone
- Superiority or disrespect
- Dismissiveness
- Character attacks disguised as humor

IMPORTANT: Be careful to distinguish:
- Genuine congratulations ("Parabéns pelo seu aniversário!") from sarcastic ones ("Parabéns, você só levou 3 horas")
- Playful teasing between close partners from hostile contempt
- Context-dependent emoji use (🙄 can be playful or contemptuous)

Respond with ONLY valid JSON (no markdown, no explanation outside JSON):
{{
  "is_contempt": boolean,
  "confidence": 0.0-1.0,
  "type": "sarcasm" | "mockery" | "dismissive" | "superiority" | "none",
  "reasoning": "brief explanation in Portuguese",
  "severity": "mild" | "moderate" | "severe"
}}"""

    RESPONSE_QUALITY_PROMPT = """You are an expert in interpersonal communication and attachment theory.

Evaluate this response to an emotional message.

Original message: "{original}"
Response: "{response}"

Based on Reis & Shaver's Interpersonal Process Model, assess:
1. Understanding - Does the responder grasp the emotional content?
2. Validation - Is the emotion acknowledged as legitimate?
3. Caring - Is support or concern expressed?

IMPORTANT: Quality is not about length. A short "Entendo, quer conversar?" can be high quality.
A long response like "Ah tá, e o que você quer que eu faça?" is dismissive despite length.

Respond with ONLY valid JSON (no markdown, no explanation outside JSON):
{{
  "understanding_score": 0-100,
  "validation_score": 0-100,
  "caring_score": 0-100,
  "overall_quality": 0-100,
  "is_dismissive": boolean,
  "reasoning": "brief explanation in Portuguese"
}}"""

    REPAIR_PROMPT = """You are an expert relationship therapist assessing repair attempts.

Analyze this potential repair attempt for authenticity.

Message: "{text}"
Conflict context: "{context}"

A genuine repair attempt:
- Takes responsibility (even partial)
- Shows remorse without defensiveness
- Does NOT shift blame to partner

A fake repair masks blame:
- "Você tem razão, MAS você também..." = blame-shifting
- "Desculpa, mas se você não tivesse..." = conditional apology
- "Ok, eu errei, feliz agora?" = sarcastic pseudo-repair

Respond with ONLY valid JSON (no markdown, no explanation outside JSON):
{{
  "is_genuine": boolean,
  "confidence": 0.0-1.0,
  "responsibility_level": "none" | "partial" | "full",
  "has_blame_shifting": boolean,
  "reasoning": "brief explanation in Portuguese"
}}"""

    VULNERABILITY_PROMPT = """You are an expert in intimacy and emotional disclosure.

Assess the depth of emotional vulnerability in this message.

Message: "{text}"
Context: "{context}"

Vulnerability levels:
- Surface: General statements ("estou cansado")
- Moderate: Specific emotions ("estou frustrado com o trabalho")
- Deep: Core fears, hopes, insecurities ("tenho medo de não ser suficiente")

Also assess if the disclosure invites reciprocity from partner.

Respond with ONLY valid JSON (no markdown, no explanation outside JSON):
{{
  "depth_level": "surface" | "moderate" | "deep",
  "depth_score": 0-100,
  "invites_reciprocity": boolean,
  "topics": ["list", "of", "emotional", "topics"],
  "reasoning": "brief explanation in Portuguese"
}}"""

    SHARED_MEANING_PROMPT = """You are an expert in relationship commitment and shared goals.

Assess the shared meaning and future planning in this message.

Message: "{text}"
Context: "{context}"

Commitment levels:
- Casual: "Vamos jantar" (immediate, low commitment)
- Moderate: "Vamos viajar nas férias" (near future, moderate)
- Strong: "Quero construir nossa vida juntos" (long-term, high)

Also assess if there's evidence of aligned goals and values.

Respond with ONLY valid JSON (no markdown, no explanation outside JSON):
{{
  "commitment_level": "casual" | "moderate" | "strong",
  "commitment_score": 0-100,
  "timeframe": "immediate" | "near_future" | "long_term",
  "goal_alignment": boolean,
  "reasoning": "brief explanation in Portuguese"
}}"""

    def __init__(self,
                 model: str = "claude-opus-4-5-20250514",
                 analyze_all: bool = True):
        """
        Initialize the LLM analyzer.

        Args:
            model: Claude model to use (default: Opus 4.5 for maximum quality)
            analyze_all: If True, analyze every message (baseline mode)
        """
        self.client = anthropic.Anthropic()
        self.model = model
        self.analyze_all = analyze_all
        self.cost_tracker = CostTracker()
        self._sample_analyses: List[Dict] = []
        self._max_samples = 10  # Keep sample analyses for output

    def _call_llm(self, prompt: str, analysis_type: str) -> Tuple[str, AnalysisCost]:
        """
        Make a synchronous LLM call and track costs.

        Returns tuple of (response_text, cost_info)
        """
        message = self.client.messages.create(
            model=self.model,
            max_tokens=500,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        # Extract response text
        response_text = message.content[0].text

        # Track costs
        cost = AnalysisCost(
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
            model=self.model,
            analysis_type=analysis_type,
        )
        self.cost_tracker.log_analysis(cost)

        return response_text, cost

    async def _call_llm_async(self, prompt: str, analysis_type: str) -> Tuple[str, AnalysisCost]:
        """
        Make an async LLM call and track costs.
        """
        # Run sync client in executor for async compatibility
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._call_llm(prompt, analysis_type)
        )

    def _parse_json_response(self, response: str) -> Dict:
        """Parse JSON from LLM response, handling potential formatting issues."""
        # Clean up response - remove markdown code blocks if present
        response = response.strip()
        if response.startswith('```'):
            # Remove markdown code block
            lines = response.split('\n')
            response = '\n'.join(lines[1:-1] if lines[-1].startswith('```') else lines[1:])

        try:
            return json.loads(response)
        except json.JSONDecodeError:
            # Try to extract JSON from response
            import re
            json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group())
                except json.JSONDecodeError:
                    pass
            return {}

    def detect_contempt(self, text: str, context: str = "") -> ContemptResult:
        """
        Detect contempt/sarcasm with nuanced LLM analysis.

        Contempt is the strongest predictor of relationship dissolution
        (90%+ accuracy in Gottman research). This method catches subtle
        sarcasm that regex patterns miss.

        Args:
            text: Message to analyze
            context: Previous messages for context

        Returns:
            ContemptResult with detection and reasoning
        """
        prompt = self.CONTEMPT_PROMPT.format(text=text, context=context)
        response, cost = self._call_llm(prompt, 'contempt_detection')

        data = self._parse_json_response(response)

        result = ContemptResult(
            is_contempt=data.get('is_contempt', False),
            confidence=data.get('confidence', 0.0),
            contempt_type=data.get('type', 'none'),
            reasoning=data.get('reasoning', ''),
            severity=data.get('severity', 'mild'),
        )

        # Store sample for output
        if len(self._sample_analyses) < self._max_samples and result.is_contempt:
            self._sample_analyses.append({
                'message': text[:100],
                'type': 'contempt_detection',
                'result': result.to_dict(),
            })

        return result

    async def detect_contempt_async(self, text: str, context: str = "") -> ContemptResult:
        """Async version of detect_contempt."""
        prompt = self.CONTEMPT_PROMPT.format(text=text, context=context)
        response, cost = await self._call_llm_async(prompt, 'contempt_detection')

        data = self._parse_json_response(response)

        return ContemptResult(
            is_contempt=data.get('is_contempt', False),
            confidence=data.get('confidence', 0.0),
            contempt_type=data.get('type', 'none'),
            reasoning=data.get('reasoning', ''),
            severity=data.get('severity', 'mild'),
        )

    def assess_response_quality(self, original: str, response: str) -> ResponseQuality:
        """
        Assess the quality of a response to emotional content.

        Based on Reis & Shaver's Interpersonal Process Model:
        Responsiveness = Understanding + Validation + Caring

        This catches cases where word count != quality:
        - Short but validating: "Entendo, quer conversar?" = HIGH
        - Long but dismissive: "O que você quer que eu faça?" = LOW

        Args:
            original: The original emotional message
            response: The response to evaluate

        Returns:
            ResponseQuality with scores and assessment
        """
        prompt = self.RESPONSE_QUALITY_PROMPT.format(original=original, response=response)
        response_text, cost = self._call_llm(prompt, 'response_quality')

        data = self._parse_json_response(response_text)

        result = ResponseQuality(
            understanding_score=data.get('understanding_score', 50),
            validation_score=data.get('validation_score', 50),
            caring_score=data.get('caring_score', 50),
            overall_quality=data.get('overall_quality', 50),
            is_dismissive=data.get('is_dismissive', False),
            reasoning=data.get('reasoning', ''),
        )

        # Store sample
        if len(self._sample_analyses) < self._max_samples:
            if result.is_dismissive or result.overall_quality >= 80:
                self._sample_analyses.append({
                    'message': f"Original: {original[:50]}... | Response: {response[:50]}...",
                    'type': 'response_quality',
                    'result': result.to_dict(),
                })

        return result

    async def assess_response_quality_async(self, original: str, response: str) -> ResponseQuality:
        """Async version of assess_response_quality."""
        prompt = self.RESPONSE_QUALITY_PROMPT.format(original=original, response=response)
        response_text, cost = await self._call_llm_async(prompt, 'response_quality')

        data = self._parse_json_response(response_text)

        return ResponseQuality(
            understanding_score=data.get('understanding_score', 50),
            validation_score=data.get('validation_score', 50),
            caring_score=data.get('caring_score', 50),
            overall_quality=data.get('overall_quality', 50),
            is_dismissive=data.get('is_dismissive', False),
            reasoning=data.get('reasoning', ''),
        )

    def validate_repair_attempt(self, text: str, conflict_context: str = "") -> RepairResult:
        """
        Validate if a repair attempt is genuine or blame-shifting.

        Fake repairs mask blame:
        - "Você tem razão, MAS você também..." = NOT genuine
        - "Desculpa, não percebi" = genuine

        Args:
            text: The potential repair message
            conflict_context: Recent conflict messages for context

        Returns:
            RepairResult with authenticity assessment
        """
        prompt = self.REPAIR_PROMPT.format(text=text, context=conflict_context)
        response, cost = self._call_llm(prompt, 'repair_validation')

        data = self._parse_json_response(response)

        result = RepairResult(
            is_genuine=data.get('is_genuine', True),
            confidence=data.get('confidence', 0.5),
            responsibility_level=data.get('responsibility_level', 'partial'),
            has_blame_shifting=data.get('has_blame_shifting', False),
            reasoning=data.get('reasoning', ''),
        )

        # Store sample for non-genuine repairs
        if len(self._sample_analyses) < self._max_samples and not result.is_genuine:
            self._sample_analyses.append({
                'message': text[:100],
                'type': 'repair_validation',
                'result': result.to_dict(),
            })

        return result

    async def validate_repair_attempt_async(self, text: str, conflict_context: str = "") -> RepairResult:
        """Async version of validate_repair_attempt."""
        prompt = self.REPAIR_PROMPT.format(text=text, context=conflict_context)
        response, cost = await self._call_llm_async(prompt, 'repair_validation')

        data = self._parse_json_response(response)

        return RepairResult(
            is_genuine=data.get('is_genuine', True),
            confidence=data.get('confidence', 0.5),
            responsibility_level=data.get('responsibility_level', 'partial'),
            has_blame_shifting=data.get('has_blame_shifting', False),
            reasoning=data.get('reasoning', ''),
        )

    def analyze_vulnerability_depth(self, text: str, context: str = "") -> VulnerabilityResult:
        """
        Assess the depth of emotional vulnerability/disclosure.

        Not all emotional disclosure is equal:
        - Surface: "Estou cansado" (low intimacy value)
        - Deep: "Tenho medo de não ser bom o suficiente" (high intimacy value)

        Args:
            text: Message to analyze
            context: Conversation context

        Returns:
            VulnerabilityResult with depth assessment
        """
        prompt = self.VULNERABILITY_PROMPT.format(text=text, context=context)
        response, cost = self._call_llm(prompt, 'vulnerability_depth')

        data = self._parse_json_response(response)

        result = VulnerabilityResult(
            depth_level=data.get('depth_level', 'surface'),
            depth_score=data.get('depth_score', 30),
            invites_reciprocity=data.get('invites_reciprocity', False),
            topics=data.get('topics', []),
            reasoning=data.get('reasoning', ''),
        )

        # Store sample for deep vulnerabilities
        if len(self._sample_analyses) < self._max_samples and result.depth_level == 'deep':
            self._sample_analyses.append({
                'message': text[:100],
                'type': 'vulnerability_depth',
                'result': result.to_dict(),
            })

        return result

    async def analyze_vulnerability_depth_async(self, text: str, context: str = "") -> VulnerabilityResult:
        """Async version of analyze_vulnerability_depth."""
        prompt = self.VULNERABILITY_PROMPT.format(text=text, context=context)
        response, cost = await self._call_llm_async(prompt, 'vulnerability_depth')

        data = self._parse_json_response(response)

        return VulnerabilityResult(
            depth_level=data.get('depth_level', 'surface'),
            depth_score=data.get('depth_score', 30),
            invites_reciprocity=data.get('invites_reciprocity', False),
            topics=data.get('topics', []),
            reasoning=data.get('reasoning', ''),
        )

    def assess_shared_meaning(self, text: str, context: str = "") -> SharedMeaningResult:
        """
        Assess shared meaning and future planning quality.

        Distinguishes commitment levels:
        - "Vamos jantar" = casual, immediate
        - "Vamos construir nossa vida juntos" = strong, long-term

        Args:
            text: Message to analyze
            context: Conversation context

        Returns:
            SharedMeaningResult with commitment assessment
        """
        prompt = self.SHARED_MEANING_PROMPT.format(text=text, context=context)
        response, cost = self._call_llm(prompt, 'shared_meaning')

        data = self._parse_json_response(response)

        result = SharedMeaningResult(
            commitment_level=data.get('commitment_level', 'casual'),
            commitment_score=data.get('commitment_score', 30),
            timeframe=data.get('timeframe', 'immediate'),
            goal_alignment=data.get('goal_alignment', False),
            reasoning=data.get('reasoning', ''),
        )

        # Store sample for strong commitments
        if len(self._sample_analyses) < self._max_samples and result.commitment_level == 'strong':
            self._sample_analyses.append({
                'message': text[:100],
                'type': 'shared_meaning',
                'result': result.to_dict(),
            })

        return result

    async def assess_shared_meaning_async(self, text: str, context: str = "") -> SharedMeaningResult:
        """Async version of assess_shared_meaning."""
        prompt = self.SHARED_MEANING_PROMPT.format(text=text, context=context)
        response, cost = await self._call_llm_async(prompt, 'shared_meaning')

        data = self._parse_json_response(response)

        return SharedMeaningResult(
            commitment_level=data.get('commitment_level', 'casual'),
            commitment_score=data.get('commitment_score', 30),
            timeframe=data.get('timeframe', 'immediate'),
            goal_alignment=data.get('goal_alignment', False),
            reasoning=data.get('reasoning', ''),
        )

    def analyze_message(self,
                       message: str,
                       context: List[str] = None,
                       previous_message: str = None,
                       message_id: str = None,
                       sender: str = None,
                       timestamp: datetime = None,
                       is_response_to_emotional: bool = False,
                       is_potential_repair: bool = False,
                       is_emotional_disclosure: bool = False,
                       is_future_planning: bool = False) -> MessageAnalysis:
        """
        Comprehensive single-message analysis.

        Selectively applies analysis types based on message characteristics
        to optimize API usage while maintaining quality.

        Args:
            message: The message text to analyze
            context: List of previous messages for context
            previous_message: The immediately previous message (for response quality)
            message_id: Unique identifier for the message
            sender: Who sent the message
            timestamp: When the message was sent
            is_response_to_emotional: If this is responding to emotional content
            is_potential_repair: If this looks like a repair attempt
            is_emotional_disclosure: If this contains emotional disclosure
            is_future_planning: If this discusses future plans

        Returns:
            MessageAnalysis with all applicable assessments
        """
        context_str = '\n'.join(context[-5:]) if context else ""

        analysis = MessageAnalysis(
            message_id=message_id,
            message_text=message,
            sender=sender,
            timestamp=timestamp,
        )

        # Always check for contempt (highest impact)
        if self.analyze_all or len(message) > 5:
            analysis.contempt = self.detect_contempt(message, context_str)

        # Check response quality if responding to emotional content
        if is_response_to_emotional and previous_message:
            analysis.response_quality = self.assess_response_quality(
                previous_message, message
            )

        # Validate repair attempts
        if is_potential_repair:
            analysis.repair = self.validate_repair_attempt(message, context_str)

        # Assess vulnerability depth for emotional disclosures
        if is_emotional_disclosure:
            analysis.vulnerability = self.analyze_vulnerability_depth(message, context_str)

        # Assess shared meaning for future planning
        if is_future_planning:
            analysis.shared_meaning = self.assess_shared_meaning(message, context_str)

        return analysis

    async def analyze_message_async(self,
                                   message: str,
                                   context: List[str] = None,
                                   previous_message: str = None,
                                   message_id: str = None,
                                   sender: str = None,
                                   timestamp: datetime = None,
                                   is_response_to_emotional: bool = False,
                                   is_potential_repair: bool = False,
                                   is_emotional_disclosure: bool = False,
                                   is_future_planning: bool = False) -> MessageAnalysis:
        """Async version of analyze_message."""
        context_str = '\n'.join(context[-5:]) if context else ""

        analysis = MessageAnalysis(
            message_id=message_id,
            message_text=message,
            sender=sender,
            timestamp=timestamp,
        )

        # Gather all applicable analyses concurrently
        tasks = []
        task_types = []

        if self.analyze_all or len(message) > 5:
            tasks.append(self.detect_contempt_async(message, context_str))
            task_types.append('contempt')

        if is_response_to_emotional and previous_message:
            tasks.append(self.assess_response_quality_async(previous_message, message))
            task_types.append('response_quality')

        if is_potential_repair:
            tasks.append(self.validate_repair_attempt_async(message, context_str))
            task_types.append('repair')

        if is_emotional_disclosure:
            tasks.append(self.analyze_vulnerability_depth_async(message, context_str))
            task_types.append('vulnerability')

        if is_future_planning:
            tasks.append(self.assess_shared_meaning_async(message, context_str))
            task_types.append('shared_meaning')

        # Execute all tasks concurrently
        if tasks:
            results = await asyncio.gather(*tasks)
            for task_type, result in zip(task_types, results):
                if task_type == 'contempt':
                    analysis.contempt = result
                elif task_type == 'response_quality':
                    analysis.response_quality = result
                elif task_type == 'repair':
                    analysis.repair = result
                elif task_type == 'vulnerability':
                    analysis.vulnerability = result
                elif task_type == 'shared_meaning':
                    analysis.shared_meaning = result

        return analysis

    def get_analysis_summary(self) -> Dict[str, Any]:
        """
        Get summary of all analyses for output schema.

        Returns dict matching the llmAnalysis output schema.
        """
        cost_report = self.cost_tracker.generate_report()

        return {
            'enabled': True,
            'model': self.model,
            'analyzeAllMessages': self.analyze_all,
            'totalCost': cost_report['totalCost'],
            'analysisBreakdown': {
                'contemptDetections': cost_report['analysisBreakdown'].get('contempt_detection', {}).get('count', 0),
                'responseQualityAssessments': cost_report['analysisBreakdown'].get('response_quality', {}).get('count', 0),
                'repairValidations': cost_report['analysisBreakdown'].get('repair_validation', {}).get('count', 0),
                'vulnerabilityAssessments': cost_report['analysisBreakdown'].get('vulnerability_depth', {}).get('count', 0),
                'sharedMeaningAssessments': cost_report['analysisBreakdown'].get('shared_meaning', {}).get('count', 0),
            },
            'costByType': cost_report['analysisBreakdown'],
            'sampleAnalyses': self._sample_analyses,
        }
