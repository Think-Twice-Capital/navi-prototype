# NAVI - Technical Documentation (v2.2)

> Relationship Health Analyzer based on validated academic research

## Version History

### v2.2 Changes (2026-01-28)
- **Full LLM Analysis**: All four dimensions now use LLM (Claude Sonnet) for pattern detection
- **LLM Weekly Pulse**: Historical chart uses LLM analysis for each week's positive patterns
- **Interactive Detail Views**: Clickable dimension cards and Four Horsemen with modal detail views
- **Example Messages**: Each dimension and horseman shows real conversation examples
- **False Positive Filtering**: Filters forwarded messages, quotes, and messages about third parties
- **Positive/Negative Labels**: Examples are clearly labeled as positive or negative patterns

### v2.1 Changes
- **Temporal Scoring**: Now uses only the last 30 days for scoring
- **Faster Responsiveness**: Scores change quickly as relationship patterns evolve
- **Simplified Window**: Removed multi-period weighting (30d/90d/longterm)

### v2.0 Changes
This version restructures the 4-dimension model to eliminate pattern overlaps:

| Old Structure | New Structure (v2.0) |
|--------------|---------------------|
| Connection Quality | Emotional Connection |
| Relationship Maintenance | Affection & Commitment |
| Communication Health | Communication Health (consolidated) |
| Partnership Dynamics | Partnership Equity |

**Key Improvements:**
- Each pattern set is used by ONE dimension only (no double-counting)
- Reciprocity moved from D1 to D4.Emotional Reciprocity
- Shared Meaning merged into D2.Commitment Signals
- Four Horsemen consolidated into D3 sub-dimensions

## 1. Architecture Overview

### 1.1 Module Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                        NAVI Architecture                             │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌──────────────┐     ┌──────────────────────────────────────────┐  │
│  │   Input      │     │           Analysis Layer                  │  │
│  │              │     │                                          │  │
│  │  WhatsApp    │────►│  ┌────────────────┐  ┌────────────────┐ │  │
│  │  Chat Export │     │  │ Pattern        │  │ Scientific     │ │  │
│  │  (.txt)      │     │  │ Detectors      │  │ Scoring        │ │  │
│  └──────────────┘     │  │                │  │                │ │  │
│         │             │  │ • Gottman      │  │ • 4 Dimensions │ │  │
│         ▼             │  │ • Positive     │  │ • Temporal     │ │  │
│  ┌──────────────┐     │  │ • Responsive   │  │ • Weighted     │ │  │
│  │   Parser     │     │  └───────┬────────┘  └───────┬────────┘ │  │
│  │              │     │          │                   │          │  │
│  │  • Messages  │────►│          └─────────┬─────────┘          │  │
│  │  • Types     │     │                    │                    │  │
│  │  • Metadata  │     │          ┌─────────▼─────────┐          │  │
│  └──────────────┘     │          │   LLM Analyzer    │          │  │
│                       │          │   (Optional)      │          │  │
│                       │          │                   │          │  │
│                       │          │ • Contempt        │          │  │
│                       │          │ • Response Qual.  │          │  │
│                       │          │ • Repair Valid.   │          │  │
│                       │          │ • Vulnerability   │          │  │
│                       │          └───────────────────┘          │  │
│                       └──────────────────────────────────────────┘  │
│                                         │                            │
│                                         ▼                            │
│                       ┌──────────────────────────────────────────┐  │
│                       │              Output Layer                 │  │
│                       │                                          │  │
│                       │  ┌────────────┐    ┌────────────┐       │  │
│                       │  │    JSON    │    │  Markdown  │       │  │
│                       │  │   Export   │    │   Report   │       │  │
│                       │  └────────────┘    └────────────┘       │  │
│                       └──────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

### 1.2 Data Flow

```
WhatsApp Export (.txt)
        │
        ▼
┌───────────────────┐
│   WhatsAppParser  │ ──► DataFrame with columns:
└───────────────────┘     datetime, sender, message, type, etc.
        │
        ▼
┌───────────────────┐
│ PatternDetectors  │ ──► PatternMatch objects (positive/negative)
└───────────────────┘
        │
        ▼
┌───────────────────┐
│ScientificScorer   │ ──► HealthScoreResult (4 dimensions + overall)
└───────────────────┘
        │
        ▼
┌───────────────────┐
│  OutputGenerator  │ ──► JSON / Markdown / Web Data
└───────────────────┘
```

