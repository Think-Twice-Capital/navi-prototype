"""Visualization Module for WhatsApp Chat Analysis"""

import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import seaborn as sns
from wordcloud import WordCloud
from typing import Dict, List, Optional
from datetime import datetime

from .utils import clean_text, day_name_pt, count_words, count_emojis


class ChatVisualizer:
    """Generate visualizations for WhatsApp chat analysis."""

    # Color scheme
    COLORS = {
        'Thiago Alvarez': '#3498db',  # Blue
        'Daniela Anderez': '#e74c3c',  # Red
        'primary': '#3498db',
        'secondary': '#e74c3c',
        'neutral': '#95a5a6',
        'positive': '#27ae60',
        'negative': '#c0392b',
    }

    def __init__(self, df: pd.DataFrame, output_dir: str):
        """Initialize visualizer."""
        self.df = df
        self.output_dir = output_dir
        self.participants = df['sender'].unique().tolist()

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Set style
        plt.style.use('seaborn-v0_8-whitegrid')
        plt.rcParams['figure.figsize'] = (12, 6)
        plt.rcParams['font.size'] = 10
        plt.rcParams['axes.titlesize'] = 14
        plt.rcParams['axes.labelsize'] = 12

    def _get_sender_color(self, sender: str) -> str:
        """Get color for a sender."""
        return self.COLORS.get(sender, self.COLORS['neutral'])

    def _save_fig(self, name: str, dpi: int = 150):
        """Save figure to output directory."""
        filepath = os.path.join(self.output_dir, f"{name}.png")
        plt.savefig(filepath, dpi=dpi, bbox_inches='tight', facecolor='white')
        plt.close()
        print(f"Saved: {filepath}")
        return filepath

    def generate_all(self, analyzer, sentiment_analyzer=None,
                     topic_analyzer=None, conflict_detector=None) -> Dict[str, str]:
        """Generate all visualizations."""
        paths = {}

        # 1. Messages per month
        paths['01_messages_per_month'] = self.plot_messages_per_month()

        # 2. Messages by year per person
        paths['02_messages_by_year'] = self.plot_messages_by_year()

        # 3. Activity heatmap
        paths['03_activity_heatmap'] = self.plot_activity_heatmap()

        # 4. Message frequency per person
        paths['04_frequency_per_person'] = self.plot_frequency_per_person()

        # 5. Messages by day of week
        paths['05_by_day_of_week'] = self.plot_by_day_of_week()

        # 6. Messages by hour
        paths['06_by_hour'] = self.plot_by_hour()

        # 7. Message length distribution
        paths['07_message_length_dist'] = self.plot_message_length_distribution()

        # 8. Message length evolution
        paths['08_message_length_evolution'] = self.plot_message_length_evolution()

        # 9-11. Word clouds
        paths['09_wordcloud_combined'] = self.plot_wordcloud_combined()
        for i, sender in enumerate(self.participants[:2]):
            paths[f'{10+i}_wordcloud_{sender.split()[0].lower()}'] = self.plot_wordcloud_sender(sender)

        # 12. Top 20 words
        paths['12_top_words'] = self.plot_top_words(analyzer)

        # 13. Top emojis
        paths['13_top_emojis'] = self.plot_top_emojis(analyzer)

        # 14. Media type distribution
        paths['14_media_distribution'] = self.plot_media_distribution(analyzer)

        # 15. Media sharing trends
        paths['15_media_trends'] = self.plot_media_trends()

        # 16. Terms of endearment
        paths['16_terms_of_endearment'] = self.plot_terms_of_endearment(analyzer)

        # 17. Sentiment over time
        if sentiment_analyzer:
            paths['17_sentiment_over_time'] = self.plot_sentiment_over_time()

        # 18. Call duration trends
        paths['18_call_trends'] = self.plot_call_trends()

        # 19. Calendar heatmap
        paths['19_calendar_heatmap'] = self.plot_calendar_heatmap()

        # 20. Response time comparison
        paths['20_response_times'] = self.plot_response_times(analyzer)

        # 21. Messaging streak
        paths['21_streak_history'] = self.plot_streak_history()

        # 22. Conversation initiations
        paths['22_initiations'] = self.plot_conversation_initiations(analyzer)

        # 23. "Te amo" by year
        paths['23_te_amo_by_year'] = self.plot_te_amo_by_year(analyzer)

        # Topic Analysis visualizations (24-26)
        if topic_analyzer and 'primary_topic' in self.df.columns:
            paths['24_topic_distribution_time'] = self.plot_topic_distribution_over_time(topic_analyzer)
            paths['25_topics_by_sender'] = self.plot_topics_by_sender(topic_analyzer)
            paths['26_overall_topic_distribution'] = self.plot_overall_topic_distribution(topic_analyzer)

        # Stress/Conflict Analysis visualizations (27-29)
        if conflict_detector and 'conflict_score' in self.df.columns:
            paths['27_stress_timeline'] = self.plot_stress_timeline(conflict_detector)
            paths['28_stress_causes'] = self.plot_stress_causes(conflict_detector)
            paths['29_stress_topic_heatmap'] = self.plot_stress_topic_heatmap(conflict_detector)

        # NEW: Conversation-Aware Topic Analysis visualizations (30-35)
        if topic_analyzer and 'primary_topic' in self.df.columns:
            paths['30_sentiment_by_topic'] = self.plot_sentiment_by_topic(analyzer)
            paths['31_topic_initiators'] = self.plot_topic_initiators(topic_analyzer)
            paths['32_topic_evolution_yearly'] = self.plot_topic_evolution_yearly(topic_analyzer)
            paths['33_communication_health'] = self.plot_communication_health(analyzer)
            paths['34_conversation_count_by_topic'] = self.plot_conversation_count_by_topic(topic_analyzer)
            paths['35_response_time_by_topic'] = self.plot_response_time_by_topic(analyzer)

        return paths

    def plot_messages_per_month(self) -> str:
        """1. Line chart - Messages per month over time."""
        fig, ax = plt.subplots(figsize=(14, 6))

        monthly = self.df.groupby(self.df['datetime'].dt.to_period('M')).size()
        dates = [period.to_timestamp() for period in monthly.index]

        ax.plot(dates, monthly.values, color=self.COLORS['primary'], linewidth=2)
        ax.fill_between(dates, monthly.values, alpha=0.3, color=self.COLORS['primary'])

        ax.set_title('Mensagens por Mês (2018-2025)', fontsize=16, fontweight='bold')
        ax.set_xlabel('Data')
        ax.set_ylabel('Número de Mensagens')

        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

        plt.tight_layout()
        return self._save_fig('01_messages_per_month')

    def plot_messages_by_year(self) -> str:
        """2. Stacked bar - Messages by year per person."""
        fig, ax = plt.subplots(figsize=(12, 6))

        yearly = self.df.groupby(['year', 'sender']).size().unstack(fill_value=0)
        years = yearly.index.tolist()

        bottom = np.zeros(len(years))
        for sender in self.participants:
            if sender in yearly.columns:
                values = yearly[sender].values
                ax.bar(years, values, bottom=bottom,
                       label=sender, color=self._get_sender_color(sender))
                bottom += values

        ax.set_title('Mensagens por Ano', fontsize=16, fontweight='bold')
        ax.set_xlabel('Ano')
        ax.set_ylabel('Número de Mensagens')
        ax.legend(loc='upper right')

        # Add total labels on top
        totals = yearly.sum(axis=1)
        for i, (year, total) in enumerate(zip(years, totals)):
            ax.annotate(f'{int(total):,}', xy=(year, total), ha='center', va='bottom', fontsize=9)

        plt.tight_layout()
        return self._save_fig('02_messages_by_year')

    def plot_activity_heatmap(self) -> str:
        """3. Heatmap - Hour x Day of week activity."""
        fig, ax = plt.subplots(figsize=(14, 8))

        heatmap_data = self.df.groupby(['day_of_week_num', 'hour']).size().unstack(fill_value=0)

        # Day names in Portuguese
        day_names = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']

        sns.heatmap(heatmap_data, cmap='YlOrRd', ax=ax,
                    xticklabels=[f'{h:02d}:00' for h in range(24)],
                    yticklabels=day_names,
                    cbar_kws={'label': 'Mensagens'})

        ax.set_title('Padrão de Atividade (Hora x Dia da Semana)', fontsize=16, fontweight='bold')
        ax.set_xlabel('Hora do Dia')
        ax.set_ylabel('Dia da Semana')

        plt.tight_layout()
        return self._save_fig('03_activity_heatmap')

    def plot_frequency_per_person(self) -> str:
        """4. Dual line - Message frequency per person over time."""
        fig, ax = plt.subplots(figsize=(14, 6))

        for sender in self.participants:
            sender_df = self.df[self.df['sender'] == sender]
            monthly = sender_df.groupby(sender_df['datetime'].dt.to_period('M')).size()
            dates = [period.to_timestamp() for period in monthly.index]
            ax.plot(dates, monthly.values, label=sender,
                    color=self._get_sender_color(sender), linewidth=2)

        ax.set_title('Frequência de Mensagens por Pessoa', fontsize=16, fontweight='bold')
        ax.set_xlabel('Data')
        ax.set_ylabel('Mensagens por Mês')
        ax.legend(loc='upper right')

        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

        plt.tight_layout()
        return self._save_fig('04_frequency_per_person')

    def plot_by_day_of_week(self) -> str:
        """5. Bar - Messages by day of week."""
        fig, ax = plt.subplots(figsize=(10, 6))

        day_names = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
        by_day = self.df.groupby('day_of_week_num').size()

        colors = [self.COLORS['primary'] if d < 5 else self.COLORS['secondary'] for d in range(7)]
        ax.bar(day_names, [by_day.get(i, 0) for i in range(7)], color=colors)

        ax.set_title('Mensagens por Dia da Semana', fontsize=16, fontweight='bold')
        ax.set_xlabel('Dia da Semana')
        ax.set_ylabel('Total de Mensagens')

        plt.tight_layout()
        return self._save_fig('05_by_day_of_week')

    def plot_by_hour(self) -> str:
        """6. Bar - Messages by hour of day."""
        fig, ax = plt.subplots(figsize=(14, 6))

        by_hour = self.df.groupby('hour').size()

        # Color gradient based on time of day
        colors = []
        for h in range(24):
            if 6 <= h < 12:
                colors.append('#f39c12')  # Morning - orange
            elif 12 <= h < 18:
                colors.append('#e74c3c')  # Afternoon - red
            elif 18 <= h < 22:
                colors.append('#9b59b6')  # Evening - purple
            else:
                colors.append('#34495e')  # Night - dark

        ax.bar(range(24), [by_hour.get(i, 0) for i in range(24)], color=colors)

        ax.set_title('Mensagens por Hora do Dia', fontsize=16, fontweight='bold')
        ax.set_xlabel('Hora')
        ax.set_ylabel('Total de Mensagens')
        ax.set_xticks(range(24))
        ax.set_xticklabels([f'{h:02d}' for h in range(24)])

        plt.tight_layout()
        return self._save_fig('06_by_hour')

    def plot_message_length_distribution(self) -> str:
        """7. Box plot - Message length distribution."""
        fig, ax = plt.subplots(figsize=(10, 6))

        text_msgs = self.df[self.df['type'] == 'text']

        data = []
        labels = []
        colors = []

        for sender in self.participants:
            sender_lengths = text_msgs[text_msgs['sender'] == sender]['message_length']
            if len(sender_lengths) > 0:
                data.append(sender_lengths.values)
                labels.append(sender.split()[0])
                colors.append(self._get_sender_color(sender))

        bp = ax.boxplot(data, labels=labels, patch_artist=True)

        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)

        ax.set_title('Distribuição do Tamanho das Mensagens', fontsize=16, fontweight='bold')
        ax.set_ylabel('Caracteres por Mensagem')
        ax.set_ylim(0, 500)

        plt.tight_layout()
        return self._save_fig('07_message_length_dist')

    def plot_message_length_evolution(self) -> str:
        """8. Line - Message length evolution over time."""
        fig, ax = plt.subplots(figsize=(14, 6))

        text_msgs = self.df[self.df['type'] == 'text'].copy()

        for sender in self.participants:
            sender_df = text_msgs[text_msgs['sender'] == sender]
            monthly = sender_df.groupby(sender_df['datetime'].dt.to_period('M'))['message_length'].mean()
            dates = [period.to_timestamp() for period in monthly.index]
            ax.plot(dates, monthly.values, label=sender.split()[0],
                    color=self._get_sender_color(sender), linewidth=2, alpha=0.8)

        ax.set_title('Evolução do Tamanho Médio das Mensagens', fontsize=16, fontweight='bold')
        ax.set_xlabel('Data')
        ax.set_ylabel('Caracteres Médios por Mensagem')
        ax.legend(loc='upper right')

        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

        plt.tight_layout()
        return self._save_fig('08_message_length_evolution')

    def plot_wordcloud_combined(self) -> str:
        """9. Word cloud - Combined."""
        fig, ax = plt.subplots(figsize=(12, 8))

        text_msgs = self.df[self.df['type'] == 'text']['message'].tolist()
        all_text = ' '.join([clean_text(msg) for msg in text_msgs])

        wordcloud = WordCloud(
            width=1200, height=800,
            background_color='white',
            colormap='viridis',
            max_words=150,
            min_font_size=10
        ).generate(all_text)

        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        ax.set_title('Palavras Mais Frequentes (Ambos)', fontsize=16, fontweight='bold')

        plt.tight_layout()
        return self._save_fig('09_wordcloud_combined')

    def plot_wordcloud_sender(self, sender: str) -> str:
        """10-11. Word cloud - Per sender."""
        fig, ax = plt.subplots(figsize=(12, 8))

        text_msgs = self.df[(self.df['type'] == 'text') & (self.df['sender'] == sender)]['message'].tolist()
        all_text = ' '.join([clean_text(msg) for msg in text_msgs])

        color = self._get_sender_color(sender)

        def color_func(*args, **kwargs):
            return color

        wordcloud = WordCloud(
            width=1200, height=800,
            background_color='white',
            color_func=color_func,
            max_words=150,
            min_font_size=10
        ).generate(all_text)

        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        ax.set_title(f'Palavras Mais Frequentes - {sender.split()[0]}', fontsize=16, fontweight='bold')

        plt.tight_layout()
        return self._save_fig(f'wordcloud_{sender.split()[0].lower()}')

    def plot_top_words(self, analyzer) -> str:
        """12. Bar - Top 20 words."""
        fig, ax = plt.subplots(figsize=(12, 8))

        word_freq = analyzer.get_word_frequency(top_n=20)
        words, counts = zip(*word_freq['overall'])

        y_pos = np.arange(len(words))
        ax.barh(y_pos, counts, color=self.COLORS['primary'])
        ax.set_yticks(y_pos)
        ax.set_yticklabels(words)
        ax.invert_yaxis()

        ax.set_title('Top 20 Palavras Mais Usadas', fontsize=16, fontweight='bold')
        ax.set_xlabel('Frequência')

        plt.tight_layout()
        return self._save_fig('12_top_words')

    def plot_top_emojis(self, analyzer) -> str:
        """13. Bar - Top 15 emojis."""
        fig, ax = plt.subplots(figsize=(12, 8))

        emoji_freq = analyzer.get_emoji_frequency(top_n=15)

        if emoji_freq['overall']:
            emojis, counts = zip(*emoji_freq['overall'])

            y_pos = np.arange(len(emojis))
            ax.barh(y_pos, counts, color=self.COLORS['secondary'])
            ax.set_yticks(y_pos)
            ax.set_yticklabels(emojis, fontsize=20)
            ax.invert_yaxis()

        ax.set_title('Top 15 Emojis Mais Usados', fontsize=16, fontweight='bold')
        ax.set_xlabel('Frequência')

        plt.tight_layout()
        return self._save_fig('13_top_emojis')

    def plot_media_distribution(self, analyzer) -> str:
        """14. Pie - Media type distribution."""
        fig, ax = plt.subplots(figsize=(10, 8))

        media_stats = analyzer.get_media_stats()

        if media_stats['by_type']:
            labels = list(media_stats['by_type'].keys())
            sizes = list(media_stats['by_type'].values())

            # Translate labels
            label_map = {
                'image': 'Imagens',
                'video': 'Vídeos',
                'audio': 'Áudios',
                'document': 'Documentos',
                'sticker': 'Stickers',
                'gif': 'GIFs',
            }
            labels = [label_map.get(l, l) for l in labels]

            colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))

            wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                               colors=colors, startangle=90)

            ax.set_title('Distribuição de Mídia Compartilhada', fontsize=16, fontweight='bold')

        plt.tight_layout()
        return self._save_fig('14_media_distribution')

    def plot_media_trends(self) -> str:
        """15. Line - Media sharing trends over time."""
        fig, ax = plt.subplots(figsize=(14, 6))

        media_types = ['image', 'video', 'audio', 'document']
        media_df = self.df[self.df['type'].isin(media_types)]

        for sender in self.participants:
            sender_df = media_df[media_df['sender'] == sender]
            monthly = sender_df.groupby(sender_df['datetime'].dt.to_period('M')).size()
            if len(monthly) > 0:
                dates = [period.to_timestamp() for period in monthly.index]
                ax.plot(dates, monthly.values, label=sender.split()[0],
                        color=self._get_sender_color(sender), linewidth=2)

        ax.set_title('Tendência de Compartilhamento de Mídia', fontsize=16, fontweight='bold')
        ax.set_xlabel('Data')
        ax.set_ylabel('Mídias por Mês')
        ax.legend(loc='upper right')

        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

        plt.tight_layout()
        return self._save_fig('15_media_trends')

    def plot_terms_of_endearment(self, analyzer) -> str:
        """16. Bar - Terms of endearment frequency."""
        fig, ax = plt.subplots(figsize=(12, 8))

        terms = analyzer.get_terms_of_endearment()

        if terms['overall']:
            sorted_terms = sorted(terms['overall'].items(), key=lambda x: x[1], reverse=True)[:15]
            labels, counts = zip(*sorted_terms)

            y_pos = np.arange(len(labels))
            ax.barh(y_pos, counts, color=self.COLORS['secondary'])
            ax.set_yticks(y_pos)
            ax.set_yticklabels(labels)
            ax.invert_yaxis()

        ax.set_title('Termos Carinhosos Mais Usados', fontsize=16, fontweight='bold')
        ax.set_xlabel('Frequência')

        plt.tight_layout()
        return self._save_fig('16_terms_of_endearment')

    def plot_sentiment_over_time(self) -> str:
        """17. Line - Sentiment over time."""
        fig, ax = plt.subplots(figsize=(14, 6))

        text_df = self.df[self.df['type'] == 'text'].copy()

        if 'sentiment_score' in text_df.columns:
            monthly = text_df.groupby(text_df['datetime'].dt.to_period('M'))['sentiment_score'].mean()
            dates = [period.to_timestamp() for period in monthly.index]

            ax.plot(dates, monthly.values, color=self.COLORS['primary'], linewidth=2)
            ax.axhline(y=0, color='gray', linestyle='--', alpha=0.5)

            # Fill positive/negative areas
            ax.fill_between(dates, monthly.values, 0,
                            where=[v >= 0 for v in monthly.values],
                            color=self.COLORS['positive'], alpha=0.3, label='Positivo')
            ax.fill_between(dates, monthly.values, 0,
                            where=[v < 0 for v in monthly.values],
                            color=self.COLORS['negative'], alpha=0.3, label='Negativo')

        ax.set_title('Sentimento ao Longo do Tempo', fontsize=16, fontweight='bold')
        ax.set_xlabel('Data')
        ax.set_ylabel('Score de Sentimento')
        ax.legend(loc='upper right')

        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

        plt.tight_layout()
        return self._save_fig('17_sentiment_over_time')

    def plot_call_trends(self) -> str:
        """18. Area - Call duration trends."""
        fig, ax = plt.subplots(figsize=(14, 6))

        calls = self.df[self.df['type'].str.contains('call', case=False, na=False)].copy()

        if len(calls) > 0:
            # Fill NaN values with 0 for call duration
            calls['call_duration_seconds'] = calls['call_duration_seconds'].fillna(0)

            monthly = calls.groupby(calls['datetime'].dt.to_period('M')).agg({
                'call_duration_seconds': 'sum'
            })

            if len(monthly) > 0:
                dates = [period.to_timestamp() for period in monthly.index]
                durations_hours = np.array(monthly['call_duration_seconds'].values, dtype=float) / 3600

                ax.fill_between(dates, durations_hours, alpha=0.7, color=self.COLORS['primary'])
                ax.plot(dates, durations_hours, color=self.COLORS['primary'], linewidth=2)

        ax.set_title('Tempo Total de Chamadas por Mês', fontsize=16, fontweight='bold')
        ax.set_xlabel('Data')
        ax.set_ylabel('Horas de Chamada')

        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

        plt.tight_layout()
        return self._save_fig('18_call_trends')

    def plot_calendar_heatmap(self) -> str:
        """19. Calendar heatmap - GitHub style."""
        fig, axes = plt.subplots(3, 3, figsize=(18, 12))
        axes = axes.flatten()

        years = sorted(self.df['year'].unique())

        for idx, year in enumerate(years[-9:]):  # Last 9 years
            if idx >= 9:
                break

            ax = axes[idx]
            year_df = self.df[self.df['year'] == year]
            daily_counts = year_df.groupby('date').size()

            # Create full year calendar
            start = pd.Timestamp(f'{year}-01-01')
            end = pd.Timestamp(f'{year}-12-31')
            all_days = pd.date_range(start, end)

            # Fill missing dates with 0
            full_year = pd.Series(0, index=all_days.date)
            for date, count in daily_counts.items():
                if date in full_year.index:
                    full_year[date] = count

            # Create matrix for heatmap (weeks x days)
            calendar_data = []
            week = []
            for i, (date, count) in enumerate(full_year.items()):
                day_of_week = pd.Timestamp(date).dayofweek
                if day_of_week == 0 and week:
                    while len(week) < 7:
                        week.append(0)
                    calendar_data.append(week)
                    week = []
                week.append(count)

            if week:
                while len(week) < 7:
                    week.append(0)
                calendar_data.append(week)

            calendar_matrix = np.array(calendar_data).T

            sns.heatmap(calendar_matrix, ax=ax, cmap='Greens', cbar=False,
                        xticklabels=False, yticklabels=['S', 'T', 'Q', 'Q', 'S', 'S', 'D'])
            ax.set_title(str(year), fontsize=12, fontweight='bold')

        # Hide unused axes
        for idx in range(len(years[-9:]), 9):
            axes[idx].axis('off')

        fig.suptitle('Atividade Diária (Estilo GitHub)', fontsize=16, fontweight='bold', y=1.02)
        plt.tight_layout()
        return self._save_fig('19_calendar_heatmap')

    def plot_response_times(self, analyzer) -> str:
        """20. Bar - Response time comparison."""
        fig, ax = plt.subplots(figsize=(10, 6))

        response_stats = analyzer.get_response_time_stats()

        if response_stats['by_sender']:
            senders = list(response_stats['by_sender'].keys())
            means = [response_stats['by_sender'][s]['mean'] / 60 for s in senders]  # Convert to minutes
            medians = [response_stats['by_sender'][s]['median'] / 60 for s in senders]

            x = np.arange(len(senders))
            width = 0.35

            bars1 = ax.bar(x - width/2, means, width, label='Média',
                          color=[self._get_sender_color(s) for s in senders], alpha=0.7)
            bars2 = ax.bar(x + width/2, medians, width, label='Mediana',
                          color=[self._get_sender_color(s) for s in senders])

            ax.set_xlabel('Pessoa')
            ax.set_ylabel('Tempo de Resposta (minutos)')
            ax.set_title('Comparação de Tempo de Resposta', fontsize=16, fontweight='bold')
            ax.set_xticks(x)
            ax.set_xticklabels([s.split()[0] for s in senders])
            ax.legend()

        plt.tight_layout()
        return self._save_fig('20_response_times')

    def plot_streak_history(self) -> str:
        """21. Line - Messaging streak history."""
        fig, ax = plt.subplots(figsize=(14, 6))

        daily = self.df.groupby('date').size().reset_index(name='count')
        daily['date'] = pd.to_datetime(daily['date'])

        # Calculate rolling streak
        daily = daily.sort_values('date')
        streaks = []
        current_streak = 0
        prev_date = None

        for _, row in daily.iterrows():
            if prev_date is None or (row['date'] - prev_date).days == 1:
                current_streak += 1
            elif (row['date'] - prev_date).days > 1:
                current_streak = 1
            streaks.append(current_streak)
            prev_date = row['date']

        daily['streak'] = streaks

        ax.plot(daily['date'], daily['streak'], color=self.COLORS['primary'], linewidth=1)
        ax.fill_between(daily['date'], daily['streak'], alpha=0.3, color=self.COLORS['primary'])

        # Mark longest streak
        max_streak_idx = daily['streak'].idxmax()
        max_date = daily.loc[max_streak_idx, 'date']
        max_val = daily.loc[max_streak_idx, 'streak']
        ax.annotate(f'Recorde: {int(max_val)} dias',
                    xy=(max_date, max_val),
                    xytext=(max_date, max_val + 20),
                    ha='center',
                    arrowprops=dict(arrowstyle='->', color='red'),
                    fontsize=10, fontweight='bold', color='red')

        ax.set_title('Histórico de Sequência de Mensagens', fontsize=16, fontweight='bold')
        ax.set_xlabel('Data')
        ax.set_ylabel('Dias Consecutivos')

        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

        plt.tight_layout()
        return self._save_fig('21_streak_history')

    def plot_conversation_initiations(self, analyzer) -> str:
        """22. Pie - Conversation initiations."""
        fig, ax = plt.subplots(figsize=(10, 8))

        initiations = analyzer.get_conversation_initiations()

        if initiations['by_sender']:
            labels = list(initiations['by_sender'].keys())
            sizes = list(initiations['by_sender'].values())
            colors = [self._get_sender_color(s) for s in labels]

            labels = [s.split()[0] for s in labels]

            wedges, texts, autotexts = ax.pie(sizes, labels=labels, autopct='%1.1f%%',
                                               colors=colors, startangle=90,
                                               explode=[0.02] * len(labels))

            for autotext in autotexts:
                autotext.set_fontsize(12)
                autotext.set_fontweight('bold')

        ax.set_title(f'Quem Inicia as Conversas (após {initiations["gap_hours"]}h de intervalo)',
                     fontsize=16, fontweight='bold')

        plt.tight_layout()
        return self._save_fig('22_initiations')

    def plot_te_amo_by_year(self, analyzer) -> str:
        """23. Bar - 'Te amo' frequency by year."""
        fig, ax = plt.subplots(figsize=(12, 6))

        te_amo = analyzer.get_te_amo_by_year()

        if te_amo:
            years = list(te_amo.keys())
            counts = list(te_amo.values())

            colors = [self.COLORS['secondary']] * len(years)

            ax.bar(years, counts, color=colors)

            # Add value labels
            for year, count in zip(years, counts):
                if count > 0:
                    ax.annotate(str(count), xy=(year, count), ha='center', va='bottom', fontsize=10)

        ax.set_title('Frequência de "Te Amo" por Ano', fontsize=16, fontweight='bold')
        ax.set_xlabel('Ano')
        ax.set_ylabel('Vezes Ditas')

        plt.tight_layout()
        return self._save_fig('23_te_amo_by_year')

    # ==================== TOPIC ANALYSIS VISUALIZATIONS ====================

    def plot_topic_distribution_over_time(self, topic_analyzer) -> str:
        """24. Stacked Area - Topic distribution over time."""
        fig, ax = plt.subplots(figsize=(14, 8))

        monthly_topics = topic_analyzer.get_topics_over_time(self.df)

        if len(monthly_topics) == 0:
            ax.text(0.5, 0.5, 'Dados insuficientes', ha='center', va='center')
            plt.tight_layout()
            return self._save_fig('24_topic_distribution_time')

        dates = [period.to_timestamp() for period in monthly_topics['month_period']]

        # Topic columns (excluding month_period)
        topic_cols = [col for col in monthly_topics.columns if col != 'month_period']

        # Create stacked area chart
        topic_colors = {
            'trabalho': '#3498db',
            'casa': '#e67e22',
            'filhos': '#9b59b6',
            'viagem': '#1abc9c',
            'saude': '#e74c3c',
            'financas': '#f1c40f',
            'lazer': '#2ecc71',
            'relacionamento': '#e91e63',
            'outros': '#95a5a6',
        }

        # Stack the areas
        bottom = np.zeros(len(dates))
        for topic in topic_cols:
            if topic in monthly_topics.columns:
                values = monthly_topics[topic].values
                color = topic_colors.get(topic, '#95a5a6')
                ax.fill_between(dates, bottom, bottom + values, label=topic.title(),
                               color=color, alpha=0.7)
                bottom += values

        ax.set_title('Distribuição de Tópicos ao Longo do Tempo', fontsize=16, fontweight='bold')
        ax.set_xlabel('Data')
        ax.set_ylabel('Número de Mensagens')
        ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1), ncol=1)

        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

        plt.tight_layout()
        return self._save_fig('24_topic_distribution_time')

    def plot_topics_by_sender(self, topic_analyzer) -> str:
        """25. Horizontal Bar - Topics by sender."""
        fig, axes = plt.subplots(1, 2, figsize=(14, 8))

        topics_by_sender = topic_analyzer.get_topics_by_sender(self.df)

        topic_colors = {
            'trabalho': '#3498db',
            'casa': '#e67e22',
            'filhos': '#9b59b6',
            'viagem': '#1abc9c',
            'saude': '#e74c3c',
            'financas': '#f1c40f',
            'lazer': '#2ecc71',
            'relacionamento': '#e91e63',
            'outros': '#95a5a6',
        }

        for idx, (sender, topics) in enumerate(topics_by_sender.items()):
            if idx >= 2:
                break
            ax = axes[idx]

            if topics:
                # Sort by value
                sorted_topics = sorted(topics.items(), key=lambda x: x[1], reverse=True)[:8]
                labels, values = zip(*sorted_topics)

                colors = [topic_colors.get(l, '#95a5a6') for l in labels]
                y_pos = np.arange(len(labels))

                ax.barh(y_pos, values, color=colors)
                ax.set_yticks(y_pos)
                ax.set_yticklabels([l.title() for l in labels])
                ax.invert_yaxis()

            ax.set_title(f'{sender.split()[0]}', fontsize=14, fontweight='bold')
            ax.set_xlabel('% das Mensagens')

        fig.suptitle('Distribuição de Tópicos por Pessoa', fontsize=16, fontweight='bold', y=1.02)
        plt.tight_layout()
        return self._save_fig('25_topics_by_sender')

    def plot_overall_topic_distribution(self, topic_analyzer) -> str:
        """26. Pie - Overall topic distribution."""
        fig, ax = plt.subplots(figsize=(10, 8))

        distribution = topic_analyzer.get_overall_topic_distribution(self.df)

        if distribution:
            # Sort and get top topics
            sorted_dist = sorted(distribution.items(), key=lambda x: x[1], reverse=True)
            labels, sizes = zip(*sorted_dist)

            topic_colors = {
                'trabalho': '#3498db',
                'casa': '#e67e22',
                'filhos': '#9b59b6',
                'viagem': '#1abc9c',
                'saude': '#e74c3c',
                'financas': '#f1c40f',
                'lazer': '#2ecc71',
                'relacionamento': '#e91e63',
                'outros': '#95a5a6',
            }

            colors = [topic_colors.get(l, '#95a5a6') for l in labels]
            display_labels = [l.title() for l in labels]

            wedges, texts, autotexts = ax.pie(sizes, labels=display_labels, autopct='%1.1f%%',
                                               colors=colors, startangle=90,
                                               explode=[0.02] * len(labels))

            for autotext in autotexts:
                autotext.set_fontsize(10)
                autotext.set_fontweight('bold')

        ax.set_title('Distribuição Geral de Tópicos', fontsize=16, fontweight='bold')

        plt.tight_layout()
        return self._save_fig('26_overall_topic_distribution')

    # ==================== STRESS/CONFLICT VISUALIZATIONS ====================

    def plot_stress_timeline(self, conflict_detector) -> str:
        """27. Line - Conflict/stress timeline."""
        fig, ax = plt.subplots(figsize=(14, 6))

        monthly_stress = conflict_detector.get_stress_over_time(self.df)

        if len(monthly_stress) > 0:
            dates = [period.to_timestamp() for period in monthly_stress['month_period']]

            # Plot conflict and stress scores
            ax.plot(dates, monthly_stress['avg_conflict'], color='#e74c3c',
                    linewidth=2, label='Conflito', marker='o', markersize=3)
            ax.plot(dates, monthly_stress['avg_stress'], color='#f39c12',
                    linewidth=2, label='Estresse', marker='s', markersize=3)

            # Fill areas
            ax.fill_between(dates, monthly_stress['avg_conflict'], alpha=0.2, color='#e74c3c')
            ax.fill_between(dates, monthly_stress['avg_stress'], alpha=0.2, color='#f39c12')

        ax.set_title('Níveis de Conflito e Estresse ao Longo do Tempo', fontsize=16, fontweight='bold')
        ax.set_xlabel('Data')
        ax.set_ylabel('Score Médio (0-1)')
        ax.legend(loc='upper right')

        ax.xaxis.set_major_locator(mdates.YearLocator())
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y'))

        plt.tight_layout()
        return self._save_fig('27_stress_timeline')

    def plot_stress_causes(self, conflict_detector) -> str:
        """28. Bar - Stress causes by topic."""
        fig, ax = plt.subplots(figsize=(12, 8))

        stress_data = conflict_detector.get_stress_causes(self.df)

        if stress_data['topic_breakdown']:
            # Sort by percentage
            sorted_causes = sorted(stress_data['topic_breakdown'].items(),
                                   key=lambda x: x[1], reverse=True)
            labels, values = zip(*sorted_causes)

            topic_colors = {
                'trabalho': '#3498db',
                'casa': '#e67e22',
                'filhos': '#9b59b6',
                'viagem': '#1abc9c',
                'saude': '#e74c3c',
                'financas': '#f1c40f',
                'lazer': '#2ecc71',
                'relacionamento': '#e91e63',
                'outros': '#95a5a6',
            }

            colors = [topic_colors.get(l, '#95a5a6') for l in labels]
            y_pos = np.arange(len(labels))

            bars = ax.barh(y_pos, values, color=colors)
            ax.set_yticks(y_pos)
            ax.set_yticklabels([l.title() for l in labels])
            ax.invert_yaxis()

            # Add percentage labels
            for bar, value in zip(bars, values):
                ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                        f'{value:.1f}%', va='center', fontsize=10)

        ax.set_title('Causas de Estresse por Tópico', fontsize=16, fontweight='bold')
        ax.set_xlabel('% das Conversas Estressantes')

        plt.tight_layout()
        return self._save_fig('28_stress_causes')

    def plot_stress_topic_heatmap(self, conflict_detector) -> str:
        """29. Heatmap - Stress by topic × day of week."""
        fig, ax = plt.subplots(figsize=(12, 8))

        pivot_data = conflict_detector.get_stress_by_topic_and_day(self.df)

        if len(pivot_data) > 0:
            sns.heatmap(pivot_data, cmap='YlOrRd', ax=ax,
                        annot=True, fmt='d', cbar_kws={'label': 'Mensagens Estressantes'})

            ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
            ax.set_yticklabels([label.get_text().title() for label in ax.get_yticklabels()])
        else:
            ax.text(0.5, 0.5, 'Dados insuficientes para o heatmap',
                    ha='center', va='center', fontsize=12)

        ax.set_title('Estresse por Tópico e Dia da Semana', fontsize=16, fontweight='bold')
        ax.set_xlabel('Dia da Semana')
        ax.set_ylabel('Tópico')

        plt.tight_layout()
        return self._save_fig('29_stress_topic_heatmap')

    # ==================== NEW CONVERSATION-AWARE VISUALIZATIONS ====================

    def plot_sentiment_by_topic(self, analyzer) -> str:
        """30. Grouped Bar - Sentiment by topic."""
        fig, ax = plt.subplots(figsize=(14, 8))

        sentiment_data = analyzer.get_sentiment_by_topic()

        if sentiment_data:
            topics = sorted(sentiment_data.keys(), key=lambda x: sentiment_data[x]['avg_sentiment'], reverse=True)
            avg_sentiments = [sentiment_data[t]['avg_sentiment'] for t in topics]

            topic_colors = {
                'trabalho': '#3498db', 'casa': '#e67e22', 'filhos': '#9b59b6',
                'viagem': '#1abc9c', 'saude': '#e74c3c', 'financas': '#f1c40f',
                'lazer': '#2ecc71', 'relacionamento': '#e91e63', 'outros': '#95a5a6',
            }

            colors = [topic_colors.get(t, '#95a5a6') for t in topics]
            y_pos = np.arange(len(topics))

            bars = ax.barh(y_pos, avg_sentiments, color=colors)
            ax.set_yticks(y_pos)
            ax.set_yticklabels([t.title() for t in topics])
            ax.invert_yaxis()

            # Add zero line
            ax.axvline(x=0, color='gray', linestyle='--', alpha=0.7)

            # Color bars based on sentiment
            for bar, sent in zip(bars, avg_sentiments):
                if sent < 0:
                    bar.set_color('#e74c3c')
                    bar.set_alpha(0.7)

            # Add value labels
            for bar, sent in zip(bars, avg_sentiments):
                x_pos = bar.get_width() + 0.01 if sent >= 0 else bar.get_width() - 0.05
                ax.text(x_pos, bar.get_y() + bar.get_height()/2,
                        f'{sent:.3f}', va='center', fontsize=9)

        ax.set_title('Sentimento Médio por Tópico', fontsize=16, fontweight='bold')
        ax.set_xlabel('Score de Sentimento')
        ax.set_xlim(-0.3, 0.5)

        plt.tight_layout()
        return self._save_fig('30_sentiment_by_topic')

    def plot_topic_initiators(self, topic_analyzer) -> str:
        """31. Horizontal Stacked Bar - Topic initiator balance."""
        fig, ax = plt.subplots(figsize=(14, 8))

        initiator_data = topic_analyzer.get_topic_initiators(self.df)

        if initiator_data:
            # Filter topics with at least some initiations
            topics = [t for t in initiator_data.keys()
                      if initiator_data[t]['total_initiations'] > 10]
            topics = sorted(topics, key=lambda x: initiator_data[x]['total_initiations'], reverse=True)

            if topics:
                y_pos = np.arange(len(topics))
                width = 0.8

                for idx, sender in enumerate(self.participants[:2]):
                    percentages = [initiator_data[t]['percentages'].get(sender, 0) for t in topics]
                    left = [0] * len(topics) if idx == 0 else [
                        initiator_data[t]['percentages'].get(self.participants[0], 0) for t in topics
                    ]

                    bars = ax.barh(y_pos, percentages, width, left=left,
                                   label=sender.split()[0], color=self._get_sender_color(sender))

                ax.set_yticks(y_pos)
                ax.set_yticklabels([t.title() for t in topics])
                ax.invert_yaxis()

                # Add 50% line
                ax.axvline(x=50, color='gray', linestyle='--', alpha=0.7, label='Equilíbrio')

                ax.set_xlabel('% de Iniciações')
                ax.legend(loc='lower right')

        ax.set_title('Quem Inicia Conversas por Tópico', fontsize=16, fontweight='bold')

        plt.tight_layout()
        return self._save_fig('31_topic_initiators')

    def plot_topic_evolution_yearly(self, topic_analyzer) -> str:
        """32. Multi-line - Topic evolution over years."""
        fig, ax = plt.subplots(figsize=(14, 8))

        yearly_data = topic_analyzer.get_topic_evolution_yearly(self.df)

        if len(yearly_data) > 0:
            topic_colors = {
                'trabalho': '#3498db', 'casa': '#e67e22', 'filhos': '#9b59b6',
                'viagem': '#1abc9c', 'saude': '#e74c3c', 'financas': '#f1c40f',
                'lazer': '#2ecc71', 'relacionamento': '#e91e63', 'outros': '#95a5a6',
            }

            years = yearly_data['year'].tolist()

            # Get main topics (excluding outros) sorted by total percentage
            main_topics = []
            for topic in topic_colors.keys():
                if f'{topic}_pct' in yearly_data.columns:
                    avg_pct = yearly_data[f'{topic}_pct'].mean()
                    if avg_pct > 3:  # Only show topics > 3%
                        main_topics.append((topic, avg_pct))

            main_topics = sorted(main_topics, key=lambda x: x[1], reverse=True)[:8]

            for topic, _ in main_topics:
                if f'{topic}_pct' in yearly_data.columns:
                    values = yearly_data[f'{topic}_pct'].tolist()
                    ax.plot(years, values, label=topic.title(),
                            color=topic_colors.get(topic, '#95a5a6'),
                            linewidth=2, marker='o', markersize=6)

            ax.set_xlabel('Ano')
            ax.set_ylabel('% das Mensagens')
            ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1), ncol=1)
            ax.set_xticks(years)

        ax.set_title('Evolução dos Tópicos ao Longo dos Anos', fontsize=16, fontweight='bold')

        plt.tight_layout()
        return self._save_fig('32_topic_evolution_yearly')

    def plot_communication_health(self, analyzer) -> str:
        """33. Radar/Spider - Communication health scorecard."""
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))

        health_data = analyzer.get_communication_health_score()

        if health_data and health_data['components']:
            categories = list(health_data['components'].keys())
            values = [health_data['components'][c] for c in categories]

            # Portuguese labels
            label_map = {
                'response_symmetry': 'Simetria de\nRespostas',
                'topic_diversity': 'Diversidade de\nTópicos',
                'sentiment_trend': 'Tendência de\nSentimento',
                'affection_frequency': 'Frequência de\nCarinho',
                'frequency_trend': 'Tendência de\nConversa',
            }
            labels = [label_map.get(c, c) for c in categories]

            # Close the polygon
            values += values[:1]
            angles = np.linspace(0, 2 * np.pi, len(categories), endpoint=False).tolist()
            angles += angles[:1]

            ax.fill(angles, values, color='#3498db', alpha=0.25)
            ax.plot(angles, values, color='#3498db', linewidth=2)

            # Draw the category labels
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(labels, fontsize=10)

            # Set radial limits
            ax.set_ylim(0, 10)
            ax.set_yticks([2, 4, 6, 8, 10])
            ax.set_yticklabels(['2', '4', '6', '8', '10'], fontsize=8)

            # Add overall score in center
            overall = health_data['overall_score']
            ax.annotate(f'{overall:.1f}/10',
                        xy=(0, 0), ha='center', va='center',
                        fontsize=24, fontweight='bold', color='#2c3e50')

        ax.set_title('Score de Saúde da Comunicação', fontsize=16, fontweight='bold', y=1.08)

        plt.tight_layout()
        return self._save_fig('33_communication_health')

    def plot_conversation_count_by_topic(self, topic_analyzer) -> str:
        """34. Bar - Conversation count by topic."""
        fig, ax = plt.subplots(figsize=(12, 8))

        metrics = topic_analyzer.get_conversation_metrics(self.df)

        if metrics:
            # Sort by conversation count
            sorted_topics = sorted(metrics.items(),
                                   key=lambda x: x[1]['conversation_count'], reverse=True)
            topics = [t[0] for t in sorted_topics]
            counts = [t[1]['conversation_count'] for t in sorted_topics]
            avg_lengths = [t[1]['avg_message_count'] for t in sorted_topics]

            topic_colors = {
                'trabalho': '#3498db', 'casa': '#e67e22', 'filhos': '#9b59b6',
                'viagem': '#1abc9c', 'saude': '#e74c3c', 'financas': '#f1c40f',
                'lazer': '#2ecc71', 'relacionamento': '#e91e63', 'outros': '#95a5a6',
            }

            colors = [topic_colors.get(t, '#95a5a6') for t in topics]
            x_pos = np.arange(len(topics))

            bars = ax.bar(x_pos, counts, color=colors)

            # Add average message count as text on bars
            for bar, count, avg_len in zip(bars, counts, avg_lengths):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 20,
                        f'{count:,}', ha='center', va='bottom', fontsize=9, fontweight='bold')
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height()/2,
                        f'~{avg_len:.0f} msg', ha='center', va='center',
                        fontsize=8, color='white', fontweight='bold')

            ax.set_xticks(x_pos)
            ax.set_xticklabels([t.title() for t in topics], rotation=45, ha='right')
            ax.set_ylabel('Número de Conversas')

        ax.set_title('Número de Conversas por Tópico', fontsize=16, fontweight='bold')

        plt.tight_layout()
        return self._save_fig('34_conversation_count_by_topic')

    def plot_response_time_by_topic(self, analyzer) -> str:
        """35. Grouped Bar - Response time by topic and person."""
        fig, ax = plt.subplots(figsize=(14, 8))

        response_data = analyzer.get_response_time_by_topic()

        if response_data:
            # Filter topics with enough responses
            topics = [t for t in response_data.keys()
                      if response_data[t]['response_count'] > 50]
            topics = sorted(topics, key=lambda x: response_data[x]['avg_response_seconds'])

            if topics:
                x_pos = np.arange(len(topics))
                width = 0.35

                # Plot bars for each sender
                for idx, sender in enumerate(self.participants[:2]):
                    values = []
                    for topic in topics:
                        if sender in response_data[topic].get('by_sender', {}):
                            avg_sec = response_data[topic]['by_sender'][sender]['avg_response_seconds']
                            values.append(avg_sec / 60)  # Convert to minutes
                        else:
                            values.append(0)

                    offset = width * (idx - 0.5)
                    bars = ax.bar(x_pos + offset, values, width,
                                  label=sender.split()[0],
                                  color=self._get_sender_color(sender))

                ax.set_xticks(x_pos)
                ax.set_xticklabels([t.title() for t in topics], rotation=45, ha='right')
                ax.set_ylabel('Tempo de Resposta (minutos)')
                ax.legend(loc='upper right')

        ax.set_title('Tempo Médio de Resposta por Tópico', fontsize=16, fontweight='bold')

        plt.tight_layout()
        return self._save_fig('35_response_time_by_topic')
