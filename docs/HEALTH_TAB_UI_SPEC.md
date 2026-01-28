# NAVI Relationship Health Tab - UI Specification

> A reimagined chat app experience with integrated relationship health analysis

---

## Overview

The Health tab transforms raw chat data into actionable relationship insights, presenting scientific analysis in an engaging, non-clinical way.

### Design Principles

1. **Empowering, not alarming** - Focus on growth opportunities, not deficits
2. **Progress-oriented** - Show trends and improvements over time
3. **Actionable** - Every insight links to a concrete suggestion
4. **Private & respectful** - Both partners see their own perspective

---

## Tab Structure

```
┌─────────────────────────────────────────────────────────────┐
│  💬 Chat    📊 Health    🎯 Goals    ⚙️ Settings            │
└─────────────────────────────────────────────────────────────┘
```

---

## Health Tab Layout

### Section 1: Hero Score Card

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│                         72                                  │
│                    ───────────                              │
│                      Saudável                               │
│                                                             │
│              ↑ +3 pontos vs. mês passado                   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ████████████████████████████████░░░░░░░░░░░░░░░░░░░ │   │
│  └─────────────────────────────────────────────────────┘   │
│   0        25        50        72      85       100        │
│   Crítico  Atenção   Estável   ▲    Florescente           │
│                                                             │
│  Baseado em 2,847 mensagens dos últimos 30 dias            │
│  Confiança: 85%                                             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### Score Ranges (Visual Treatment)

| Range | Label | Color | Emoji |
|-------|-------|-------|-------|
| 85-100 | Florescente | Green gradient | 🌸 |
| 70-84 | Saudável | Blue gradient | 💙 |
| 55-69 | Estável | Yellow | ⚖️ |
| 40-54 | Atenção | Orange | ⚠️ |
| 25-39 | Preocupante | Red-orange | 🔶 |
| 0-24 | Crítico | Red | 🚨 |

---

### Section 2: Four Dimensions (Expandable Cards)

```
┌─────────────────────────────────────────────────────────────┐
│  AS 4 DIMENSÕES DO SEU RELACIONAMENTO                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │ 💕 Conexão           │  │ 🌱 Manutenção        │        │
│  │                      │  │                      │        │
│  │      68              │  │      78              │        │
│  │   ───────────        │  │   ───────────        │        │
│  │                      │  │                      │        │
│  │ Respostas podem      │  │ Proporção 4.8:1      │        │
│  │ ser mais profundas   │  │ quase no ideal!      │        │
│  │                      │  │                      │        │
│  │     [Ver mais]       │  │     [Ver mais]       │        │
│  └──────────────────────┘  └──────────────────────┘        │
│                                                             │
│  ┌──────────────────────┐  ┌──────────────────────┐        │
│  │ 💬 Comunicação       │  │ 🤝 Parceria          │        │
│  │                      │  │                      │        │
│  │      74              │  │      68              │        │
│  │   ───────────        │  │   ───────────        │        │
│  │                      │  │                      │        │
│  │ Bons padrões de      │  │ Participação         │        │
│  │ reparação            │  │ equilibrada          │        │
│  │                      │  │                      │        │
│  │     [Ver mais]       │  │     [Ver mais]       │        │
│  └──────────────────────┘  └──────────────────────┘        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

#### Expanded Dimension View (Conexão)

```
┌─────────────────────────────────────────────────────────────┐
│  ← Voltar                                                   │
│                                                             │
│  💕 CONEXÃO                                          68/100 │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  "A qualidade da sua resposta quando seu parceiro          │
│   compartilha sentimentos"                                  │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  COMPONENTES                                        │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │                                                     │   │
│  │  Responsividade           ████████████░░░░░  65    │   │
│  │  Quando você responde a mensagens emocionais       │   │
│  │                                                     │   │
│  │  Expressão Emocional      █████████████░░░░  72    │   │
│  │  Sua abertura ao compartilhar sentimentos          │   │
│  │                                                     │   │
│  │  Reciprocidade            ████████████░░░░░  67    │   │
│  │  Equilíbrio na troca emocional                     │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  💡 INSIGHT                                         │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │                                                     │   │
│  │  Quando seu parceiro diz "estou estressado",       │   │
│  │  tente validar antes de resolver:                  │   │
│  │                                                     │   │
│  │  ❌ "Ok" ou "E o que você quer que eu faça?"       │   │
│  │  ✅ "Entendo, quer conversar sobre isso?"          │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  📈 TENDÊNCIA (últimos 90 dias)                     │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │       ╭─╮                                          │   │
│  │      ╭╯ ╰─╮    ╭──╮                               │   │
│  │  ───╯     ╰────╯  ╰──●                            │   │
│  │  Nov      Dez       Jan                           │   │
│  │                      ↑ Você está aqui             │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### Section 3: Strengths & Growth Areas