### 1.3 Key Dependencies

```
whatsapp_analyzer/
├── parser.py              # WhatsApp chat parsing
├── pattern_detectors.py   # Gottman & positive patterns
├── scientific_scoring.py  # 4-dimension scoring framework
├── llm_analyzer.py        # Claude Opus 4.5 integration
├── navi_output.py         # JSON export
└── navi_reports.py        # Markdown reports
```

**External Dependencies:**
- `pandas` - Data manipulation
- `numpy` - Numerical operations
- `anthropic` - Claude API client (for LLM features)

---

## 2. Core Modules

### 2.1 Parser (`whatsapp_analyzer/parser.py`)

**Purpose:** Parse WhatsApp chat export files into structured DataFrames.

#### Input Format

Supports WhatsApp iOS/Android export format:
```
[M/D/YY, H:MM:SS AM/PM] Sender: Message content
```

Example:
```
[3/15/24, 2:30:45 PM] Alice: Hello!
[3/15/24, 2:31:12 PM] Bob: Hi there! How are you?
```

#### Output DataFrame Columns

| Column | Type | Description |
|--------|------|-------------|
| `datetime` | datetime64 | Full timestamp |
| `date` | date | Date only |
| `time` | time | Time only |
| `year`, `month`, `day`, `hour` | int | Date components |
| `day_of_week` | str | Day name (e.g., "Monday") |
| `day_of_week_num` | int | Day number (0-6) |
| `sender` | str | Message sender name |
| `message` | str | Message content |
| `type` | str | Message type (see below) |
| `call_duration_seconds` | int | Duration for calls |
| `message_length` | int | Character count (text only) |
| `word_count` | int | Word count (text only) |

#### Message Types

- `text` - Regular text messages
- `image`, `video`, `audio`, `sticker`, `document` - Media
- `voice_call`, `video_call` - Calls
- `missed_voice`, `missed_video` - Missed calls
- `system` - System notifications

#### Usage Example

```python
from whatsapp_analyzer import WhatsAppParser

parser = WhatsAppParser("chat_export.txt")
df = parser.parse()

# Get participants
participants = parser.get_participants()

# Filter by type
text_messages = parser.filter_by_type('text')
```

---

### 2.2 Pattern Detectors (`whatsapp_analyzer/pattern_detectors.py`)

**Purpose:** Detect relationship patterns based on Gottman's research and positive psychology.

#### 2.2.1 GottmanPatternDetector

Detects the Four Horsemen of the Apocalypse (predictors of relationship dissolution):

**Criticism Patterns (PT-BR):**
```python
CRITICISM_PATTERNS = [
    r'\bvocê sempre\b',          # "you always"
    r'\bvocê nunca\b',           # "you never"
    r'\bvocê é tão preguiçoso\b', # "you are so lazy"
    r'\bvocê só pensa\b',        # "you only think"
    # ... more patterns
]
```

**Contempt Patterns (PT-BR):**
```python
CONTEMPT_PATTERNS = [
    r'\bgrande coisa\b',     # "big deal" (sarcastic)
    r'\btanto faz\b',        # "whatever"
    r'\bfoda-se\b',          # explicit dismissal
    r'🙄',                   # eye-roll emoji
    # ... more patterns
]
```

**Defensiveness Patterns (PT-BR):**
```python
DEFENSIVENESS_PATTERNS = [
    r'\bmas você também\b',   # "but you also"
    r'\bnão é minha culpa\b', # "it's not my fault"
    r'\bvocê está exagerando\b', # "you're exaggerating"
    # ... more patterns
]
```

**Stonewalling Patterns:**
```python
STONEWALLING_PHRASES = [
    r'\btanto faz\b',        # "whatever"
    r'\bnão quero falar\b',  # "don't want to talk"
    r'\besquece\b',          # "forget it"
    r'\bok\b$',              # minimal "ok"
]
```

**Antidotes (Research-backed solutions):**
```python
ANTIDOTES = {
    'criticism': {
        'name': 'Gentle Startup',
        'description': 'Use "Eu sinto..." instead of "Você é..."'
    },
    'contempt': {
        'name': 'Build Culture of Appreciation',
        'description': 'Express specific gratitude daily'
    },
    # ...
}
```

