"""WhatsApp Chat Analyzer Package

Scientific health scoring based on validated academic research:
- Gottman's research for conflict detection (Four Horsemen, 5:1 ratio)
- Interpersonal Process Model for connection quality (Reis & Shaver)
- Maintenance Behaviors for partnership equity (Stafford & Canary)

LLM Enhancement (v2.1):
- Claude Opus 4.5 integration for nuanced pattern detection
- Context-aware contempt/sarcasm detection
- Response quality assessment beyond word count
- Repair attempt authenticity validation
- Vulnerability depth scoring
"""

from .parser import WhatsAppParser
from .analyzer import ChatAnalyzer
from .visualizer import ChatVisualizer
from .sentiment import SentimentAnalyzer
from .topic_analyzer import TopicAnalyzer
from .conflict_detector import ConflictDetector
from .navi_output import NAVIOutputGenerator
from .navi_reports import NAVIReportGenerator
from .utils import format_duration, clean_text, get_portuguese_stopwords

# Scientific scoring modules (v2.0)
from .pattern_detectors import (
    PatternMatch,
    PatternSummary,
    GottmanPatternDetector,
    PositivePatternDetector,
    ResponsivenessAnalyzer,
    RelationshipPatternAnalyzer,
)
from .scientific_scoring import (
    DimensionScore,
    HealthScoreResult,
    ScientificHealthScorer,
)

# LLM-enhanced analysis (v2.1)
from .llm_analyzer import (
    LLMRelationshipAnalyzer,
    CostTracker,
    AnalysisCost,
    ContemptResult,
    ResponseQuality,
    RepairResult,
    VulnerabilityResult,
    SharedMeaningResult,
    MessageAnalysis,
)

__all__ = [
    # Core analyzers
    'WhatsAppParser',
    'ChatAnalyzer',
    'ChatVisualizer',
    'SentimentAnalyzer',
    'TopicAnalyzer',
    'ConflictDetector',

    # NAVI output generators
    'NAVIOutputGenerator',
    'NAVIReportGenerator',

    # Scientific scoring (v2.0)
    'PatternMatch',
    'PatternSummary',
    'GottmanPatternDetector',
    'PositivePatternDetector',
    'ResponsivenessAnalyzer',
    'RelationshipPatternAnalyzer',
    'DimensionScore',
    'HealthScoreResult',
    'ScientificHealthScorer',

    # LLM-enhanced analysis (v2.1)
    'LLMRelationshipAnalyzer',
    'CostTracker',
    'AnalysisCost',
    'ContemptResult',
    'ResponseQuality',
    'RepairResult',
    'VulnerabilityResult',
    'SharedMeaningResult',
    'MessageAnalysis',

    # Utilities
    'format_duration',
    'clean_text',
    'get_portuguese_stopwords',
]