```
┌─────────────────────────────────────────────────────────────┐
│  O QUE ESTÁ FUNCIONANDO BEM 💪                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  🌟 Proporção Positiva                              │   │
│  │                                                     │   │
│  │  Vocês têm 4.8 interações positivas para cada      │   │
│  │  negativa. Pesquisas mostram que 5:1 é o ideal.    │   │
│  │                                                     │   │
│  │  ████████████████████████████████████████░░░░░░░░  │   │
│  │  4.8:1                                    Meta: 5:1│   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  🔧 Reparação de Conflitos                          │   │
│  │                                                     │   │
│  │  85% das tentativas de reparação são bem           │   │
│  │  sucedidas. Isso é excelente!                      │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  ÁREAS PARA CRESCER 🌱                                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  ⚠️ Atenção: Padrões de Desprezo                    │   │
│  │                                                     │   │
│  │  Detectamos 2 instâncias de sarcasmo/desprezo      │   │
│  │  esta semana. Este é o padrão mais destrutivo.     │   │
│  │                                                     │   │
│  │  📖 Exemplos detectados:                            │   │
│  │  • "Parabéns, você só levou 3 horas"               │   │
│  │  • "Grande coisa" (em resposta a boa notícia)      │   │
│  │                                                     │   │
│  │  💡 Antídoto: Cultura de Apreciação                │   │
│  │  Expressar gratidão específica diariamente:        │   │
│  │  "Obrigado por ter feito X, isso significou muito" │   │
│  │                                                     │   │
│  │                        [Entendi, quero melhorar]   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### Section 4: Four Horsemen Monitor

```
┌─────────────────────────────────────────────────────────────┐
│  OS 4 CAVALEIROS (Gottman)                                  │
│  Padrões que predizem problemas com 90%+ de precisão       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌────────┐│
│  │  Crítica    │ │  Desprezo   │ │ Defensivid. │ │Stonew. ││
│  │             │ │             │ │             │ │        ││
│  │     3       │ │     2       │ │     1       │ │   0    ││
│  │   ⚠️ médio  │ │  🚨 alto    │ │   ✓ baixo   │ │ ✓ zero ││
│  │             │ │             │ │             │ │        ││
│  │  [detalhes] │ │  [detalhes] │ │  [detalhes] │ │        ││
│  └─────────────┘ └─────────────┘ └─────────────┘ └────────┘│
│                                                             │
│  ℹ️ Desprezo é o preditor mais forte de dissolução.        │
│     Priorize construir cultura de apreciação.              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### Section 5: Weekly Pulse (Timeline)