#### 2.2.2 PositivePatternDetector

Detects positive relationship markers:

| Pattern Category | Examples (PT-BR) |
|-----------------|------------------|
| **Repair Attempts** | "desculpa", "me perdoa", "eu errei" |
| **Affection** | "te amo", "saudade", "❤️" |
| **Gratitude** | "obrigado por", "agradeço" |
| **Support** | "estou aqui", "conte comigo" |
| **Future Planning** | "vamos fazer", "nosso futuro" |
| **Active Listening** | "como foi", "me conta" |
| **Disclosure** | "eu sinto", "estou preocupado" |
| **Understanding** | "entendo você", "faz sentido" |
| **Assurance** | "sempre vou", "somos um time" |

#### 2.2.3 ResponsivenessAnalyzer

Based on Reis & Shaver's Interpersonal Process Model:

```
Responsiveness = Understanding + Validation + Caring
```

**Key Methods:**

```python
def is_emotional_message(text: str) -> bool:
    """Check if message contains emotional content."""

def is_dismissive_response(text: str) -> bool:
    """Check if response is dismissive (minimal to emotional)."""

def calculate_response_quality(
    original_msg: str,
    response_msg: str,
    response_time_minutes: float
) -> Dict:
    """
    Returns:
        score: 0-100
        is_emotional_context: bool
        is_dismissive: bool
        response_depth: 'deep' | 'moderate' | 'minimal'
    """
```

---

### 2.3 Scientific Scoring (`whatsapp_analyzer/scientific_scoring.py`)

**Purpose:** Calculate relationship health scores using validated academic frameworks.

#### 2.3.1 Four-Dimension Model (v2.0)

```
┌─────────────────────────────────────────────────────────────────────┐
│                 NAVI v2.0 - RESTRUCTURED SCORING MODEL               │
│                           (0-100 scale)                              │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────┐  ┌────────────────────────┐            │
│  │  EMOTIONAL CONNECTION  │  │ AFFECTION & COMMITMENT │            │
│  │        (30%)           │  │        (25%)           │            │
│  │                        │  │                        │            │
│  │ • Responsiveness (40%) │  │ • Expressed Affection  │            │
│  │ • Vulnerability (35%)  │  │   (40%)                │            │
│  │ • Attunement (25%)     │  │ • Commitment Signals   │            │
│  │                        │  │   (35%)                │            │
│  │ Patterns:              │  │ • Appreciation (25%)   │            │
│  │ - DISCLOSURE           │  │                        │            │
│  │ - ACTIVE_LISTENING     │  │ Patterns:              │            │
│  └────────────────────────┘  │ - AFFECTION            │            │
│                              │ - ASSURANCE            │            │
│                              │ - FUTURE_PLANNING      │            │
│                              │ - GRATITUDE            │            │
│                              └────────────────────────┘            │
│                                                                      │
│  ┌────────────────────────┐  ┌────────────────────────┐            │
│  │  COMMUNICATION HEALTH  │  │   PARTNERSHIP EQUITY   │            │
│  │        (25%)           │  │        (20%)           │            │
│  │                        │  │                        │            │
│  │ • Constructive         │  │ • Contribution Balance │            │
│  │   Dialogue (30%)       │  │   (40%)                │            │
│  │ • Conflict Repair (30%)│  │ • Coordination (35%)   │            │
│  │ • Emotional Safety     │  │ • Emotional            │            │
│  │   (25%)                │  │   Reciprocity (25%)    │            │
│  │ • Supportive           │  │                        │            │
│  │   Responses (15%)      │  │ Patterns:              │            │
│  │                        │  │ - action_verbs         │            │
│  │ Patterns:              │  │ - completion_markers   │            │
│  │ - REPAIR               │  │ - balance metrics      │            │
│  │ - CRITICISM (inverse)  │  │                        │            │
│  │ - CONTEMPT (inverse)   │  └────────────────────────┘            │
│  │ - SUPPORT              │                                        │
│  │ - UNDERSTANDING        │                                        │
│  └────────────────────────┘                                        │
└─────────────────────────────────────────────────────────────────────┘
```

#### 2.3.2 Pattern Ownership (v2.0 - No Overlaps)

