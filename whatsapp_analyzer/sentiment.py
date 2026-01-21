"""Portuguese Sentiment Analysis Module"""

import re
import pandas as pd
from typing import Dict, List, Tuple
from collections import defaultdict


class SentimentAnalyzer:
    """Lexicon-based sentiment analyzer for Brazilian Portuguese."""

    def __init__(self):
        """Initialize with Portuguese sentiment lexicons."""
        self.positive_words = self._get_positive_words()
        self.negative_words = self._get_negative_words()
        self.intensifiers = self._get_intensifiers()
        self.negators = self._get_negators()

    def _get_positive_words(self) -> set:
        """Get set of positive words in Portuguese."""
        return {
            # Love and affection
            'amor', 'amo', 'ama', 'amando', 'amei', 'amou', 'amar',
            'adoro', 'adora', 'adorando', 'adorei', 'adorou', 'adorar',
            'carinho', 'carinhoso', 'carinhosa', 'afeto', 'afetuoso',
            'querido', 'querida', 'quero', 'quer', 'querer',
            'beijo', 'beijos', 'beijar', 'beijinho', 'beijinhos',
            'abraço', 'abraços', 'abraçar',
            'coração', 'coracão',

            # Happiness
            'feliz', 'felicidade', 'felizes', 'alegre', 'alegria',
            'contente', 'satisfeito', 'satisfeita',
            'empolgado', 'empolgada', 'animado', 'animada',
            'entusiasmado', 'entusiasmada',

            # Positive adjectives
            'bom', 'boa', 'bons', 'boas', 'ótimo', 'ótima', 'ótimos',
            'excelente', 'maravilhoso', 'maravilhosa', 'incrível',
            'perfeito', 'perfeita', 'lindo', 'linda', 'lindos', 'lindas',
            'bonito', 'bonita', 'bonitos', 'bonitas',
            'fofo', 'fofa', 'fofos', 'fofas', 'fofinho', 'fofinha',
            'legal', 'bacana', 'demais', 'show',
            'melhor', 'melhores', 'especial', 'especiais',
            'favorito', 'favorita',

            # Gratitude
            'obrigado', 'obrigada', 'agradeço', 'agradecido', 'agradecida',
            'grato', 'grata', 'valeu',

            # Positive verbs
            'gosto', 'gosta', 'gostando', 'gostei', 'gostou', 'gostar',
            'curto', 'curte', 'curtindo', 'curti', 'curtiu', 'curtir',
            'diverte', 'divertido', 'divertida',
            'relaxar', 'relaxando', 'relaxado', 'relaxada',
            'sorrir', 'sorrindo', 'sorriso', 'sorrisos',
            'rir', 'rindo', 'risada', 'risadas', 'risos',
            'celebrar', 'celebrando', 'comemorar', 'comemorando',

            # Agreement and support
            'sim', 'claro', 'certeza', 'verdade', 'concordo',
            'apoio', 'apoiar', 'ajuda', 'ajudar', 'ajudando',
            'consegui', 'conseguiu', 'conseguir', 'conseguimos',
            'sucesso', 'vitória', 'venceu', 'ganhou',

            # Terms of endearment
            'bebê', 'bebe', 'neném', 'nenem', 'princesa', 'príncipe',
            'anjo', 'anjinho', 'vida', 'minha vida',

            # Positive expressions
            'parabéns', 'parabens', 'orgulho', 'orgulhoso', 'orgulhosa',
            'saudade', 'saudades', 'miss',
            'sonho', 'sonhos', 'sonhar', 'sonhando',
            'esperança', 'espero', 'esperando',

            # Chat expressions
            'haha', 'hahaha', 'hehe', 'hihi', 'kkk', 'kkkk', 'kkkkk',
            'rsrs', 'rsrsrs', 'lol', 'uhu', 'eba', 'uhul', 'yay',
        }

    def _get_negative_words(self) -> set:
        """Get set of negative words in Portuguese."""
        return {
            # Sadness
            'triste', 'tristeza', 'chorar', 'chorando', 'chorei', 'chorou',
            'choro', 'lágrimas', 'lagrimas', 'deprimido', 'deprimida',
            'desanimado', 'desanimada', 'desanimar',
            'sozinho', 'sozinha', 'solidão', 'solidao',

            # Anger
            'raiva', 'bravo', 'brava', 'irritado', 'irritada',
            'furioso', 'furiosa', 'nervoso', 'nervosa',
            'ódio', 'odio', 'odeio', 'odeia', 'odiar',
            'detesto', 'detesta', 'detestar',

            # Negative adjectives
            'ruim', 'ruins', 'péssimo', 'péssima', 'pessimo', 'pessima',
            'horrível', 'terrível', 'feio', 'feia', 'feios', 'feias',
            'chato', 'chata', 'chatos', 'chatas', 'chatice',
            'difícil', 'dificil', 'complicado', 'complicada',
            'impossível', 'impossivel',

            # Fear and worry
            'medo', 'medroso', 'medrosa', 'assustado', 'assustada',
            'preocupado', 'preocupada', 'preocupar', 'preocupação',
            'ansioso', 'ansiosa', 'ansiedade', 'angústia', 'angustia',
            'tenso', 'tensa', 'tensão', 'tensao', 'estresse', 'stress',

            # Pain and discomfort
            'dor', 'dores', 'doendo', 'doeu', 'machucado', 'machucada',
            'cansado', 'cansada', 'cansaço', 'exausto', 'exausta',
            'doente', 'doença', 'enfermo', 'enferma',

            # Disappointment
            'decepção', 'decepcao', 'decepcionado', 'decepcionada',
            'frustrado', 'frustrada', 'frustração', 'frustracao',
            'desapontado', 'desapontada',

            # Problems
            'problema', 'problemas', 'erro', 'erros', 'errado', 'errada',
            'falha', 'falhar', 'falhei', 'falhou', 'fracasso',
            'perdi', 'perdeu', 'perder', 'perdido', 'perdida',

            # Negative verbs
            'desculpa', 'desculpe', 'perdão', 'perdao', 'sinto muito',
            'infelizmente', 'lamento',

            # Conflict
            'briga', 'brigar', 'brigando', 'brigamos', 'brigas',
            'discussão', 'discussao', 'discutir', 'discutindo',
            'conflito', 'conflitos',

            # Chat expressions (negative)
            'pqp', 'merda', 'droga', 'caramba', 'putz',
        }

    def _get_intensifiers(self) -> set:
        """Get words that intensify sentiment."""
        return {
            'muito', 'muita', 'muitos', 'muitas',
            'demais', 'bastante', 'extremamente', 'super',
            'mega', 'ultra', 'hiper', 'totalmente',
            'completamente', 'absolutamente', 'realmente',
            'verdadeiramente', 'incrivelmente',
        }

    def _get_negators(self) -> set:
        """Get words that negate sentiment."""
        return {
            'não', 'nao', 'nunca', 'jamais', 'nem',
            'nenhum', 'nenhuma', 'nada', 'tampouco',
        }

    def analyze_text(self, text: str) -> Dict:
        """Analyze sentiment of a single text."""
        if not text:
            return {'score': 0, 'label': 'neutral', 'positive_count': 0, 'negative_count': 0}

        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)

        positive_count = 0
        negative_count = 0
        has_negator = False
        intensity = 1.0

        for i, word in enumerate(words):
            # Check for negators
            if word in self.negators:
                has_negator = True
                continue

            # Check for intensifiers
            if word in self.intensifiers:
                intensity = 1.5
                continue

            # Check sentiment
            if word in self.positive_words:
                if has_negator:
                    negative_count += intensity
                else:
                    positive_count += intensity
                has_negator = False
                intensity = 1.0

            elif word in self.negative_words:
                if has_negator:
                    positive_count += intensity * 0.5  # Negated negative is weakly positive
                else:
                    negative_count += intensity
                has_negator = False
                intensity = 1.0

        # Calculate score (-1 to 1)
        total = positive_count + negative_count
        if total == 0:
            score = 0
        else:
            score = (positive_count - negative_count) / (positive_count + negative_count)

        # Determine label
        if score > 0.1:
            label = 'positive'
        elif score < -0.1:
            label = 'negative'
        else:
            label = 'neutral'

        return {
            'score': score,
            'label': label,
            'positive_count': positive_count,
            'negative_count': negative_count
        }

    def analyze_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add sentiment columns to DataFrame."""
        df = df.copy()

        # Analyze sentiment for text messages only
        text_mask = df['type'] == 'text'

        df['sentiment_score'] = 0.0
        df['sentiment_label'] = 'neutral'
        df['positive_words'] = 0.0
        df['negative_words'] = 0.0

        for idx in df[text_mask].index:
            result = self.analyze_text(df.loc[idx, 'message'])
            df.loc[idx, 'sentiment_score'] = result['score']
            df.loc[idx, 'sentiment_label'] = result['label']
            df.loc[idx, 'positive_words'] = result['positive_count']
            df.loc[idx, 'negative_words'] = result['negative_count']

        return df

    def get_monthly_sentiment(self, df: pd.DataFrame) -> pd.DataFrame:
        """Get average sentiment by month."""
        df = df.copy()
        df['month_period'] = df['datetime'].dt.to_period('M')

        text_df = df[df['type'] == 'text'].copy()

        monthly = text_df.groupby('month_period').agg({
            'sentiment_score': 'mean',
            'positive_words': 'sum',
            'negative_words': 'sum'
        }).reset_index()

        return monthly

    def get_sentiment_by_sender(self, df: pd.DataFrame) -> Dict:
        """Get sentiment statistics by sender."""
        text_df = df[df['type'] == 'text']

        results = {}
        for sender in df['sender'].unique():
            sender_df = text_df[text_df['sender'] == sender]
            results[sender] = {
                'avg_score': sender_df['sentiment_score'].mean(),
                'positive_messages': len(sender_df[sender_df['sentiment_label'] == 'positive']),
                'negative_messages': len(sender_df[sender_df['sentiment_label'] == 'negative']),
                'neutral_messages': len(sender_df[sender_df['sentiment_label'] == 'neutral']),
                'total_positive_words': sender_df['positive_words'].sum(),
                'total_negative_words': sender_df['negative_words'].sum(),
            }

        return results

    def get_sentiment_trends(self, df: pd.DataFrame) -> Dict:
        """Get sentiment trends over time."""
        monthly = self.get_monthly_sentiment(df)

        # Find peaks and valleys
        scores = monthly['sentiment_score'].values

        trends = {
            'overall_avg': df[df['type'] == 'text']['sentiment_score'].mean(),
            'most_positive_month': None,
            'most_negative_month': None,
            'monthly_data': monthly.to_dict('records')
        }

        if len(monthly) > 0:
            max_idx = monthly['sentiment_score'].idxmax()
            min_idx = monthly['sentiment_score'].idxmin()

            trends['most_positive_month'] = {
                'period': str(monthly.loc[max_idx, 'month_period']),
                'score': monthly.loc[max_idx, 'sentiment_score']
            }
            trends['most_negative_month'] = {
                'period': str(monthly.loc[min_idx, 'month_period']),
                'score': monthly.loc[min_idx, 'sentiment_score']
            }

        return trends