```
┌─────────────────────────────────────────────────────────────┐
│  PULSO SEMANAL                                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Seg   Ter   Qua   Qui   Sex   Sab   Dom                   │
│   │     │     │     │     │     │     │                    │
│   ●     ●     ●     ○     ●     ●     ●                    │
│   │     │     │     │     │     │     │                    │
│  ───────────────────────────────────────                    │
│   74    76    72    58    71    78    75                   │
│                     ↑                                       │
│              Conflito detectado                             │
│              (reparado com sucesso)                         │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  Quinta-feira, 23 Jan                               │   │
│  │                                                     │   │
│  │  📉 Queda temporária (58)                           │   │
│  │  • 1 crítica detectada                              │   │
│  │  • 1 resposta dismissiva                            │   │
│  │                                                     │   │
│  │  ✅ Reparação bem sucedida                          │   │
│  │  • "Desculpa, eu errei. Não deveria ter..."        │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### Section 6: LLM Insights (Premium Feature)

```
┌─────────────────────────────────────────────────────────────┐
│  🧠 ANÁLISE PROFUNDA (IA)                          Premium │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Nossa IA analisou 17 momentos-chave esta semana:          │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  🎯 SARCASMO DETECTADO                              │   │
│  │                                                     │   │
│  │  "Parabéns, você só levou 3 horas"                 │   │
│  │                                                     │   │
│  │  A IA detectou sarcasmo que uma análise simples    │   │
│  │  teria confundido com parabéns genuíno.            │   │
│  │                                                     │   │
│  │  Confiança: 85%                                     │   │
│  │  Severidade: Moderada                               │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  🔍 DESCULPA FALSA DETECTADA                        │   │
│  │                                                     │   │
│  │  "Você tem razão, MAS você também não ajudou"      │   │
│  │                                                     │   │
│  │  Esta desculpa transfere culpa para o parceiro.    │   │
│  │  Reparações genuínas assumem responsabilidade      │   │
│  │  sem "mas".                                         │   │
│  │                                                     │   │
│  │  ✅ Sugestão: "Você tem razão, eu deveria ter      │   │
│  │     prestado mais atenção. Desculpa."              │   │
│  │                                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  Custo desta análise: $0.27 | 17 mensagens analisadas      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Structure for UI

### API Response Schema

```typescript
interface HealthTabData {
  // Hero Score
  score: {
    overall: number;           // 0-100
    label: string;             // "Saudável"
    labelEn: string;           // "Healthy"
    trend: {
      direction: 'up' | 'down' | 'stable';
      change: number;          // +3
      period: string;          // "vs. mês passado"
    };
    confidence: number;        // 0.85
    dataPoints: {
      messages: number;        // 2847
      period: string;          // "últimos 30 dias"
    };
  };

  // Four Dimensions
  dimensions: {
    connection: DimensionData;
    maintenance: DimensionData;
    communication: DimensionData;
    partnership: DimensionData;
  };

  // Insights
  insights: {
    strengths: Insight[];
    opportunities: Insight[];
    alerts: Alert[];
  };

  // Four Horsemen
  horsemen: {
    criticism: HorsemanData;
    contempt: HorsemanData;
    defensiveness: HorsemanData;
    stonewalling: HorsemanData;
  };

  // Timeline
  weeklyPulse: DayData[];

  // LLM Analysis (Premium)
  llmAnalysis?: {
    enabled: boolean;
    cost: number;
    analyses: LLMInsight[];
  };
}

interface DimensionData {
  score: number;
  icon: string;
  title: string;
  subtitle: string;
  components: ComponentData[];
  insight: string;
  trend: TrendData;
}

interface ComponentData {
  name: string;
  score: number;
  description: string;
  detail?: string;          // e.g., "4.8:1" for ratio
}

interface Insight {
  dimension: string;
  title: string;
  finding: string;
  evidence?: string;
  suggestion?: string;
  impact?: 'high' | 'medium' | 'low';
}

interface Alert {
  pattern: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  frequency: string;
  examples: string[];
  antidote: {
    title: string;
    description: string;
    example: string;
  };
}

interface HorsemanData {
  count: number;
  severity: 'critical' | 'high' | 'medium' | 'low' | 'none';
  instances: HorsemanInstance[];
  antidote: string;
}

interface DayData {
  date: string;
  score: number;
  hasConflict: boolean;
  wasRepaired: boolean;
  highlights: string[];
}

interface LLMInsight {
  type: 'contempt' | 'response_quality' | 'repair' | 'vulnerability';
  message: string;
  result: any;
  confidence: number;
  suggestion?: string;
}
```

---

## Navigation Flow

```
Health Tab (Main)
├── Hero Score Card
│   └── [Tap] → Score History Modal
│
├── Dimensions Grid
│   ├── Connection Card
│   │   └── [Tap] → Connection Detail Screen
│   │       ├── Components breakdown
│   │       ├── Insight cards
│   │       └── Trend chart
│   ├── Maintenance Card → Detail Screen
│   ├── Communication Card → Detail Screen
│   └── Partnership Card → Detail Screen
│
├── Strengths Section
│   └── [Tap card] → Expand with evidence
│
├── Growth Areas Section
│   └── [Tap card] → Expand with examples + antidote
│
├── Four Horsemen Monitor
│   └── [Tap horseman] → Detail Modal
│       ├── Instances list
│       ├── Antidote explanation
│       └── Practice exercises
│
├── Weekly Pulse
│   └── [Tap day] → Day Detail Card
│
└── LLM Insights (Premium)
    └── [Tap insight] → Expand with full analysis
```