| Pattern Set | Exclusive Location |
|-------------|-------------------|
| `DISCLOSURE_PATTERNS` | D1: Vulnerability |
| `ACTIVE_LISTENING_PATTERNS` | D1: Attunement |
| `AFFECTION_PATTERNS` | D2: Expressed Affection |
| `ASSURANCE_PATTERNS` | D2: Commitment Signals |
| `FUTURE_PLANNING_PATTERNS` | D2: Commitment Signals |
| `GRATITUDE_PATTERNS` | D2: Appreciation |
| `CRITICISM_PATTERNS` | D3: Constructive Dialogue (inverse) |
| `DEFENSIVENESS_PATTERNS` | D3: Constructive Dialogue (inverse) |
| `REPAIR_PATTERNS` | D3: Conflict Repair |
| `CONTEMPT_PATTERNS` | D3: Emotional Safety (inverse) |
| `STONEWALLING` | D3: Emotional Safety (inverse) |
| `SUPPORT_PATTERNS` | D3: Supportive Responses |
| `UNDERSTANDING_PATTERNS` | D3: Supportive Responses |
| `action_verbs` | D4: Contribution Balance |
| `completion_markers` | D4: Coordination |

#### 2.3.3 Dimension Weights (v2.0)

```python
DIMENSION_WEIGHTS = {
    'emotional_connection': 0.30,    # Interpersonal Process Model
    'affection_commitment': 0.25,    # Stafford & Canary + Gottman
    'communication_health': 0.25,    # Gottman's Four Horsemen
    'partnership_equity': 0.20,      # Equity Theory
}
```

#### 2.3.3 Scoring Window (v2.1)

Scoring uses only the last 30 days for faster responsiveness:

```python
SCORING_WINDOW_DAYS = 30  # Only last 30 days

def _get_scoring_df(self) -> pd.DataFrame:
    """Filter to scoring window."""
    now = self.df[self.datetime_col].max()
    cutoff = now - timedelta(days=self.SCORING_WINDOW_DAYS)
    return self.df[self.df[self.datetime_col] >= cutoff]
```

This design choice ensures scores change quickly as relationship patterns evolve, allowing users to see immediate impact of behavioral changes.

#### 2.3.4 Score Labels

| Score Range | Portuguese | English |
|-------------|------------|---------|
| 85-100 | Florescente | Flourishing |
| 70-84 | Saudável | Healthy |
| 55-69 | Estável | Stable |
| 40-54 | Atenção | Attention |
| 25-39 | Preocupante | Concerning |
| 0-24 | Crítico | Critical |

#### 2.3.5 Key Formulas

