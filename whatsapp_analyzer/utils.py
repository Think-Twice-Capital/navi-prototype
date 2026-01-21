"""Utility Functions for WhatsApp Chat Analysis"""

import re
import emoji
from typing import List, Set
from collections import Counter


def format_duration(seconds: int) -> str:
    """Format seconds into human-readable duration."""
    if seconds is None:
        return "N/A"

    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}h {minutes}min {secs}s"
    elif minutes > 0:
        return f"{minutes}min {secs}s"
    else:
        return f"{secs}s"


def format_large_number(num: int) -> str:
    """Format large numbers with thousands separator."""
    return f"{num:,}"


def get_portuguese_stopwords() -> Set[str]:
    """Get a comprehensive set of Portuguese stopwords."""
    stopwords = {
        # Articles
        'o', 'a', 'os', 'as', 'um', 'uma', 'uns', 'umas',
        # Prepositions
        'de', 'da', 'do', 'das', 'dos', 'em', 'na', 'no', 'nas', 'nos',
        'por', 'para', 'pra', 'pro', 'pela', 'pelo', 'pelas', 'pelos',
        'com', 'sem', 'sob', 'sobre', 'entre', 'até', 'após', 'ante',
        # Conjunctions
        'e', 'ou', 'mas', 'porém', 'contudo', 'todavia', 'entretanto',
        'que', 'se', 'como', 'quando', 'enquanto', 'porque', 'pois',
        # Pronouns
        'eu', 'tu', 'ele', 'ela', 'nós', 'vós', 'eles', 'elas',
        'me', 'te', 'se', 'nos', 'vos', 'lhe', 'lhes',
        'meu', 'minha', 'meus', 'minhas', 'teu', 'tua', 'teus', 'tuas',
        'seu', 'sua', 'seus', 'suas', 'nosso', 'nossa', 'nossos', 'nossas',
        'este', 'esta', 'estes', 'estas', 'esse', 'essa', 'esses', 'essas',
        'aquele', 'aquela', 'aqueles', 'aquelas', 'isto', 'isso', 'aquilo',
        'quem', 'qual', 'quais', 'quanto', 'quanta', 'quantos', 'quantas',
        # Verbs (common auxiliaries and forms)
        'é', 'são', 'ser', 'estar', 'estou', 'está', 'estamos', 'estão',
        'foi', 'eram', 'era', 'fui', 'fomos', 'foram', 'será', 'serão',
        'ter', 'tenho', 'tem', 'temos', 'têm', 'tinha', 'tinham', 'teve',
        'haver', 'há', 'havia', 'houve',
        'ir', 'vou', 'vai', 'vamos', 'vão', 'ia', 'iam', 'foi',
        'poder', 'posso', 'pode', 'podemos', 'podem', 'podia', 'podiam',
        'fazer', 'faço', 'faz', 'fazemos', 'fazem', 'fez', 'fazia',
        'dizer', 'digo', 'diz', 'dizemos', 'dizem', 'disse',
        'saber', 'sei', 'sabe', 'sabemos', 'sabem', 'sabia',
        'querer', 'quero', 'quer', 'queremos', 'querem', 'quis', 'queria',
        'ver', 'vejo', 'vê', 'vemos', 'veem', 'viu', 'via',
        'dar', 'dou', 'dá', 'damos', 'dão', 'deu', 'dava',
        'ficar', 'fico', 'fica', 'ficamos', 'ficam', 'ficou', 'ficava',
        # Adverbs
        'não', 'sim', 'já', 'ainda', 'sempre', 'nunca', 'jamais',
        'muito', 'muita', 'muitos', 'muitas', 'pouco', 'pouca', 'poucos', 'poucas',
        'mais', 'menos', 'bem', 'mal', 'assim', 'também', 'só', 'apenas',
        'aqui', 'ali', 'aí', 'lá', 'onde', 'aonde', 'donde',
        'hoje', 'ontem', 'amanhã', 'agora', 'depois', 'antes', 'então',
        'talvez', 'certamente', 'realmente', 'mesmo', 'mesma', 'mesmos', 'mesmas',
        # Other common words
        'tudo', 'nada', 'algo', 'alguém', 'ninguém', 'cada', 'todo', 'toda',
        'todos', 'todas', 'outro', 'outra', 'outros', 'outras',
        'coisa', 'coisas', 'vez', 'vezes', 'tempo', 'dia', 'dias',
        'parte', 'lado', 'forma', 'modo', 'jeito', 'tipo',
        # Chat-specific
        'vc', 'tb', 'tbm', 'pq', 'cmg', 'ctg', 'oq', 'hj', 'blz',
        'kk', 'kkk', 'kkkk', 'kkkkk', 'rs', 'rsrs', 'rsrsrs',
        'haha', 'hahaha', 'hehe', 'hihi',
        'ok', 'okay', 'ta', 'tá', 'né', 'aham', 'uhum', 'hmm',
        # English common words (might appear in chat)
        'the', 'be', 'to', 'of', 'and', 'in', 'that', 'have', 'it',
        'for', 'not', 'on', 'with', 'he', 'as', 'you', 'do', 'at',
        'this', 'but', 'his', 'by', 'from', 'they', 'we', 'say', 'her',
        # Media placeholders
        'attached', 'omitted', 'image', 'video', 'audio', 'sticker',
    }
    return stopwords