---

## Color Palette

```css
/* Score Colors */
--score-flourishing: linear-gradient(135deg, #10B981, #34D399);
--score-healthy: linear-gradient(135deg, #3B82F6, #60A5FA);
--score-stable: #F59E0B;
--score-attention: #F97316;
--score-concerning: #EF4444;
--score-critical: #DC2626;

/* Dimension Colors */
--dim-connection: #EC4899;    /* Pink */
--dim-maintenance: #10B981;   /* Green */
--dim-communication: #6366F1; /* Indigo */
--dim-partnership: #F59E0B;   /* Amber */

/* Horsemen Colors */
--horseman-safe: #10B981;     /* Green */
--horseman-low: #60A5FA;      /* Blue */
--horseman-medium: #F59E0B;   /* Amber */
--horseman-high: #EF4444;     /* Red */
--horseman-critical: #DC2626; /* Dark Red */

/* UI Colors */
--bg-primary: #0F172A;        /* Dark blue-gray */
--bg-card: #1E293B;           /* Lighter card bg */
--text-primary: #F8FAFC;
--text-secondary: #94A3B8;
--accent: #6366F1;
```

---

## Animations & Micro-interactions

1. **Score Counter** - Animate from 0 to final score on load
2. **Dimension Cards** - Subtle pulse on the lowest scoring dimension
3. **Alert Cards** - Gentle shake animation on critical alerts
4. **Progress Bars** - Fill animation with easing
5. **Weekly Pulse** - Dot pulse animation on today's score
6. **Expand/Collapse** - Smooth height transitions

---

## Gamification Elements (Optional)

### Streaks

```
┌─────────────────────────────────────────────────────────────┐
│  🔥 7 dias consecutivos acima de 70!                        │
│  Continue assim para desbloquear o badge "Semana Saudável" │
└─────────────────────────────────────────────────────────────┘
```

### Badges

| Badge | Criteria | Icon |
|-------|----------|------|
| Semana Saudável | 7 dias >70 | 🏆 |
| Reparador | 5 reparações bem sucedidas | 🔧 |
| Comunicador | 0 cavaleiros em 7 dias | 💬 |
| Florescente | Score >85 por 30 dias | 🌸 |

---

## Privacy Considerations

1. **Individual Views** - Each partner sees their own contribution metrics
2. **No Blame** - Insights focus on "we can improve" not "you did wrong"
3. **Optional Sharing** - Couples can choose to share their tab
4. **Data Retention** - Clear data age and retention policies
5. **Export** - Allow data export for therapy sessions

---

## Implementation Priority

### Phase 1 (MVP)
- [ ] Hero Score Card
- [ ] Dimension Cards (collapsed view)
- [ ] Strengths & Growth sections
- [ ] Four Horsemen Monitor

### Phase 2
- [ ] Dimension Detail Screens
- [ ] Weekly Pulse Timeline
- [ ] Trend Charts

### Phase 3 (Premium)
- [ ] LLM Insights
- [ ] Gamification
- [ ] Partner Sharing
- [ ] Export for Therapy

---

---

## Interactive Detail Views (v2.2)

### Dimension Card Click → Modal Detail View

Each dimension card is clickable and opens a modal with:

1. **Score Display** - Large score number with color coding
2. **Components Breakdown** - Each sub-component with individual scores
3. **LLM Analysis Notes** - AI-generated observation about the pattern
4. **Example Conversations** - Real messages that contributed to the score

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  💕 Conexão Emocional                                   ✕   │
│                                                             │
│                      100                                    │
│              ────────────────                               │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  COMPONENTES                                        │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │  Responsividade        ████████████████████  100    │   │
│  │  10.5/semana | Altamente responsivo                 │   │
│  │                                                     │   │
│  │  Vulnerabilidade       ████████████████████  100    │   │
│  │  6.3/semana | Alta abertura emocional               │   │
│  │                                                     │   │
│  │  Sintonia              ████████████████████  100    │   │
│  │  8.4/semana | Alta sintonia emocional               │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  EXEMPLOS                                           │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │  vulnerability                                      │   │
│  │  ┌──────────────────────────────────────────────┐   │   │
│  │  │ 💚 positivo                                  │   │   │
│  │  │ Person A                                     │   │   │
│  │  │ "Estou preocupado com..."                    │   │   │
│  │  └──────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Horseman Card Click → Modal Detail View