**Positivity Ratio (Gottman's 5:1):**
```python
ratio = total_positive / total_negative

if ratio >= 5.0:
    score = 100
elif ratio >= 3.0:
    score = 70 + (ratio - 3.0) * 15
elif ratio >= 1.0:
    score = 40 + (ratio - 1.0) * 15
else:
    score = max(10, ratio * 40)
```

**Responsiveness Score:**
```python
# Word count baseline
if word_count >= 15:
    depth = 'deep', score = 100
elif word_count >= 8:
    depth = 'moderate', score = 70
else:
    depth = 'minimal', score = 20-40

# Penalty for dismissive to emotional
if is_emotional and is_dismissive:
    score = 20
```

**Equity Score:**
```python
msg_balance = 100 - abs(min_pct - 50) * 2
init_balance = 100 - abs(init_min_pct - 50) * 2
score = (msg_balance * 0.6 + init_balance * 0.4)
```

#### 2.3.6 Classes

**DimensionScore:**
```python
@dataclass
class DimensionScore:
    score: float          # 0-100
    components: Dict      # Sub-component scores
    insights: List[str]   # PT-BR insights
```

**HealthScoreResult:**
```python
@dataclass
class HealthScoreResult:
    overall: float        # 0-100
    label: str            # Portuguese label
    label_en: str         # English label
    confidence: float     # 0-1 based on data volume
    trend: str            # e.g., "+3 vs last month"
    dimensions: Dict[str, DimensionScore]
    insights: Dict        # Strengths & opportunities
    alerts: List[Dict]    # Concerning patterns
```

---

### 2.4 LLM Analyzer (`whatsapp_analyzer/llm_analyzer.py` + `generate_health_data_quick.py`)

**Purpose:** Full LLM-based pattern detection for accurate relationship analysis.

#### 2.4.1 Integration Architecture (v2.2)

The v2.2 system uses LLM for ALL pattern detection, not just validation:

```python
# In generate_health_data_quick.py
import anthropic
client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY from .env

# LLM analyzes sample messages for each dimension
response = client.messages.create(
    model="claude-sonnet-4-20250514",  # Fast and accurate
    max_tokens=1500,
    messages=[{"role": "user", "content": prompt}]
)
```

#### 2.4.2 LLM Analysis Coverage (v2.2)

| Dimension | LLM Analysis | Patterns Detected |
|-----------|--------------|-------------------|
| **Emotional Connection** | ✓ Full | Vulnerability, Attunement, Responsiveness |
| **Affection & Commitment** | ✓ Full | Affection, Commitment, Appreciation |
| **Communication Health** | ✓ Validation | Four Horsemen (filters false positives) |
| **Partnership Equity** | ✓ Full | Shared Decisions, Coordination, Reciprocity |
| **Weekly Pulse** | ✓ Full | Positive patterns per week |

#### 2.4.3 Sample LLM Prompts (v2.2)

**Emotional Connection Analysis:**
```python
prompt = """Analyze these WhatsApp messages and count instances of:
1. VULNERABILITY: Sharing fears, insecurities, emotional struggles
2. ATTUNEMENT: Noticing partner's emotional state, checking in
3. RESPONSIVENESS: Engaged responses to emotional bids

Messages: {messages_text}

Respond in JSON: {vulnerability_count, attunement_count, responsiveness_count, ...}"""
```

**Partnership Equity Analysis:**
```python
prompt = """Analyze these WhatsApp messages and count instances of:
1. SHARED_DECISIONS: Joint decision-making, "o que você acha?"
2. COORDINATION: Coordinating schedules, dividing tasks
3. EMOTIONAL_RECIPROCITY: Both partners initiating emotional conversations

Messages: {messages_text}

Respond in JSON: {shared_decisions_count, coordination_count, emotional_reciprocity_score, ...}"""
```

#### 2.4.4 False Positive Filtering

Before LLM analysis, messages are filtered to exclude:

```python
def is_forwarded_or_quote(message_text: str) -> bool:
    """Filter out messages that aren't direct couple communication."""
    # Filters:
    # - WhatsApp forward markers (‎image omitted, etc.)
    # - Embedded timestamps (forwarded messages)
    # - Greeting patterns (Fala [Name]...)
    # - Forward indicators (encaminhei, fwd:)
    # - Third-party quotes (ele disse, ela falou)
    # - Messages about third parties (meu filho disse, teu filho)
```

#### 2.4.5 Legacy Analysis Types (still used for validation)

| Type | Purpose | When Used |
|------|---------|-----------|
| **Contempt Detection** | Catch sarcasm/subtle contempt | Four Horsemen validation |
| **Response Quality** | Assess empathy beyond word count | Emotional responses |
| **Repair Validation** | Distinguish genuine vs blame-shifting | Apologies |
| **Vulnerability Depth** | Score emotional disclosure quality | Emotional messages |
| **Shared Meaning** | Assess commitment level | Future planning |

#### 2.4.3 Cost Tracking

```python
MODEL_COSTS = {
    'claude-opus-4-5-20251101': {
        'input': 15.00,   # per million tokens
        'output': 75.00
    },
    'claude-sonnet-4-20250514': {
        'input': 3.00,
        'output': 15.00
    },
}
```

**Cost Report Structure:**
```python
{
    'totalCost': {
        'inputTokens': 12500,
        'outputTokens': 3200,
        'estimatedUSD': 0.4275
    },
    'analysisBreakdown': {
        'contempt_detection': {'count': 50, 'cost_usd': 0.25},
        'response_quality': {'count': 20, 'cost_usd': 0.12},
        # ...
    }
}
```

#### 2.4.4 Prompt Templates

**Contempt Detection:**
```python
CONTEMPT_PROMPT = """You are an expert relationship therapist...
Message: "{text}"
Context: "{context}"

IMPORTANT: Distinguish genuine from sarcastic statements.
- "Parabéns pelo aniversário!" = genuine
- "Parabéns, só levou 3 horas" = sarcastic contempt

Respond with JSON:
{
  "is_contempt": boolean,
  "confidence": 0.0-1.0,
  "type": "sarcasm" | "mockery" | "dismissive" | ...,
  "reasoning": "explanation in Portuguese",
  "severity": "mild" | "moderate" | "severe"
}"""
```

**Response Quality:**
```python
RESPONSE_QUALITY_PROMPT = """Based on Reis & Shaver's model...

IMPORTANT: Quality ≠ length.
- Short "Entendo, quer conversar?" = HIGH quality
- Long "O que você quer que eu faça?" = LOW (dismissive)

{
  "understanding_score": 0-100,
  "validation_score": 0-100,
  "caring_score": 0-100,
  "overall_quality": 0-100,
  "is_dismissive": boolean
}"""
```

#### 2.4.5 Result Classes

```python
@dataclass
class ContemptResult:
    is_contempt: bool
    confidence: float      # 0.0-1.0
    contempt_type: str     # sarcasm, mockery, dismissive, superiority
    reasoning: str
    severity: str          # mild, moderate, severe

@dataclass
class ResponseQuality:
    understanding_score: int   # 0-100
    validation_score: int
    caring_score: int
    overall_quality: int
    is_dismissive: bool
    reasoning: str

@dataclass
class RepairResult:
    is_genuine: bool
    confidence: float
    responsibility_level: str  # none, partial, full
    has_blame_shifting: bool
    reasoning: str
```

---

## 3. API and Interfaces

### 3.1 Main Classes

#### ScientificHealthScorer

```python
from whatsapp_analyzer import (
    ScientificHealthScorer,
    LLMRelationshipAnalyzer
)

# Without LLM (regex-only)
scorer = ScientificHealthScorer(
    df=messages_df,
    sender_col='sender',
    message_col='message',
    datetime_col='datetime',
    person_a='Alice',
    person_b='Bob'
)

# With LLM enhancement
llm_analyzer = LLMRelationshipAnalyzer()
scorer = ScientificHealthScorer(
    df=messages_df,
    llm_analyzer=llm_analyzer,
    use_llm=True
)

# Calculate scores
result = scorer.calculate_overall_score()
print(f"Score: {result.overall} ({result.label})")

# Export to dict
output = scorer.to_dict()
```

#### RelationshipPatternAnalyzer

```python
from whatsapp_analyzer import RelationshipPatternAnalyzer

analyzer = RelationshipPatternAnalyzer(
    llm_analyzer=llm_analyzer,
    use_llm=True
)

# Analyze single message
matches = analyzer.analyze_message(
    text="Você nunca me escuta!",
    sender="Alice",
    previous_message="..."
)

# Analyze conversation
summary = analyzer.analyze_conversation(df)
print(f"Positive ratio: {summary.positive_ratio}")
print(f"Four Horsemen: {summary.four_horsemen_counts}")
```

### 3.2 JSON Output Schema (v2.2)

```json
{
  "healthScore": {
    "overall": 86.3,
    "label": "Excelente",
    "labelEn": "Excellent",
    "confidence": 0.85,
    "trend": "+5 vs mês anterior",

    "dimensions": {
      "emotionalConnection": {
        "score": 100.0,
        "llmAnalysisNotes": "Strong emotional connection with frequent vulnerability sharing",
        "components": {
          "responsiveness": {
            "score": 100,
            "perWeek": 10.5,
            "count": 45,
            "insight": "Altamente responsivo",
            "llmValidated": true,
            "examples": ["Como você está se sentindo?", "Me conta mais..."]
          },
          "vulnerability": {
            "score": 100,
            "perWeek": 6.3,
            "count": 27,
            "insight": "Alta abertura emocional",
            "llmValidated": true,
            "examples": ["Estou com medo de...", "Preciso de você"]
          },
          "attunement": {
            "score": 100,
            "perWeek": 8.4,
            "count": 36,
            "insight": "Alta sintonia emocional",
            "llmValidated": true,
            "examples": ["Percebi que você está triste", "Sei que está difícil"]
          }
        },
        "examples": {
          "vulnerability": [
            {"text": "Estou preocupado com...", "sender": "Person A", "type": "positive"}
          ],
          "support": [
            {"text": "Estou aqui pra você", "sender": "Person B", "type": "positive"}
          ]
        }
      },
      "affectionCommitment": {
        "score": 76.2,
        "llmAnalysisNotes": "Regular affection with strong commitment signals",
        "components": {
          "expressedAffection": {
            "score": 82.5,
            "perWeek": 8.4,
            "count": 36,
            "insight": "Afeto presente regularmente",
            "llmValidated": true,
            "examples": ["Te amo", "Saudade ❤️"]
          },
          "commitmentSignals": {
            "score": 70.0,
            "perWeek": 6.3,
            "count": 27,
            "insight": "Compromisso demonstrado regularmente",
            "llmValidated": true,
            "examples": ["Vamos fazer juntos", "Nosso futuro"]
          },
          "appreciation": {
            "score": 76.0,
            "perWeek": 4.2,
            "count": 18,
            "insight": "Apreciação presente regularmente",
            "llmValidated": true,
            "examples": ["Obrigado por...", "Valeu!"]
          }
        }
      },
      "communicationHealth": {
        "score": 75.9,
        "components": {
          "constructiveDialogue": {
            "score": 100,
            "criticismCount": 0,
            "defensivenessCount": 0,
            "insight": "Diálogo construtivo e respeitoso",
            "criticismExamples": [],
            "defensivenessExamples": []
          },
          "conflictRepair": {"score": 78, "successRate": "75%"},
          "emotionalSafety": {
            "score": 100,
            "contemptCount": 0,
            "stonewallingCount": 0,
            "insight": "Ambiente emocionalmente seguro",
            "contemptExamples": [],
            "stonewallingExamples": []
          },
          "supportiveResponses": {"score": 72, "rate": "3.5%"}
        }
      },
      "partnershipEquity": {
        "score": 91.3,
        "llmAnalysisNotes": "Excellent coordination with balanced decision-making",
        "components": {
          "contributionBalance": {
            "score": 85.0,
            "perWeek": 4.5,
            "count": 27,
            "insight": "Contribuições bem equilibradas",
            "llmValidated": true
          },
          "coordination": {
            "score": 100,
            "perWeek": 10.5,
            "count": 45,
            "insight": "Excelente coordenação",
            "llmValidated": true
          },
          "emotionalReciprocity": {
            "score": 75,
            "insight": "Both partners initiate emotional conversations equally",
            "llmValidated": true
          },
          "sharedDecisions": {
            "score": 85.0,
            "perWeek": 6.3,
            "count": 27,
            "insight": "Decisões tomadas em conjunto",
            "llmValidated": true
          }
        }
      }
    }
  },

  "weeklyPulse": [
    {
      "weekKey": "2025-W50",
      "weekStart": "2025-12-08",
      "weekLabel": "08 Dec",
      "score": 80,
      "messages": 250,
      "positive": 25,
      "negative": 0,
      "ratio": 25.0,
      "positiveRate": 10.0,
      "hasConflict": false,
      "horsemen": {"criticism": 0, "contempt": 0, "defensiveness": 0, "stonewalling": 0},
      "llmAnalyzed": true
    }
  ],

  "methodology": {
    "framework": "NAVI v2.2 - LLM-Analyzed Dimensions (30-Day Window)",
    "version": "2.2",
    "scale": "1-100",
    "scoringWindow": "30 days",
    "analysisMethod": "LLM (Claude Sonnet) for all dimensions",
    "dimensionWeights": {
      "emotional_connection": 0.30,
      "affection_commitment": 0.25,
      "communication_health": 0.25,
      "partnership_equity": 0.20
    }
  },

  "llmAnalysis": {
    "enabled": true,
    "model": "claude-sonnet-4-20250514",
    "validations": [
      {"category": "contempt", "text": "...", "isValid": false}
    ],
    "costSummary": {...}
  },

  "metadata": {
    "totalMessages": 32279,
    "dateRange": {"start": "2018-03-27", "end": "2025-12-16"},
    "participants": ["Person A", "Person B"],
    "generatedAt": "2026-01-28T..."
  }
}
```

---

## 4. Configuration and Deployment

### 4.1 Dependencies

**requirements.txt:**
```
pandas>=2.0.0
numpy>=1.24.0
anthropic>=0.39.0
```

### 4.2 Environment Variables

| Variable | Purpose | Required |
|----------|---------|----------|
| `ANTHROPIC_API_KEY` | Claude API authentication | Only if using LLM |

### 4.3 Execution Modes

**Quick Mode (No LLM):**
```python
scorer = ScientificHealthScorer(df=df)
result = scorer.to_dict()  # Fast, regex-only
```

**LLM Enhanced Mode:**
```python
llm = LLMRelationshipAnalyzer(model="claude-opus-4-5-20251101")
scorer = ScientificHealthScorer(df=df, llm_analyzer=llm, use_llm=True)
result = scorer.to_dict()  # Higher accuracy, API costs
```

**Cost-Optimized Mode (Future):**
```python
llm = LLMRelationshipAnalyzer(
    model="claude-3-5-haiku-20241022",  # Lower cost
    analyze_all=False                    # Selective analysis
)
```

---

## 5. Extensibility

### 5.1 Adding New Patterns

**In `pattern_detectors.py`:**

```python
class PositivePatternDetector:
    # Add new category
    NEW_CATEGORY_PATTERNS = [
        r'\bpattern one\b',
        r'\bpattern two\b',
    ]

    def __init__(self):
        # Compile patterns
        self.new_category_re = [
            re.compile(p, re.IGNORECASE)
            for p in self.NEW_CATEGORY_PATTERNS
        ]

    def detect_new_category(self, text: str) -> Optional[PatternMatch]:
        return self._detect_pattern(
            text,
            self.new_category_re,
            'new_category',
            score_impact=+3
        )

    def detect_all(self, text: str) -> List[PatternMatch]:
        # Add to detection list
        match = self.detect_new_category(text)
        if match:
            matches.append(match)
```

### 5.2 Adjusting Weights

**In `scientific_scoring.py`:**

```python
class ScientificHealthScorer:
    # Modify dimension weights (v2.1)
    DIMENSION_WEIGHTS = {
        'emotional_connection': 0.35,      # Increased
        'affection_commitment': 0.25,
        'communication_health': 0.25,
        'partnership_equity': 0.15,        # Decreased
    }

    # Modify scoring window (v2.1)
    SCORING_WINDOW_DAYS = 30  # Can be adjusted (e.g., 14, 60)
```

### 5.3 Adding New Dimensions

1. Create new calculate method:
```python
def calculate_new_dimension(self, df: pd.DataFrame) -> DimensionScore:
    # Calculate components
    component_1 = self._calc_component_1(df)
    component_2 = self._calc_component_2(df)

    total_score = (
        component_1['score'] * 0.50 +
        component_2['score'] * 0.50
    )

    return DimensionScore(
        score=round(total_score, 1),
        components={
            'component1': component_1,
            'component2': component_2,
        },
        insights=[]
    )
```

2. Update weights:
```python
DIMENSION_WEIGHTS = {
    'emotional_connection': 0.25,
    'affection_commitment': 0.20,
    'communication_health': 0.20,
    'partnership_equity': 0.15,
    'new_dimension': 0.20,  # New!
}
```

3. Include in overall calculation:
```python
def calculate_overall_score(self):
    # Add to dimension calculations
    new_dim = self.calculate_new_dimension(period_df)

    period_overall = (
        # ... existing dimensions ...
        new_dim.score * self.DIMENSION_WEIGHTS['new_dimension']
    )
```

---

## 6. Scientific References

1. **Gottman, J. M. (1994).** *What Predicts Divorce? The Relationship Between Marital Processes and Marital Outcomes.* Lawrence Erlbaum Associates.

2. **Reis, H. T., & Shaver, P. (1988).** Intimacy as an interpersonal process. In S. Duck (Ed.), *Handbook of personal relationships* (pp. 367-389).

3. **Stafford, L., & Canary, D. J. (1991).** Maintenance strategies and romantic relationship type, gender and relational characteristics. *Journal of Social and Personal Relationships, 8*(2), 217-242.

4. **Funk, J. L., & Rogge, R. D. (2007).** Testing the ruler with item response theory: Increasing precision of measurement for relationship satisfaction with the Couples Satisfaction Index. *Journal of Family Psychology, 21*(4), 572.

5. **Spanier, G. B. (1976).** Measuring dyadic adjustment: New scales for assessing the quality of marriage and similar dyads. *Journal of Marriage and the Family*, 15-28.
