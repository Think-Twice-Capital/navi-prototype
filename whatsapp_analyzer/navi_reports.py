"""
NAVI Report Generator

Generates human-readable markdown reports from NAVI JSON outputs.

Updated to support the new scientific health score framework based on:
- Gottman's research for conflict detection
- Interpersonal Process Model for connection quality
- Maintenance Behaviors for partnership equity
"""

import json
from datetime import datetime
from typing import Dict, List, Optional


class NAVIReportGenerator:
    """Generates markdown reports from NAVI JSON outputs."""

    # Score interpretation for new 1-100 scale
    SCORE_LABELS = {
        (85, 100): ('Florescente', 'Flourishing', 'Saúde excepcional do relacionamento'),
        (70, 84): ('Saudável', 'Healthy', 'Base sólida com áreas menores para nutrir'),
        (55, 69): ('Estável', 'Stable', 'Funcionando mas poderia melhorar'),
        (40, 54): ('Atenção', 'Attention', 'Padrões notáveis precisam de atenção'),
        (25, 39): ('Preocupante', 'Concerning', 'Questões significativas presentes'),
        (0, 24): ('Crítico', 'Critical', 'Intervenção urgente recomendada'),
    }

    def __init__(self, outputs: Dict):
        """
        Initialize with NAVI outputs.

        Args:
            outputs: Dictionary from NAVIOutputGenerator.generate_all_outputs()
        """
        self.outputs = outputs

    @classmethod
    def from_files(cls, output_dir: str) -> 'NAVIReportGenerator':
        """
        Load outputs from files.

        Args:
            output_dir: Directory containing NAVI JSON outputs

        Returns:
            NAVIReportGenerator instance
        """
        import os

        with open(os.path.join(output_dir, 'all_outputs.json'), 'r') as f:
            outputs = json.load(f)

        return cls(outputs)

    def generate_health_report(self) -> str:
        """Generate scientific health score report with 4-dimension framework."""
        scoring = self.outputs.get('scoring', {})
        health = scoring.get('healthScore', {})
        pattern_analysis = scoring.get('patternAnalysis', {})
        balance = scoring.get('balance', {})
        weekly = scoring.get('weeklyStats', {})

        overall = health.get('overall', 'N/A')
        label = health.get('label', 'N/A')
        label_en = health.get('labelEn', 'N/A')
        confidence = health.get('confidence', 0)
        trend = health.get('trend', 'N/A')

        report = f"""# NAVI Scientific Health Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## Overall Health Score

| Metric | Value |
|--------|-------|
| **Score** | **{overall}/100** |
| **Status (PT)** | **{label}** |
| **Status (EN)** | **{label_en}** |
| **Confidence** | **{confidence*100:.0f}%** |
| **Trend** | **{trend}** |

### Scientific Framework

This score is based on validated academic research:
- **Gottman's Research** - Four Horsemen, 5:1 positive ratio
- **Interpersonal Process Model** - Partner responsiveness (Reis & Shaver)
- **Maintenance Behaviors** - Partnership equity (Stafford & Canary)

### Score Interpretation

| Range | PT | EN | Meaning |
|-------|----|----|---------|
| 85-100 | Florescente | Flourishing | Exceptional relationship health |
| 70-84 | Saudável | Healthy | Strong foundation, minor areas to nurture |
| 55-69 | Estável | Stable | Functioning but could improve |
| 40-54 | Atenção | Attention | Noticeable patterns need addressing |
| 25-39 | Preocupante | Concerning | Significant issues present |
| 0-24 | Crítico | Critical | Urgent intervention recommended |

---

## 4-Dimension Analysis

"""
        dimensions = health.get('dimensions', {})

        # Dimension 1: Connection Quality
        conn = dimensions.get('connectionQuality', {})
        conn_score = conn.get('score', 'N/A')
        conn_components = conn.get('components', {})

        report += f"""### 1. Connection Quality: {conn_score}/100 (Weight: 30%)

*Based on: Interpersonal Process Model (Reis & Shaver)*

| Component | Score | Insight |
|-----------|-------|---------|
| Responsiveness | {conn_components.get('responsiveness', {}).get('score', 'N/A')} | {conn_components.get('responsiveness', {}).get('insight', 'N/A')} |
| Emotional Expression | {conn_components.get('emotionalExpression', {}).get('score', 'N/A')} | {conn_components.get('emotionalExpression', {}).get('insight', 'N/A')} |
| Reciprocity | {conn_components.get('reciprocity', {}).get('score', 'N/A')} | {conn_components.get('reciprocity', {}).get('insight', 'N/A')} |

"""

        # Dimension 2: Relationship Maintenance
        maint = dimensions.get('relationshipMaintenance', {})
        maint_score = maint.get('score', 'N/A')
        maint_components = maint.get('components', {})

        positivity = maint_components.get('positivity', {})
        report += f"""### 2. Relationship Maintenance: {maint_score}/100 (Weight: 25%)

*Based on: Stafford & Canary Maintenance Behaviors*

| Component | Score | Detail |
|-----------|-------|--------|
| Positivity | {positivity.get('score', 'N/A')} | Ratio: {positivity.get('ratio', 'N/A')} (Gottman goal: 5:1) |
| Assurances | {maint_components.get('assurances', {}).get('score', 'N/A')} | {maint_components.get('assurances', {}).get('perWeek', 'N/A')}/week |
| Task Sharing | {maint_components.get('taskSharing', {}).get('score', 'N/A')} | Balance: {maint_components.get('taskSharing', {}).get('balance', 'N/A')} |
| Understanding | {maint_components.get('understanding', {}).get('score', 'N/A')} | {maint_components.get('understanding', {}).get('insight', 'N/A')} |

"""

        # Dimension 3: Communication Health
        comm = dimensions.get('communicationHealth', {})
        comm_score = comm.get('score', 'N/A')
        comm_components = comm.get('components', {})

        report += f"""### 3. Communication Health: {comm_score}/100 (Weight: 25%)

*Based on: Gottman's Four Horsemen (inverse)*

| Component | Score | Detail |
|-----------|-------|--------|
| Gentle Startup | {comm_components.get('gentleStartup', {}).get('score', 'N/A')} | Criticism count: {comm_components.get('gentleStartup', {}).get('criticismCount', 0)} |
| Repair Attempts | {comm_components.get('repairAttempts', {}).get('score', 'N/A')} | Success rate: {comm_components.get('repairAttempts', {}).get('successRate', 'N/A')} |
| Absence of Contempt | {comm_components.get('absenceOfContempt', {}).get('score', 'N/A')} | {comm_components.get('absenceOfContempt', {}).get('insight', 'N/A')} |
| Engagement | {comm_components.get('engagement', {}).get('score', 'N/A')} | Avg response: {comm_components.get('engagement', {}).get('avgResponseMin', 'N/A')}min |

"""

        # Dimension 4: Partnership Dynamics
        partner = dimensions.get('partnershipDynamics', {})
        partner_score = partner.get('score', 'N/A')
        partner_components = partner.get('components', {})

        report += f"""### 4. Partnership Dynamics: {partner_score}/100 (Weight: 20%)

*Based on: Equity Theory, Interdependence*

| Component | Score | Detail |
|-----------|-------|--------|
| Equity | {partner_components.get('equity', {}).get('score', 'N/A')} | Message balance: {partner_components.get('equity', {}).get('messageBalance', 'N/A')} |
| Coordination | {partner_components.get('coordination', {}).get('score', 'N/A')} | Task completion: {partner_components.get('coordination', {}).get('completionRate', 'N/A')} |
| Shared Meaning | {partner_components.get('sharedMeaning', {}).get('score', 'N/A')} | Future planning: {partner_components.get('sharedMeaning', {}).get('perWeek', 'N/A')}/week |

---

## Gottman Pattern Analysis

"""
        # Four Horsemen
        four_horsemen = pattern_analysis.get('fourHorsemen', {})
        report += f"""### Four Horsemen Detection

*The Four Horsemen predict relationship dissolution with >90% accuracy*

| Horseman | Count | Antidote |
|----------|-------|----------|
| Criticism | {four_horsemen.get('criticism', 0)} | Gentle Startup: "Eu sinto..." |
| Contempt | {four_horsemen.get('contempt', 0)} | Build Appreciation Culture |
| Defensiveness | {four_horsemen.get('defensiveness', 0)} | Take Responsibility |
| Stonewalling | {four_horsemen.get('stonewalling', 0)} | Self-Soothing (20min break) |

### Positive/Negative Ratio

| Metric | Value | Target |
|--------|-------|--------|
| Current Ratio | {pattern_analysis.get('positiveNegativeRatio', 'N/A')}:1 | 5:1 (Gottman) |
| Ratio Met | {'Yes' if pattern_analysis.get('gottmanRatioMet', False) else 'No'} | - |
| Total Positive | {pattern_analysis.get('totalPositive', 'N/A')} | - |
| Total Negative | {pattern_analysis.get('totalNegative', 'N/A')} | - |

---

## Insights & Recommendations

"""
        insights = health.get('insights', {})

        # Strengths
        strengths = insights.get('strengths', [])
        if strengths:
            report += "### Strengths\n\n"
            for s in strengths:
                report += f"""**{s.get('dimension', 'N/A').replace('Quality', ' Quality').replace('Maintenance', ' Maintenance')}**
- {s.get('finding', 'N/A')}
- Evidence: {s.get('evidence', 'N/A')}

"""

        # Opportunities
        opportunities = insights.get('opportunities', [])
        if opportunities:
            report += "### Growth Opportunities\n\n"
            for o in opportunities:
                report += f"""**{o.get('dimension', 'N/A').replace('Quality', ' Quality').replace('Maintenance', ' Maintenance')}**
- Finding: {o.get('finding', 'N/A')}
- Suggestion: {o.get('suggestion', 'N/A')}
- Impact: {o.get('impact', 'N/A')}

"""

        # Alerts
        alerts = health.get('alerts', [])
        if alerts:
            report += "### Alerts\n\n"
            for a in alerts:
                report += f"""**{a.get('pattern', 'N/A').title()}**
- Frequency: {a.get('frequency', 'N/A')}
- Context: {a.get('context', 'N/A')}
- Antidote: {a.get('antidote', 'N/A')}

"""

        report += """---

## Balance Metrics

"""
        # Task Distribution
        td = balance.get('taskDistribution', {})
        report += f"""### Task Distribution

| Person | Percentage | Trend |
|--------|------------|-------|
| Thiago | {td.get('thiago', 'N/A')}% | {td.get('trend', 'N/A')} |
| Daniela | {td.get('daniela', 'N/A')}% | |

"""

        # Conversation Initiation
        ci = balance.get('conversationInitiation', {})
        report += f"""### Conversation Initiation

| Person | Percentage |
|--------|------------|
| Thiago | {ci.get('thiago', 'N/A')}% |
| Daniela | {ci.get('daniela', 'N/A')}% |

"""

        # Response Time
        rt = balance.get('responseTime', {})
        report += f"""### Response Time

| Person | Average |
|--------|---------|
| Thiago | {rt.get('thiago', {}).get('avg', 'N/A')} |
| Daniela | {rt.get('daniela', {}).get('avg', 'N/A')} |

---

## Weekly Statistics

"""
        period = weekly.get('period', {})
        report += f"""**Period:** {period.get('start', 'N/A')[:10] if period.get('start') else 'N/A'} to {period.get('end', 'N/A')[:10] if period.get('end') else 'N/A'}

| Metric | Value |
|--------|-------|
| Messages Exchanged | {weekly.get('messagesExchanged', 'N/A'):,} |
| Tasks Completed | {weekly.get('tasksCompleted', 'N/A')} |
| Connection Moments | {weekly.get('connectionMoments', 'N/A')} |
| Most Active Topic | {weekly.get('mostActiveTopic', 'N/A')} |
| Stress Events | {weekly.get('stressEvents', 'N/A')} |
| Celebration Moments | {weekly.get('celebrationMoments', 'N/A')} |

---

## References

1. Gottman, J. M. (1994). *What Predicts Divorce?*
2. Reis, H. T., & Shaver, P. (1988). *Intimacy as an interpersonal process*
3. Stafford, L., & Canary, D. J. (1991). *Maintenance strategies and romantic relationship type*
4. Funk, J. L., & Rogge, R. D. (2007). *Testing the ruler with item response theory (CSI)*
5. Spanier, G. B. (1976). *Measuring dyadic adjustment (DAS)*

---

*Report generated by NAVI WhatsApp Analyzer - Scientific Framework v2.0*
"""
        return report

    def generate_messages_report(self) -> str:
        """Generate message groups report."""
        messages_data = self.outputs.get('messages', {})
        groups = messages_data.get('messageGroups', [])
        tasks = messages_data.get('tasks', [])
        period = messages_data.get('period', {})

        report = f"""# NAVI Messages Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Period:** {period.get('start', 'N/A')[:10] if period.get('start') else 'N/A'} to {period.get('end', 'N/A')[:10] if period.get('end') else 'N/A'}
**Days Analyzed:** {period.get('days', 'N/A')}

---

## Summary

| Metric | Count |
|--------|-------|
| Total Message Groups | {len(groups):,} |
| Total Tasks Extracted | {len(tasks):,} |

---

## Message Groups by Space

"""
        # Count by space
        space_counts = {}
        for g in groups:
            space = g.get('space', 'outros')
            space_counts[space] = space_counts.get(space, 0) + 1

        report += "| Space | Count | Percentage |\n"
        report += "|-------|-------|------------|\n"
        total = len(groups)
        for space, count in sorted(space_counts.items(), key=lambda x: -x[1]):
            pct = (count / total * 100) if total > 0 else 0
            report += f"| {space} | {count:,} | {pct:.1f}% |\n"

        report += """
---

## Message Groups by Status

"""
        # Count by status
        status_counts = {}
        for g in groups:
            status = g.get('status', 'pending')
            status_counts[status] = status_counts.get(status, 0) + 1

        report += "| Status | Label | Count |\n"
        report += "|--------|-------|-------|\n"
        status_labels = {
            'pending': '⏳ Pendente',
            'done': '✅ Feito',
            'urgent': '🔴 Urgente',
            'scheduled': '📅 Agendado',
            'connection': '💕 Conexão',
        }
        for status, count in sorted(status_counts.items(), key=lambda x: -x[1]):
            label = status_labels.get(status, status)
            report += f"| {status} | {label} | {count:,} |\n"

        report += """
---

## Tasks Overview

"""
        # Tasks by status
        task_status = {}
        for t in tasks:
            status = t.get('status', 'pending')
            task_status[status] = task_status.get(status, 0) + 1

        report += "### Tasks by Status\n\n"
        report += "| Status | Count |\n"
        report += "|--------|-------|\n"
        for status, count in sorted(task_status.items(), key=lambda x: -x[1]):
            report += f"| {status} | {count:,} |\n"

        # Tasks by space
        task_space = {}
        for t in tasks:
            space = t.get('space', 'outros')
            task_space[space] = task_space.get(space, 0) + 1

        report += "\n### Tasks by Space\n\n"
        report += "| Space | Count |\n"
        report += "|-------|-------|\n"
        for space, count in sorted(task_space.items(), key=lambda x: -x[1]):
            report += f"| {space} | {count:,} |\n"

        # Recent urgent tasks
        urgent_tasks = [t for t in tasks if t.get('status') == 'urgent']
        if urgent_tasks:
            report += "\n### Urgent Tasks\n\n"
            for task in urgent_tasks[:10]:
                title = task.get('title', 'N/A')[:60]
                space = task.get('space', 'N/A')
                due = task.get('due', 'N/A')
                report += f"- **[{space}]** {title}\n"
                if due:
                    report += f"  - Due: {due}\n"

        # Pending tasks (sample)
        pending_tasks = [t for t in tasks if t.get('status') == 'pending']
        if pending_tasks:
            report += "\n### Recent Pending Tasks (sample)\n\n"
            for task in pending_tasks[-10:]:
                title = task.get('title', 'N/A')[:60]
                space = task.get('space', 'N/A')
                report += f"- **[{space}]** {title}\n"

        report += """
---

## Recent Message Groups (sample)

"""
        # Show last 5 groups
        for group in groups[-5:]:
            space = group.get('space', 'outros')
            status = group.get('statusLabel', 'N/A')
            summary = group.get('summary', 'N/A')[:80]
            has_action = "Yes" if group.get('hasAction') else "No"

            report += f"### {status} | {space}\n\n"
            report += f"**Summary:** {summary}\n"
            report += f"**Has Action:** {has_action}\n\n"

            messages = group.get('messages', [])[:5]
            if messages:
                report += "**Messages:**\n"
                for msg in messages:
                    time = msg.get('time', '')
                    sender = msg.get('sender', '')
                    text = msg.get('text', '')[:60]
                    report += f"- `{time}` **{sender}:** {text}...\n"
            report += "\n---\n\n"

        report += "*Report generated by NAVI WhatsApp Analyzer*\n"
        return report

    def generate_agent_report(self, user: str) -> str:
        """
        Generate agent context report.

        Args:
            user: 'thiago', 'daniela', or 'community'
        """
        contexts = self.outputs.get('agentContexts', {})

        if user == 'community':
            return self._generate_community_report(contexts.get('community', {}))
        else:
            context_data = contexts.get(user, {})
            return self._generate_individual_report(user, context_data)

    def _generate_individual_report(self, user: str, context_data: Dict) -> str:
        """Generate individual agent report."""
        ctx = context_data.get('agentContext', {})
        user_display = user.title()
        partner = ctx.get('partner', 'parceiro').title()

        report = f"""# NAVI Agent Context Report: {user_display}

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Last Updated:** {ctx.get('lastUpdated', 'N/A')[:10] if ctx.get('lastUpdated') else 'N/A'}

---

## Profile

| Attribute | Value |
|-----------|-------|
| User | {user_display} |
| Partner | {partner} |

---

## Communication Patterns

"""
        patterns = ctx.get('communicationPatterns', {})
        report += f"""| Pattern | Value |
|---------|-------|
| Response Style | {patterns.get('responseStyle', 'N/A')} |
| Avg Response Length | {patterns.get('avgResponseLength', 'N/A')} words |

### Typical Responses

"""
        for resp in patterns.get('typicalResponses', patterns.get('typicalPatterns', []))[:5]:
            report += f"- \"{resp}\"\n"

        report += "\n### Response Time by Context\n\n"
        report += "| Context | Time |\n"
        report += "|---------|------|\n"
        for context, time in patterns.get('responseTimeByContext', {}).items():
            report += f"| {context.title()} | {time} |\n"

        report += """
---

## Strengths

"""
        for strength in ctx.get('strengths', []):
            pattern = strength.get('pattern', 'N/A')
            desc = strength.get('description', 'N/A')
            evidence = strength.get('evidence', 'N/A')
            freq = strength.get('frequency', 'N/A')

            report += f"""### {pattern.replace('_', ' ').title()}

- **Description:** {desc}
- **Evidence:** {evidence}
- **Frequency:** {freq}

"""

        report += """---

## Areas for Growth

"""
        for area in ctx.get('areasForGrowth', []):
            pattern = area.get('pattern', 'N/A')
            desc = area.get('description', 'N/A')
            freq = area.get('frequency', 'N/A')
            suggestion = area.get('suggestion', 'N/A')
            impact = area.get('impact', 'N/A')

            report += f"""### {pattern.replace('_', ' ').title()}

- **Description:** {desc}
- **Frequency:** {freq}
- **Suggestion:** {suggestion}
- **Impact:** {impact}

"""

        report += """---

## Topic Expertise

"""
        expertise = ctx.get('topicExpertise', {})

        report += "### Primary Topics (leads)\n\n"
        for topic in expertise.get('primary', []):
            report += f"- {topic}\n"

        report += "\n### Secondary Topics (supports)\n\n"
        for topic in expertise.get('secondary', []):
            report += f"- {topic}\n"

        report += "\n### Partner Leads\n\n"
        for topic in expertise.get('partner_leads', []):
            report += f"- {topic}\n"

        # Stress indicators if present
        stress = ctx.get('stressIndicators', {})
        if stress:
            report += """
---

## Stress Indicators

### Triggers

"""
            for trigger in stress.get('triggers', []):
                report += f"- {trigger}\n"

            report += "\n### Signals\n\n"
            for signal in stress.get('signals', []):
                report += f"- {signal}\n"

            report += f"\n**Support Preference:** {stress.get('supportPreference', 'N/A')}\n"

        report += """
---

*Report generated by NAVI WhatsApp Analyzer*
"""
        return report

    def _generate_community_report(self, context_data: Dict) -> str:
        """Generate community manager report with scientific insights."""
        ctx = context_data.get('communityContext', {})

        report = f"""# NAVI Community Manager Report

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}
**Last Updated:** {ctx.get('lastUpdated', 'N/A')[:10] if ctx.get('lastUpdated') else 'N/A'}

---

## Couple Profile

**Members:** {', '.join(ctx.get('couple', []))}

---

## Relationship Dynamics (Scientific Framework)

"""
        dynamics = ctx.get('relationshipDynamics', {})
        report += f"""| Metric | Value |
|--------|-------|
| Overall Health | {dynamics.get('overallHealth', 'N/A')}/100 |
| Health Label | {dynamics.get('healthLabel', 'N/A')} |
| Health Trend | {dynamics.get('healthTrend', 'N/A')} |
| Confidence | {dynamics.get('confidence', 0)*100:.0f}% |

### Strength Areas

"""
        for area in dynamics.get('strengthAreas', []):
            report += f"- {area.replace('_', ' ').title()}\n"

        report += "\n### Growth Areas\n\n"
        for area in dynamics.get('growthAreas', []):
            report += f"- {area.replace('_', ' ').title()}\n"

        # Scientific Insights
        scientific_insights = ctx.get('scientificInsights', {})
        if scientific_insights:
            report += "\n---\n\n## Scientific Insights\n\n"

            strengths = scientific_insights.get('strengths', [])
            if strengths:
                report += "### Research-Backed Strengths\n\n"
                for s in strengths:
                    report += f"""**{s.get('dimension', 'N/A')}**
- {s.get('finding', 'N/A')}
- Evidence: {s.get('evidence', 'N/A')}

"""

            opportunities = scientific_insights.get('opportunities', [])
            if opportunities:
                report += "### Research-Backed Opportunities\n\n"
                for o in opportunities:
                    report += f"""**{o.get('dimension', 'N/A')}**
- Finding: {o.get('finding', 'N/A')}
- Suggestion: {o.get('suggestion', 'N/A')}
- Impact: {o.get('impact', 'N/A')}

"""

        # Alerts
        alerts = ctx.get('alerts', [])
        if alerts:
            report += "---\n\n## Gottman Alerts\n\n"
            for alert in alerts:
                report += f"""### {alert.get('pattern', 'N/A').title()}

- **Frequency:** {alert.get('frequency', 'N/A')}
- **Context:** {alert.get('context', 'N/A')}
- **Antidote:** {alert.get('antidote', 'N/A')}

"""

        report += """---

## Success Patterns

"""
        for pattern in ctx.get('successPatterns', []):
            name = pattern.get('pattern', 'N/A').replace('_', ' ').title()
            desc = pattern.get('description', 'N/A')
            freq = pattern.get('frequency', 'N/A')

            report += f"""### {name}

- **Description:** {desc}
- **Frequency:** {freq}

"""
            example = pattern.get('recentExample', {})
            if example:
                report += f"""**Recent Example:**
- Date: {example.get('date', 'N/A')}
- Trigger: {example.get('trigger', 'N/A')}
- Response: {example.get('response', 'N/A')}
- Outcome: {example.get('outcome', 'N/A')}

"""

        report += """---

## Attention Areas

"""
        for area in ctx.get('attentionAreas', []):
            name = area.get('area', 'N/A').replace('_', ' ').title()
            obs = area.get('observation', 'N/A')
            sug = area.get('suggestion', 'N/A')
            priority = area.get('priority', 'N/A')
            research_based = area.get('researchBased', False)

            report += f"""### {name}

- **Observation:** {obs}
- **Suggestion:** {sug}
- **Priority:** {priority}
"""
            if research_based:
                report += "- **Source:** Research-based (Gottman/Reis & Shaver)\n"
            if area.get('antidote'):
                report += f"- **Antidote:** {area.get('antidote')}\n"
            report += "\n"

        if not ctx.get('attentionAreas'):
            report += "*No attention areas identified at this time.*\n\n"

        report += """---

## Celebration Moments

"""
        for moment in ctx.get('celebrationMoments', []):
            date = moment.get('date', 'N/A')
            title = moment.get('title', 'N/A')
            significance = moment.get('significance', 'N/A')

            report += f"""### {title}

- **Date:** {date}
- **Significance:** {significance}

"""
            quotes = moment.get('quotes', [])
            if quotes:
                report += "**Quotes:**\n"
                for quote in quotes:
                    report += f"> \"{quote[:100]}...\"\n\n"

        report += """---

## Suggested Activities (Research-Backed)

"""
        for activity in ctx.get('suggestedActivities', []):
            act_type = activity.get('type', 'N/A').replace('_', ' ').title()
            suggestion = activity.get('suggestion', 'N/A')
            rationale = activity.get('rationale', 'N/A')
            timing = activity.get('timing', 'N/A')
            priority = activity.get('priority', 'N/A')

            report += f"""### {act_type}

- **Suggestion:** {suggestion}
- **Rationale:** {rationale}
- **Timing:** {timing}
- **Priority:** {priority}

"""

        # Methodology
        methodology = ctx.get('methodology', {})
        if methodology:
            report += f"""---

## Methodology

- **Framework:** {methodology.get('framework', 'N/A')}
- **Scale:** {methodology.get('scale', 'N/A')}
- **References:** {', '.join(methodology.get('references', []))}

"""

        report += """---

*Report generated by NAVI WhatsApp Analyzer - Scientific Framework v2.0*
"""
        return report

    def generate_all_reports(self) -> Dict[str, str]:
        """
        Generate all reports.

        Returns:
            Dictionary mapping report names to content
        """
        return {
            'health_report.md': self.generate_health_report(),
            'messages_report.md': self.generate_messages_report(),
            'agent_thiago_report.md': self.generate_agent_report('thiago'),
            'agent_daniela_report.md': self.generate_agent_report('daniela'),
            'agent_community_report.md': self.generate_agent_report('community'),
        }

    def save_reports(self, output_dir: str) -> Dict[str, str]:
        """
        Generate and save all reports.

        Args:
            output_dir: Directory to save reports

        Returns:
            Dictionary mapping report names to file paths
        """
        import os
        os.makedirs(output_dir, exist_ok=True)

        reports = self.generate_all_reports()
        paths = {}

        for filename, content in reports.items():
            filepath = os.path.join(output_dir, filename)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            paths[filename] = filepath

        return paths