Each Four Horsemen indicator is clickable and opens a modal with:

1. **Count Display** - Number of instances with severity color
2. **Description** - What this pattern means
3. **Antidote** - Research-backed solution
4. **Example Messages** - Real detected instances (if any)

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  ⚔️ Desprezo                                            ✕   │
│                                                             │
│                       0                                     │
│              ────────────────                               │
│           instâncias nos últimos 30 dias                    │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  O QUE É                                            │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │  Sarcasmo, cinismo, revirar de olhos, tom de        │   │
│  │  superioridade.                                     │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  💡 ANTÍDOTO                                        │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │  Construir cultura de apreciação. Expressar         │   │
│  │  gratidão diária específica.                        │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  EXEMPLOS DETECTADOS                                │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │  Nenhum exemplo disponível                          │   │
│  │  ✅ Excelente! Nenhum desprezo detectado.           │   │
│  └─────────────────────────────────────────────────────┘   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Modal CSS Classes

```css
/* Modal Overlay */
.modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0, 0, 0, 0.8);
    z-index: 1000;
    display: none;
    align-items: center;
    justify-content: center;
}

.modal-overlay.active {
    display: flex;
}

.modal-content {
    background: var(--bg-secondary);
    border-radius: 20px;
    width: 90%;
    max-width: 360px;
    max-height: 80vh;
    overflow-y: auto;
    padding: 24px;
    animation: slideUp 0.3s ease-out;
}

/* Example message styling */
.example-message {
    background: var(--bg-card);
    border-radius: 12px;
    padding: 12px;
    margin-bottom: 12px;
    border-left: 3px solid var(--accent);
}

.example-message.positive {
    border-left-color: var(--success);
    background: rgba(16, 185, 129, 0.05);
}

.example-message.negative {
    border-left-color: var(--danger);
    background: rgba(239, 68, 68, 0.05);
}

.example-type-badge {
    display: inline-block;
    font-size: 10px;
    padding: 2px 6px;
    border-radius: 4px;
    margin-bottom: 6px;
}

.example-type-badge.positive {
    background: rgba(16, 185, 129, 0.2);
    color: var(--success);
}

.example-type-badge.negative {
    background: rgba(239, 68, 68, 0.2);
    color: var(--danger);
}
```

### JavaScript Functions

```javascript
// Global state for current data
let currentData = null;

function showModal(content) {
    document.getElementById('modalContent').innerHTML = content;
    document.getElementById('modalOverlay').classList.add('active');
}

function hideModal() {
    document.getElementById('modalOverlay').classList.remove('active');
}

function showDimensionDetail(key) {
    const dim = currentData.healthScore.dimensions[key];
    // Build HTML with components, scores, and examples
    // ...
    showModal(html);
}

function showHorsemanDetail(key) {
    const components = currentData.healthScore.dimensions.communicationHealth.components;
    // Build HTML with description, antidote, and examples
    // ...
    showModal(html);
}

// Close on overlay click
document.getElementById('modalOverlay').addEventListener('click', (e) => {
    if (e.target.id === 'modalOverlay') hideModal();
});
```

---

## Implementation Status (v2.2)

### Phase 1 (MVP) ✅
- [x] Hero Score Card
- [x] Dimension Cards (collapsed view)
- [x] Four Horsemen Monitor
- [x] Weekly Pulse Timeline

### Phase 2 ✅
- [x] Dimension Detail Modal Views
- [x] Horseman Detail Modal Views
- [x] Example Conversations Display
- [x] LLM-validated scores and insights

### Phase 3 (Future)
- [ ] LLM Deep Insights (additional analysis)
- [ ] Gamification (streaks, badges)
- [ ] Partner Sharing
- [ ] Export for Therapy

---

*Specification v2.2 - NAVI Relationship Health Tab*
