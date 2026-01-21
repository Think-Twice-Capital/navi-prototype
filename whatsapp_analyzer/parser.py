"""WhatsApp Chat Parser Module"""

import re
import pandas as pd
from datetime import datetime
from typing import List, Dict, Optional, Tuple


class WhatsAppParser:
    """Parser for WhatsApp chat export files."""

    # WhatsApp export format: [M/D/YY, H:MM:SS AM/PM] Sender: Message
    MESSAGE_PATTERN = re.compile(
        r'^\[(\d{1,2}/\d{1,2}/\d{2}),\s*(\d{1,2}:\d{2}:\d{2}\s*[AP]M)\]\s*([^:]+):\s*(.*)$'
    )

    # Media patterns
    MEDIA_PATTERNS = {
        'image': re.compile(r'<attached:\s*\d+-[A-Z]+-[A-Z]+-[A-Z]+-[A-Z]+\.(?:jpg|jpeg|png|gif|webp)>', re.IGNORECASE),
        'video': re.compile(r'<attached:\s*\d+-[A-Z]+-[A-Z]+-[A-Z]+-[A-Z]+\.(?:mp4|mov|avi|3gp)>', re.IGNORECASE),
        'audio': re.compile(r'<attached:\s*\d+-[A-Z]+-[A-Z]+-[A-Z]+-[A-Z]+\.(?:opus|mp3|m4a|aac|ogg)>', re.IGNORECASE),
        'document': re.compile(r'<attached:\s*\d+-[A-Z]+-[A-Z]+-[A-Z]+-[A-Z]+\.(?:pdf|doc|docx|xls|xlsx|ppt|pptx|txt|zip)>', re.IGNORECASE),
        'sticker': re.compile(r'<attached:\s*\d+-[A-Z]+-[A-Z]+-[A-Z]+-[A-Z]+\.webp>', re.IGNORECASE),
    }

    # Call patterns
    CALL_PATTERNS = {
        'voice_call': re.compile(r'(?:Chamada de voz|Voice call|Ligação de voz)', re.IGNORECASE),
        'video_call': re.compile(r'(?:Chamada de vídeo|Video call|Videochamada)', re.IGNORECASE),
        'missed_voice': re.compile(r'(?:Chamada de voz perdida|Missed voice call)', re.IGNORECASE),
        'missed_video': re.compile(r'(?:Chamada de vídeo perdida|Missed video call)', re.IGNORECASE),
    }

    # Duration pattern (e.g., "2 min 30 seg" or "1:23:45")
    DURATION_PATTERN = re.compile(
        r'(?:(\d+)\s*(?:h|hora|hours?))?\s*(?:(\d+)\s*(?:min|minuto|minutes?))?\s*(?:(\d+)\s*(?:s|seg|segundo|seconds?))?|(\d+):(\d{2}):(\d{2})|(\d+):(\d{2})'
    )

    # System message patterns
    SYSTEM_PATTERNS = [
        re.compile(r'Messages and calls are end-to-end encrypted', re.IGNORECASE),
        re.compile(r'As mensagens e as chamadas são protegidas', re.IGNORECASE),
        re.compile(r'You deleted this message', re.IGNORECASE),
        re.compile(r'Esta mensagem foi apagada', re.IGNORECASE),
        re.compile(r'This message was deleted', re.IGNORECASE),
        re.compile(r'image omitted', re.IGNORECASE),
        re.compile(r'video omitted', re.IGNORECASE),
        re.compile(r'audio omitted', re.IGNORECASE),
        re.compile(r'sticker omitted', re.IGNORECASE),
        re.compile(r'document omitted', re.IGNORECASE),
        re.compile(r'GIF omitted', re.IGNORECASE),
        re.compile(r'Contact card omitted', re.IGNORECASE),
        re.compile(r'Location:.*', re.IGNORECASE),
    ]

    def __init__(self, filepath: str):
        """Initialize parser with file path."""
        self.filepath = filepath
        self.messages: List[Dict] = []
        self.df: Optional[pd.DataFrame] = None

    def parse(self) -> pd.DataFrame:
        """Parse the WhatsApp chat file and return a DataFrame."""
        print(f"Parsing file: {self.filepath}")

        with open(self.filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')
        print(f"Total lines: {len(lines)}")

        current_message = None

        for line in lines:
            match = self.MESSAGE_PATTERN.match(line)

            if match:
                # Save previous message if exists
                if current_message:
                    self.messages.append(current_message)

                date_str, time_str, sender, message = match.groups()

                # Parse datetime
                try:
                    datetime_str = f"{date_str} {time_str}"
                    dt = datetime.strptime(datetime_str, "%m/%d/%y %I:%M:%S %p")
                except ValueError:
                    try:
                        dt = datetime.strptime(datetime_str, "%d/%m/%y %I:%M:%S %p")
                    except ValueError:
                        continue

                # Classify message type
                msg_type, call_duration = self._classify_message(message)

                current_message = {
                    'datetime': dt,
                    'date': dt.date(),
                    'time': dt.time(),
                    'year': dt.year,
                    'month': dt.month,
                    'day': dt.day,
                    'hour': dt.hour,
                    'day_of_week': dt.strftime('%A'),
                    'day_of_week_num': dt.weekday(),
                    'sender': sender.strip(),
                    'message': message.strip(),
                    'type': msg_type,
                    'call_duration_seconds': call_duration,
                    'message_length': len(message.strip()) if msg_type == 'text' else 0,
                    'word_count': len(message.split()) if msg_type == 'text' else 0,
                }
            elif current_message and line.strip():
                # Multi-line message continuation
                current_message['message'] += '\n' + line
                if current_message['type'] == 'text':
                    current_message['message_length'] = len(current_message['message'])
                    current_message['word_count'] = len(current_message['message'].split())

        # Don't forget the last message
        if current_message:
            self.messages.append(current_message)

        # Create DataFrame
        self.df = pd.DataFrame(self.messages)

        if not self.df.empty:
            self.df['datetime'] = pd.to_datetime(self.df['datetime'])
            self.df = self.df.sort_values('datetime').reset_index(drop=True)

        print(f"Parsed {len(self.df)} messages")
        print(f"Date range: {self.df['datetime'].min()} to {self.df['datetime'].max()}")

        return self.df

    def _classify_message(self, message: str) -> Tuple[str, Optional[int]]:
        """Classify message type and extract call duration if applicable."""
        message_lower = message.lower()

        # Check for calls first
        for call_type, pattern in self.CALL_PATTERNS.items():
            if pattern.search(message):
                duration = self._extract_call_duration(message)
                return call_type, duration

        # Check for media
        for media_type, pattern in self.MEDIA_PATTERNS.items():
            if pattern.search(message):
                return media_type, None

        # Check for omitted media
        if 'image omitted' in message_lower:
            return 'image', None
        if 'video omitted' in message_lower:
            return 'video', None
        if 'audio omitted' in message_lower:
            return 'audio', None
        if 'sticker omitted' in message_lower:
            return 'sticker', None
        if 'document omitted' in message_lower:
            return 'document', None
        if 'gif omitted' in message_lower:
            return 'gif', None
        if 'contact card omitted' in message_lower:
            return 'contact', None

        # Check for system messages
        for pattern in self.SYSTEM_PATTERNS:
            if pattern.search(message):
                return 'system', None

        # Default to text
        return 'text', None

    def _extract_call_duration(self, message: str) -> Optional[int]:
        """Extract call duration in seconds from message."""
        match = self.DURATION_PATTERN.search(message)
        if not match:
            return None

        groups = match.groups()

        # Check for "Xh Xmin Xs" format
        if groups[0] or groups[1] or groups[2]:
            hours = int(groups[0]) if groups[0] else 0
            minutes = int(groups[1]) if groups[1] else 0
            seconds = int(groups[2]) if groups[2] else 0
            return hours * 3600 + minutes * 60 + seconds

        # Check for "H:MM:SS" format
        if groups[3] and groups[4] and groups[5]:
            return int(groups[3]) * 3600 + int(groups[4]) * 60 + int(groups[5])

        # Check for "M:SS" format
        if groups[6] and groups[7]:
            return int(groups[6]) * 60 + int(groups[7])

        return None

    def get_participants(self) -> List[str]:
        """Get list of unique participants."""
        if self.df is None:
            return []
        return self.df['sender'].unique().tolist()

    def get_date_range(self) -> Tuple[datetime, datetime]:
        """Get the date range of the chat."""
        if self.df is None or self.df.empty:
            return None, None
        return self.df['datetime'].min(), self.df['datetime'].max()

    def filter_by_sender(self, sender: str) -> pd.DataFrame:
        """Filter messages by sender."""
        if self.df is None:
            return pd.DataFrame()
        return self.df[self.df['sender'] == sender].copy()

    def filter_by_type(self, msg_type: str) -> pd.DataFrame:
        """Filter messages by type."""
        if self.df is None:
            return pd.DataFrame()
        return self.df[self.df['type'] == msg_type].copy()

    def filter_by_date_range(self, start: datetime, end: datetime) -> pd.DataFrame:
        """Filter messages by date range."""
        if self.df is None:
            return pd.DataFrame()
        mask = (self.df['datetime'] >= start) & (self.df['datetime'] <= end)
        return self.df[mask].copy()
