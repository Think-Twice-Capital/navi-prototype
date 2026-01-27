# NAVI WhatsApp Analyzer Output Specification

> Complete specification for the WhatsApp chat analyzer that generates categorized messages, scoring metrics, and AI agent contexts.

---

## Table of Contents

1. [Overview](#overview)
2. [Output 1: Categorized Messages for UI](#output-1-categorized-messages-for-ui)
3. [Output 2: Scoring System](#output-2-scoring-system)
4. [Output 3: AI Agent Contexts](#output-3-ai-agent-contexts)
5. [Detection Rules & Keywords](#detection-rules--keywords)
6. [Scoring Calculation Formulas](#scoring-calculation-formulas)
7. [Configuration](#configuration)

---

## Overview

The NAVI WhatsApp Analyzer processes chat exports and generates three key outputs:

| Output | Purpose | Consumer |
|--------|---------|----------|
| Categorized Messages | Display conversations grouped by topic/status | NAVI UI |
| Scoring System | Track relationship health metrics | Dashboard & Insights |
| AI Agent Contexts | Personalized guidance for each party | Individual AI Agents |

---

## Output 1: Categorized Messages for UI

### 1.1 Space/Topic Mapping

Each message group is categorized into a "space" that maps to the UI navigation.

| Analyzer Topic | UI Space | Icon | Color | Description |
|---------------|----------|------|-------|-------------|
| `trabalho` | trabalho | 💼 | `#3498db` | Work-related discussions, meetings, deadlines |
| `casa` | casa | 🏠 | `#e67e22` | Household tasks, bills, maintenance |
| `filhos` | filhos | 👨‍👩‍👧 | `#9b59b6` | Children activities, school, health |
| `viagem` | viagem | ✈️ | `#1abc9c` | Travel planning, trips, vacations |
| `saude` | saude | 🏥 | `#e74c3c` | Health appointments, wellness, medical |
| `financas` | financas | 💰 | `#f1c40f` | Financial decisions, investments, budgeting |
| `lazer` | lazer | 🎉 | `#2ecc71` | Entertainment, hobbies, social events |
| `relacionamento` | nos | ❤️ | `#e91e63` | Relationship moments, affection, connection |

### 1.2 Message Group Schema

Message groups aggregate related messages into actionable conversation threads.

```json
{
  "messageGroups": [
    {
      "id": "string (UUID v4)",
      "space": "string (one of: trabalho|casa|filhos|viagem|saude|financas|lazer|nos)",
      "status": "string (one of: pending|done|urgent|scheduled|connection)",
      "statusLabel": "string (localized display label with emoji)",
      "summary": "string (concise description, max 50 chars)",
      "hasAction": "boolean (true if requires action)",
      "dueDate": "string|null (ISO date if applicable)",
      "owner": "string|null (thiago|daniela|both)",
      "messages": [
        {
          "time": "string (HH:mm format)",
          "sender": "string (T|D for initials)",
          "senderName": "string (full name)",
          "text": "string (message content)",
          "type": "string (text|image|audio|document|sticker)"
        }
      ]
    }
  ]
}
```

#### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier (UUID v4) for the message group |
| `space` | string | Yes | Topic category from the mapping table |
| `status` | string | Yes | Current status of the conversation thread |
| `statusLabel` | string | Yes | Human-readable status with emoji prefix |
| `summary` | string | Yes | Brief description of the main topic/action |
| `hasAction` | boolean | Yes | Whether this group requires someone to take action |
| `dueDate` | string | No | Due date in ISO format (YYYY-MM-DD) if time-sensitive |
| `owner` | string | No | Who is responsible for the action |
| `messages` | array | Yes | Chronologically ordered messages in this group |

#### Status Labels Mapping

| Status | statusLabel | Description |
|--------|-------------|-------------|
| `pending` | ⏳ Pendente | Awaiting action |
| `done` | ✅ Feito | Completed |
| `urgent` | 🔴 Urgente | Needs immediate attention |
| `scheduled` | 📅 Agendado | Planned for specific date/time |
| `connection` | 💕 Conexão | Emotional/relationship moment |

### 1.3 Status Detection Rules

The analyzer determines status based on linguistic patterns in Portuguese.

| Status | Detection Rules | Example Triggers |
|--------|----------------|------------------|
| `pending` | Action verbs present + no completion marker | "Tem que pagar", "Precisa comprar", "Você pode fazer" |
| `done` | Completion markers present | "feito", "pago", "pronto", "já fiz", ✓ emoji, "ok feito" |
| `urgent` | Urgency words + pending status | "hoje", "agora", "urgente", "não pode atrasar" |
| `scheduled` | Future time references + no urgency | "amanhã", "segunda", "às 14h", "semana que vem" |
| `connection` | High sentiment + relationship keywords + no action needed | "te amo", "saudade", "❤️", "obrigada por tudo" |

#### Detailed Detection Patterns

**Pending Detection:**
```
Pattern: (action_verb) + (object) + NOT(completion_marker)
Action verbs: pagar, fazer, comprar, ligar, marcar, resolver, buscar, levar, enviar
Example: "Tem que pagar um DARF hoje!" → pending (has "pagar", no completion)
```

**Done Detection:**
```
Pattern: (completion_marker) OR (confirmation + past_tense)
Completion markers: feito, pago, pronto, resolvido, comprado, já fiz, tá feito
Confirmation: ok, pode deixar, combinado + evidence of action
Example: "Pago! ✓" → done
```

**Urgent Detection:**
```
Pattern: (pending) + (urgency_marker)
Urgency markers: hoje, agora, urgente, precisamos, não pode atrasar, deadline
Time proximity: Due date is today or overdue
Example: "Urgente! Precisa assinar hoje" → urgent
```

**Scheduled Detection:**
```
Pattern: (future_reference) + NOT(urgency_marker)
Future references: amanhã, segunda, terça, próxima semana, às Xh, dia DD
Example: "Pediatra marcado para terça às 14h" → scheduled
```

**Connection Detection:**
```
Pattern: (affection_marker) + (positive_sentiment) + NOT(action_verb)
Affection markers: te amo, saudade, obrigada, você é incrível, ❤️, 😘
Example: "Você é o melhor ❤️" → connection
```

### 1.4 Task Extraction Schema

Tasks are actionable items extracted from message groups.

```json
{
  "tasks": [
    {
      "id": "string (UUID v4)",
      "title": "string (action + object + details)",
      "space": "string (topic category)",
      "status": "string (pending|done|urgent|scheduled)",
      "due": "string|null (human-readable due date)",
      "owner": "string|null (thiago|daniela|both)",
      "sourceGroupId": "string (reference to message group)",
      "extractedFrom": "string (original message text)"
    }
  ]
}
```

#### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique identifier for the task |
| `title` | string | Yes | Formatted task title with key details (amount, item, etc.) |
| `space` | string | Yes | Topic category the task belongs to |
| `status` | string | Yes | Current task status |
| `due` | string | No | Human-readable due description ("Hoje", "Amanhã", "Até sexta") |
| `owner` | string | No | Person responsible for completing the task |
| `sourceGroupId` | string | Yes | Reference to the originating message group |
| `extractedFrom` | string | Yes | The original message text that generated this task |

#### Task Title Formatting Rules

1. **Financial tasks**: Include amount with currency formatting
   - Input: "pagar o DARF de 1247 reais"
   - Output: "Pagar DARF - R$1.247,00"

2. **Appointment tasks**: Include time and location
   - Input: "marcar pediatra pra terça 14h"
   - Output: "Pediatra - Terça 14h"

3. **Purchase tasks**: Include item and quantity if mentioned
   - Input: "comprar uniforme novo da Bia"
   - Output: "Comprar uniforme - Bia"

---

## Output 2: Scoring System

### 2.1 Health Score Schema

The health score provides an overall relationship health metric from 1-10.

```json
{
  "healthScore": {
    "overall": "number (1.0-10.0, one decimal place)",
    "label": "string (Crítico|Preocupante|Moderado|Saudável|Excelente)",
    "trend": "string (improving|stable|declining)",
    "components": {
      "responseSymmetry": {
        "score": "number (1.0-10.0)",
        "percentage": "number (0-100)",
        "description": "string"
      },
      "topicDiversity": {
        "score": "number (1.0-10.0)",
        "value": "string (X/8 topics)",
        "description": "string"
      },
      "sentimentTrend": {
        "score": "number (1.0-10.0)",
        "trend": "string (+/-X%)",
        "description": "string"
      },
      "affectionFrequency": {
        "score": "number (1.0-10.0)",
        "perWeek": "number",
        "description": "string"
      },
      "conversationFrequency": {
        "score": "number (1.0-10.0)",
        "perDay": "number",
        "description": "string"
      }
    }
  }
}
```

#### Health Score Labels

| Score Range | Label | Color | Interpretation |
|-------------|-------|-------|----------------|
| 1.0 - 3.0 | Crítico | `#e74c3c` | Needs immediate attention |
| 3.1 - 5.0 | Preocupante | `#e67e22` | Several areas need improvement |
| 5.1 - 6.5 | Moderado | `#f1c40f` | Room for improvement |
| 6.6 - 8.0 | Saudável | `#2ecc71` | Good relationship dynamics |
| 8.1 - 10.0 | Excelente | `#27ae60` | Outstanding communication |

#### Component Descriptions

| Component | Weight | What it Measures |
|-----------|--------|------------------|
| `responseSymmetry` | 20% | Balance in who responds to whom |
| `topicDiversity` | 15% | Variety of subjects discussed |
| `sentimentTrend` | 25% | Emotional tone trajectory over time |
| `affectionFrequency` | 20% | Frequency of affectionate expressions |
| `conversationFrequency` | 20% | Volume and consistency of communication |

### 2.2 Balance Metrics Schema

Balance metrics track equitable participation in the relationship.

```json
{
  "balance": {
    "taskDistribution": {
      "thiago": "number (percentage 0-100)",
      "daniela": "number (percentage 0-100)",
      "trend": "string (balanced|thiago_increasing|daniela_increasing)",
      "history": [
        {
          "week": "string (ISO week)",
          "thiago": "number",
          "daniela": "number"
        }
      ]
    },
    "conversationInitiation": {
      "thiago": "number (percentage 0-100)",
      "daniela": "number (percentage 0-100)"
    },
    "responseTime": {
      "thiago": {
        "avg": "string (Xmin)",
        "median": "string (Xmin)",
        "byContext": {
          "urgent": "string",
          "routine": "string"
        }
      },
      "daniela": {
        "avg": "string (Xmin)",
        "median": "string (Xmin)",
        "byContext": {
          "urgent": "string",
          "routine": "string"
        }
      }
    },
    "messageVolume": {
      "thiago": "number (percentage 0-100)",
      "daniela": "number (percentage 0-100)"
    }
  }
}
```

#### Balance Interpretation

| Metric | Healthy Range | Warning Signs |
|--------|---------------|---------------|
| Task Distribution | 40-60% each | >70% one person consistently |
| Conversation Initiation | 35-65% each | >80% one person always starts |
| Response Time | Both <15min avg | One >30min, other <5min |
| Message Volume | 40-60% each | >75% one person |

### 2.3 Weekly Stats Schema

Aggregated statistics for the past week.

```json
{
  "weeklyStats": {
    "period": {
      "start": "string (ISO date)",
      "end": "string (ISO date)"
    },
    "messagesExchanged": "number",
    "tasksCompleted": "number",
    "tasksPending": "number",
    "connectionMoments": "number",
    "mostActiveTopic": "string (space name)",
    "topicBreakdown": {
      "trabalho": "number (percentage)",
      "casa": "number (percentage)",
      "filhos": "number (percentage)",
      "viagem": "number (percentage)",
      "saude": "number (percentage)",
      "financas": "number (percentage)",
      "lazer": "number (percentage)",
      "nos": "number (percentage)"
    },
    "stressEvents": "number",
    "celebrationMoments": "number",
    "longestConversation": {
      "topic": "string",
      "messages": "number",
      "duration": "string"
    }
  }
}
```

---

## Output 3: AI Agent Contexts

### 3.1 Individual Agent Context Schema

Private context for each person's AI agent.

```json
{
  "agentContext": {
    "user": "string (thiago|daniela)",
    "partner": "string (thiago|daniela)",
    "lastUpdated": "string (ISO datetime)",

    "communicationPatterns": {
      "responseStyle": "string (concise|detailed|variable)",
      "avgResponseLength": "number (words)",
      "typicalResponses": ["array of common response patterns"],
      "responseTimeByContext": {
        "urgent": "string (Xmin)",
        "routine": "string (Xmin)",
        "emotional": "string (Xmin)"
      },
      "preferredChannels": {
        "quickUpdates": "string (text|audio)",
        "importantMatters": "string (text|call)",
        "emotional": "string (text|audio|call)"
      }
    },

    "strengths": [
      {
        "pattern": "string (snake_case identifier)",
        "description": "string (what they do well)",
        "evidence": "string (specific example from chat)",
        "frequency": "string (how often observed)"
      }
    ],

    "areasForGrowth": [
      {
        "pattern": "string (snake_case identifier)",
        "description": "string (what could be improved)",
        "frequency": "string (how often occurs)",
        "suggestion": "string (specific actionable advice)",
        "impact": "string (how it affects partner)"
      }
    ],

    "topicExpertise": {
      "primary": ["array of spaces they lead"],
      "secondary": ["array of spaces they support"],
      "partner_leads": ["array of spaces partner leads"]
    },

    "stressIndicators": {
      "triggers": ["array of known stress triggers"],
      "signals": ["array of behavioral changes when stressed"],
      "supportPreference": "string (how they prefer support)"
    },

    "appreciationLanguage": {
      "givesAppreciation": "string (how they show gratitude)",
      "receivesAppreciation": "string (what makes them feel valued)"
    }
  }
}
```

#### Thiago's Agent Context Example

```json
{
  "agentContext": {
    "user": "thiago",
    "partner": "daniela",
    "lastUpdated": "2024-01-20T10:00:00Z",

    "communicationPatterns": {
      "responseStyle": "concise",
      "avgResponseLength": 12,
      "typicalResponses": ["Ok", "👍", "Pode deixar", "Feito"],
      "responseTimeByContext": {
        "urgent": "2min",
        "routine": "15min",
        "emotional": "8min"
      },
      "preferredChannels": {
        "quickUpdates": "text",
        "importantMatters": "text",
        "emotional": "text"
      }
    },

    "strengths": [
      {
        "pattern": "quick_action",
        "description": "Age rapidamente em pedidos urgentes",
        "evidence": "Pagou DARF em 2h após pedido",
        "frequency": "90% das urgências"
      },
      {
        "pattern": "proactive_care",
        "description": "Assume responsabilidades sem ser pedido",
        "evidence": "Pediu pizza quando Daniela ia chegar tarde",
        "frequency": "Semanal"
      },
      {
        "pattern": "crisis_response",
        "description": "Reorganiza agenda para apoiar em emergências",
        "evidence": "Cuidou das meninas quando Daniela teve deadline",
        "frequency": "Sempre que necessário"
      }
    ],

    "areasForGrowth": [
      {
        "pattern": "brief_acknowledgment",
        "description": "Respostas curtas em pedidos importantes",
        "frequency": "73% das vezes",
        "suggestion": "Adicionar confirmação específica: 'Pode deixar, faço até 12h'",
        "impact": "Daniela reenvia mensagem após 'Ok' por incerteza"
      },
      {
        "pattern": "delayed_emotional_response",
        "description": "Demora para responder mensagens emocionais",
        "frequency": "Ocasional",
        "suggestion": "Priorizar mensagens com conteúdo emocional",
        "impact": "Daniela pode interpretar como desinteresse"
      }
    ],

    "topicExpertise": {
      "primary": ["financas", "casa"],
      "secondary": ["filhos"],
      "partner_leads": ["trabalho", "saude"]
    },

    "stressIndicators": {
      "triggers": ["Múltiplas tarefas simultâneas", "Prazo apertado trabalho"],
      "signals": ["Respostas monossilábicas", "Demora para responder"],
      "supportPreference": "Espaço para resolver sozinho"
    },

    "appreciationLanguage": {
      "givesAppreciation": "Ações práticas de suporte",
      "receivesAppreciation": "Reconhecimento verbal específico"
    }
  }
}
```

#### Daniela's Agent Context Example

```json
{
  "agentContext": {
    "user": "daniela",
    "partner": "thiago",
    "lastUpdated": "2024-01-20T10:00:00Z",

    "communicationPatterns": {
      "responseStyle": "detailed",
      "avgResponseLength": 28,
      "typicalPatterns": [
        "Múltiplas mensagens para um tópico",
        "Detalhes enviados separadamente",
        "Uso frequente de emojis"
      ],
      "responseTimeByContext": {
        "urgent": "3min",
        "routine": "10min",
        "emotional": "2min"
      },
      "preferredChannels": {
        "quickUpdates": "text",
        "importantMatters": "text",
        "emotional": "text"
      }
    },

    "strengths": [
      {
        "pattern": "explicit_gratitude",
        "description": "Expressa gratidão de forma específica e calorosa",
        "evidence": "'Você é o melhor ❤️' após Thiago cuidar das meninas",
        "frequency": "Diário"
      },
      {
        "pattern": "proactive_planning",
        "description": "Antecipa necessidades e organiza com antecedência",
        "evidence": "Reservou restaurante, planejou uniforme, organizou agenda",
        "frequency": "Constante"
      },
      {
        "pattern": "emotional_check_ins",
        "description": "Verifica como parceiro está se sentindo",
        "evidence": "Pergunta sobre dia de trabalho, expressa preocupação",
        "frequency": "Diário"
      }
    ],

    "areasForGrowth": [
      {
        "pattern": "fragmented_requests",
        "description": "Envia pedidos em múltiplas mensagens separadas",
        "frequency": "60% dos pedidos",
        "suggestion": "Consolidar informações: 'Pagar DARF R$1.247 - vence hoje - [foto]'",
        "impact": "Thiago pode perder detalhes entre mensagens"
      },
      {
        "pattern": "implicit_expectations",
        "description": "Assume que parceiro entendeu prioridade sem explicitar",
        "frequency": "Ocasional",
        "suggestion": "Adicionar urgência explícita quando necessário",
        "impact": "Frustração quando expectativa não é atendida"
      }
    ],

    "topicExpertise": {
      "primary": ["trabalho", "saude", "filhos"],
      "secondary": ["viagem", "lazer"],
      "partner_leads": ["financas", "casa"]
    },

    "stressIndicators": {
      "triggers": ["Lia agenda reuniões de última hora", "Crianças doentes"],
      "signals": ["Mensagens mais curtas", "Menos emojis", "Respostas atrasadas"],
      "supportPreference": "Assumir responsabilidades práticas"
    },

    "appreciationLanguage": {
      "givesAppreciation": "Expressões verbais carinhosas",
      "receivesAppreciation": "Ações que demonstram cuidado"
    }
  }
}
```

### 3.2 Community Manager Context Schema

Shared context for the relationship-level AI agent.

```json
{
  "communityContext": {
    "couple": ["string (person1)", "string (person2)"],
    "lastUpdated": "string (ISO datetime)",

    "relationshipDynamics": {
      "overallHealth": "number (1.0-10.0)",
      "healthTrend": "string (improving|stable|declining)",
      "strengthAreas": ["array of relationship strengths"],
      "growthAreas": ["array of areas needing attention"]
    },

    "successPatterns": [
      {
        "pattern": "string (identifier)",
        "description": "string (what works well)",
        "recentExample": {
          "date": "string (ISO date)",
          "trigger": "string (what started it)",
          "response": "string (how they handled it)",
          "outcome": "string (result)"
        },
        "frequency": "string (how often this happens)"
      }
    ],

    "attentionAreas": [
      {
        "area": "string (category)",
        "observation": "string (what was noticed)",
        "data": "string|object (supporting metrics)",
        "suggestion": "string (recommended action)",
        "priority": "string (high|medium|low)"
      }
    ],

    "pendingDecisions": [
      {
        "topic": "string (space)",
        "item": "string (description)",
        "daysOpen": "number",
        "lastMentioned": "string (ISO date)",
        "context": "string (relevant background)"
      }
    ],

    "celebrationMoments": [
      {
        "date": "string (ISO date)",
        "title": "string (moment description)",
        "quotes": ["array of key messages"],
        "significance": "string (why it matters)"
      }
    ],

    "suggestedActivities": [
      {
        "type": "string (couple_time|family_time|individual_support)",
        "suggestion": "string (specific recommendation)",
        "rationale": "string (why this is suggested)",
        "timing": "string (when to do it)",
        "priority": "string (high|medium|low)"
      }
    ],

    "communicationHealth": {
      "lastMeaningfulConversation": {
        "date": "string (ISO date)",
        "topic": "string",
        "sentiment": "string (positive|neutral|negative)"
      },
      "conflictStatus": {
        "unresolvedTopics": ["array of topics"],
        "lastDisagreement": "string|null (ISO date)",
        "resolutionPattern": "string (how they typically resolve)"
      }
    }
  }
}
```

#### Community Manager Context Example

```json
{
  "communityContext": {
    "couple": ["thiago", "daniela"],
    "lastUpdated": "2024-01-20T10:00:00Z",

    "relationshipDynamics": {
      "overallHealth": 7.8,
      "healthTrend": "stable",
      "strengthAreas": ["crisis_response", "task_collaboration", "mutual_support"],
      "growthAreas": ["scheduled_connection_time", "explicit_communication"]
    },

    "successPatterns": [
      {
        "pattern": "crisis_teamwork",
        "description": "Quando um tem imprevisto, outro assume responsabilidades",
        "recentExample": {
          "date": "2024-01-15",
          "trigger": "Daniela: deadline urgente com Lia",
          "response": "Thiago: pediu pizza, cuidou das meninas, organizou casa",
          "outcome": "Gratidão expressa, momento de conexão"
        },
        "frequency": "Semanal"
      },
      {
        "pattern": "coordinated_planning",
        "description": "Planejam juntos eventos familiares e compromissos",
        "recentExample": {
          "date": "2024-01-18",
          "trigger": "Jantar com amigos sábado",
          "response": "Coordenaram babá, reserva, horários",
          "outcome": "Evento confirmado sem conflitos"
        },
        "frequency": "Constante"
      }
    ],

    "attentionAreas": [
      {
        "area": "connection_time",
        "observation": "Último programa só de casal foi há 12 dias",
        "data": {
          "lastCoupleActivity": "2024-01-08",
          "daysSince": 12,
          "averageFrequency": "7 dias"
        },
        "suggestion": "Jantar de sábado é oportunidade - chegar 30min antes",
        "priority": "medium"
      },
      {
        "area": "pending_decisions",
        "observation": "Decisão sobre viagem pendente há 3 dias",
        "data": {
          "topic": "viagem",
          "item": "Lisboa R$2.400",
          "daysOpen": 3
        },
        "suggestion": "Definir até sexta para aproveitar preço",
        "priority": "high"
      }
    ],

    "pendingDecisions": [
      {
        "topic": "viagem",
        "item": "Passagens Lisboa - R$2.400 por pessoa",
        "daysOpen": 3,
        "lastMentioned": "2024-01-17",
        "context": "Promoção expira em 2 dias"
      },
      {
        "topic": "filhos",
        "item": "Escola de natação para Bia",
        "daysOpen": 7,
        "lastMentioned": "2024-01-13",
        "context": "Matrículas abertas até fim do mês"
      }
    ],

    "celebrationMoments": [
      {
        "date": "2024-01-15",
        "title": "Crise virou conexão",
        "quotes": [
          "Você é o melhor ❤️",
          "Não sei o que faria sem você"
        ],
        "significance": "Demonstrou parceria em momento de estresse"
      },
      {
        "date": "2024-01-10",
        "title": "7 anos de casados",
        "quotes": [
          "Te amo mais a cada ano",
          "Melhor decisão da minha vida"
        ],
        "significance": "Reafirmação do compromisso"
      }
    ],

    "suggestedActivities": [
      {
        "type": "couple_time",
        "suggestion": "Chegar 30min antes no japonês sábado para conversar só vocês",
        "rationale": "Mencionaram saudade de tempo a dois, jantar é oportunidade",
        "timing": "Sábado 19:00",
        "priority": "high"
      },
      {
        "type": "family_time",
        "suggestion": "Domingo de manhã - café da manhã especial com meninas",
        "rationale": "Semana corrida, momento de reconexão familiar",
        "timing": "Domingo manhã",
        "priority": "medium"
      }
    ],

    "communicationHealth": {
      "lastMeaningfulConversation": {
        "date": "2024-01-15",
        "topic": "Gratidão pelo suporte",
        "sentiment": "positive"
      },
      "conflictStatus": {
        "unresolvedTopics": [],
        "lastDisagreement": "2024-01-05",
        "resolutionPattern": "Conversam e resolvem em 24h"
      }
    }
  }
}
```

---

## Detection Rules & Keywords

### Topic Classification Keywords

#### trabalho
```
Keywords: trabalho, escritório, reunião, cliente, projeto, deadline,
          apresentação, relatório, chefe, colega, Lia, empresa
Patterns: "reunião às", "call com", "preciso entregar", "trabalho hoje"
```

#### casa
```
Keywords: casa, conta, DARF, IPTU, condomínio, mercado, compras,
          limpeza, conserto, reforma, móvel, eletrodoméstico
Patterns: "pagar conta", "comprar para casa", "precisa consertar"
```

#### filhos
```
Keywords: meninas, Bia, [nome das filhas], escola, pediatra,
          uniforme, lição, natação, ballet, aniversário
Patterns: "buscar na escola", "levar no médico", "festa de"
```

#### viagem
```
Keywords: viagem, passagem, hotel, Lisboa, voo, aeroporto,
          mala, reserva, férias
Patterns: "vamos para", "passagens para", "hotel em"
```

#### saude
```
Keywords: médico, consulta, exame, remédio, farmácia,
          dentista, dor, doente, vacina
Patterns: "marcar médico", "tomar remédio", "consulta dia"
```

#### financas
```
Keywords: dinheiro, investimento, conta, banco, cartão,
          fatura, parcela, empréstimo, poupança
Patterns: "quanto custa", "transferir", "pagar fatura"
```

#### lazer
```
Keywords: jantar, restaurante, cinema, show, festa,
          amigos, churrasco, pizza, série, filme
Patterns: "vamos ao", "reservar mesa", "convite para"
```

#### relacionamento (nos)
```
Keywords: te amo, saudade, nós, juntos, aniversário de casamento,
          obrigado/a, melhor, incrível, parceiro/a
Patterns: "❤️", "😘", "você é", "nós dois"
Sentiment: Positive + affection markers
```

### Sentiment Analysis Keywords

#### Positive Indicators
```
Strong: te amo, incrível, maravilhoso, perfeito, melhor, ❤️, 😍
Moderate: obrigado/a, legal, ótimo, bom, 👍, 😊
Mild: ok, pode ser, tá bom
```

#### Negative Indicators
```
Strong: não acredito, absurdo, péssimo, horrível, 😤, 😡
Moderate: chateado/a, frustrado/a, cansado/a, difícil
Mild: não sei, talvez, hmm
```

#### Stress Indicators
```
Explicit: estressado/a, não aguento, muito trabalho, deadline
Implicit: respostas curtas, menos emojis, demora para responder
Contextual: menção a Lia + urgência, múltiplas tarefas
```

---

## Scoring Calculation Formulas

### Overall Health Score

```
healthScore = (
  responseSymmetry × 0.20 +
  topicDiversity × 0.15 +
  sentimentTrend × 0.25 +
  affectionFrequency × 0.20 +
  conversationFrequency × 0.20
)
```

### Component Calculations

#### Response Symmetry (1-10)
```
ratio = min(responsesByA, responsesByB) / max(responsesByA, responsesByB)
score = ratio × 10
Example: 85 responses by A, 100 by B → 85/100 = 0.85 → 8.5
```

#### Topic Diversity (1-10)
```
activeTopics = count of topics with messages in last 30 days
score = (activeTopics / 8) × 10
Example: 8/8 topics active → 10.0
```

#### Sentiment Trend (1-10)
```
currentSentiment = average sentiment score last 7 days
previousSentiment = average sentiment score 8-14 days ago
change = (currentSentiment - previousSentiment) / previousSentiment
score = 5 + (change × 50)  // capped at 1-10
Example: +10% improvement → 5 + 5 = 10 (capped)
```

#### Affection Frequency (1-10)
```
affectionMessages = count of messages with affection markers per week
baseline = 10 messages per week (configurable)
score = min(10, (affectionMessages / baseline) × 10)
Example: 12 per week → 12/10 × 10 = 10 (capped)
```

#### Conversation Frequency (1-10)
```
dailyAverage = total messages / days in period
baseline = 50 messages per day (configurable)
score = min(10, (dailyAverage / baseline) × 10)
Example: 47 per day → 47/50 × 10 = 9.4
```

### Balance Score

```
balanceScore = 100 - |percentage_A - 50| × 2
Example: 60/40 split → 100 - |60-50| × 2 = 80
```

---

## Configuration

### Processing Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `historyDepth` | all | Use all available history for pattern detection |
| `recentWindow` | 30 days | Period for "recent" examples in agent context |
| `healthScoreWindow` | 7 days | Period for health score calculation |
| `weeklyStatsWindow` | 7 days | Period for weekly statistics |
| `minMessagesForPattern` | 10 | Minimum occurrences to identify a pattern |

### Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| Task imbalance | >65% one person | >80% one person |
| Response time gap | >2x difference | >5x difference |
| Days since connection | >7 days | >14 days |
| Pending decisions | >5 days | >10 days |

### Output Files

| Output | Format | Location |
|--------|--------|----------|
| Message Groups | JSON | `/api/messages/grouped` |
| Tasks | JSON | `/api/tasks` |
| Health Score | JSON | `/api/health` |
| Balance Metrics | JSON | `/api/balance` |
| Weekly Stats | JSON | `/api/stats/weekly` |
| Agent Context (Thiago) | JSON | `/api/agent/thiago/context` |
| Agent Context (Daniela) | JSON | `/api/agent/daniela/context` |
| Community Context | JSON | `/api/agent/community/context` |

---

## Validation Checklist

- [ ] All JSON schemas are valid and parseable
- [ ] Status detection rules cover all common patterns
- [ ] Scoring formulas produce values in expected ranges (1-10)
- [ ] Agent contexts include actionable, specific insights
- [ ] Keywords cover Portuguese variations and common typos
- [ ] Examples reflect realistic conversation patterns
- [ ] All spaces/topics have complete keyword lists
- [ ] Balance metrics correctly identify concerning patterns

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2024-01-20 | Initial specification |