def clean_text(text: str, remove_stopwords: bool = True) -> str:
    """Clean text for analysis."""
    if not text:
        return ""

    # Convert to lowercase
    text = text.lower()

    # Remove URLs
    text = re.sub(r'http[s]?://\S+', '', text)

    # Remove media placeholders
    text = re.sub(r'<attached:[^>]+>', '', text)
    text = re.sub(r'\w+ omitted', '', text)

    # Remove special characters but keep accented letters
    text = re.sub(r'[^\w\sáàâãéèêíìîóòôõúùûç]', ' ', text)

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    if remove_stopwords:
        stopwords = get_portuguese_stopwords()
        words = text.split()
        words = [w for w in words if w not in stopwords and len(w) > 1]
        text = ' '.join(words)

    return text


def extract_emojis(text: str) -> List[str]:
    """Extract all emojis from text."""
    return [char for char in text if char in emoji.EMOJI_DATA]


def count_emojis(texts: List[str]) -> Counter:
    """Count emoji occurrences across multiple texts."""
    all_emojis = []
    for text in texts:
        all_emojis.extend(extract_emojis(text))
    return Counter(all_emojis)


def extract_words(text: str, min_length: int = 2) -> List[str]:
    """Extract words from text with minimum length filter."""
    cleaned = clean_text(text, remove_stopwords=True)
    words = cleaned.split()
    return [w for w in words if len(w) >= min_length]


def count_words(texts: List[str], min_length: int = 2) -> Counter:
    """Count word occurrences across multiple texts."""
    all_words = []
    for text in texts:
        all_words.extend(extract_words(text, min_length))
    return Counter(all_words)


def calculate_streak(dates: List) -> dict:
    """Calculate messaging streaks from a list of dates."""
    if not dates:
        return {'current': 0, 'longest': 0, 'longest_start': None, 'longest_end': None}

    # Convert to set of unique dates
    unique_dates = sorted(set(dates))

    if len(unique_dates) < 2:
        return {'current': 1, 'longest': 1, 'longest_start': unique_dates[0], 'longest_end': unique_dates[0]}

    # Find streaks
    streaks = []
    current_streak_start = unique_dates[0]
    current_streak_length = 1

    for i in range(1, len(unique_dates)):
        diff = (unique_dates[i] - unique_dates[i-1]).days

        if diff == 1:
            current_streak_length += 1
        else:
            streaks.append({
                'start': current_streak_start,
                'end': unique_dates[i-1],
                'length': current_streak_length
            })
            current_streak_start = unique_dates[i]
            current_streak_length = 1

    # Don't forget the last streak
    streaks.append({
        'start': current_streak_start,
        'end': unique_dates[-1],
        'length': current_streak_length
    })

    # Find longest streak
    longest = max(streaks, key=lambda x: x['length'])

    # Current streak (most recent)
    current = streaks[-1]['length']

    return {
        'current': current,
        'longest': longest['length'],
        'longest_start': longest['start'],
        'longest_end': longest['end'],
        'all_streaks': streaks
    }


def day_name_pt(day_num: int) -> str:
    """Convert day number to Portuguese day name."""
    days = {
        0: 'Segunda',
        1: 'Terça',
        2: 'Quarta',
        3: 'Quinta',
        4: 'Sexta',
        5: 'Sábado',
        6: 'Domingo'
    }
    return days.get(day_num, 'Unknown')


def month_name_pt(month_num: int) -> str:
    """Convert month number to Portuguese month name."""
    months = {
        1: 'Janeiro',
        2: 'Fevereiro',
        3: 'Março',
        4: 'Abril',
        5: 'Maio',
        6: 'Junho',
        7: 'Julho',
        8: 'Agosto',
        9: 'Setembro',
        10: 'Outubro',
        11: 'Novembro',
        12: 'Dezembro'
    }
    return months.get(month_num, 'Unknown')
