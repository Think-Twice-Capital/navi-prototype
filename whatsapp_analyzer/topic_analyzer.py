"""Topic Classification Module for WhatsApp Chat Analysis"""

import re
import pandas as pd
from typing import Dict, List, Tuple
from collections import defaultdict


class TopicAnalyzer:
    """Lexicon-based topic classifier for Brazilian Portuguese WhatsApp messages."""

    def __init__(self):
        """Initialize with Portuguese topic lexicons."""
        self.topics = self._get_topic_lexicons()
        self.topic_names = {
            'trabalho': 'Trabalho (Work)',
            'casa': 'Casa (House Chores)',
            'filhos': 'Filhos/Familia (Kids/Family)',
            'viagem': 'Viagem (Travel)',
            'saude': 'Saude (Health)',
            'financas': 'Financas (Finance)',
            'lazer': 'Lazer (Leisure)',
            'relacionamento': 'Relacionamento (Relationship)',
        }

    def _get_topic_lexicons(self) -> Dict[str, set]:
        """Get topic keyword lexicons in Portuguese."""
        return {
            'trabalho': {
                # Core work terms
                'trabalho', 'trabalhar', 'trabalhando', 'trabalhei', 'trabalhou',
                'trabalhos', 'trabalhado', 'trampo', 'trampando', 'trampei',
                # Meetings and office
                'reuniao', 'reunioes', 'meeting', 'call', 'calls',
                'escritorio', 'office', 'home office', 'homeoffice',
                # Projects and tasks
                'projeto', 'projetos', 'tarefa', 'tarefas', 'demanda', 'demandas',
                'entrega', 'entregas', 'entregar', 'entregue', 'deadline', 'prazo',
                # People
                'cliente', 'clientes', 'chefe', 'gerente', 'diretor', 'colega',
                'colegas', 'equipe', 'time', 'funcionario', 'funcionarios',
                # Actions
                'apresentacao', 'apresentar', 'relatorio', 'email', 'emails',
                'planilha', 'documento', 'contrato', 'proposta',
                # Status
                'ocupado', 'ocupada', 'atarefado', 'atarefada', 'corrido', 'corrida',
                'atrasado', 'atrasada', 'adiantado', 'adiantada',
                # Career
                'emprego', 'carreira', 'profissional', 'salario', 'promocao',
                'empresa', 'empresas', 'negocio', 'negocios',
            },
            'casa': {
                # Cleaning
                'limpeza', 'limpar', 'limpando', 'limpei', 'limpo', 'limpa',
                'faxina', 'faxineira', 'varrer', 'esfregar', 'passar pano',
                # Laundry
                'lavar', 'lavando', 'lavei', 'roupa', 'roupas', 'secar',
                'passar roupa', 'estender', 'maquina de lavar',
                # Dishes
                'louca', 'loucas', 'louça', 'louças', 'prato', 'pratos',
                'lavar louca', 'lavar louça',
                # Kitchen
                'cozinhar', 'cozinhando', 'cozinhei', 'cozinha', 'comida',
                'jantar', 'almoco', 'almoço', 'cafe', 'café', 'refeicao',
                # Shopping
                'compras', 'mercado', 'supermercado', 'feira', 'padaria',
                'comprar', 'comprando', 'comprei',
                # Organization
                'organizar', 'organizando', 'organizei', 'arrumar', 'arrumando',
                'arrumei', 'guardar', 'guardando', 'guardei', 'bagunca',
                # Repairs
                'consertar', 'consertando', 'consertei', 'quebrou', 'estragou',
                'manutencao', 'encanador', 'eletricista',
                # General house
                'casa', 'apartamento', 'ape', 'lar', 'quarto', 'sala',
                'banheiro', 'cozinha', 'varanda', 'garagem',
            },
            'filhos': {
                # Children
                'filho', 'filha', 'filhos', 'filhas', 'crianca', 'criancas',
                'bebe', 'bebê', 'nenem', 'neném', 'pequeno', 'pequena',
                # Family
                'familia', 'mae', 'mãe', 'pai', 'pais', 'avo', 'avó', 'irmao',
                'irma', 'irmã', 'tio', 'tia', 'primo', 'prima', 'sobrinho', 'sobrinha',
                # School
                'escola', 'colegio', 'aula', 'aulas', 'professor', 'professora',
                'dever', 'licao', 'lição', 'prova', 'nota', 'notas',
                'matricula', 'formatura', 'recreio', 'merenda',
                # Activities
                'brincar', 'brincando', 'brincadeira', 'brinquedo', 'brinquedos',
                'parquinho', 'parque', 'jogar', 'jogando',
                # Care
                'cuidar', 'cuidando', 'banho', 'mamadeira', 'fralda', 'fraldas',
                'pediatra', 'vacina', 'vacinas', 'creche', 'baba',
                # Events
                'aniversario', 'festinha', 'formatura',
            },
            'viagem': {
                # Travel
                'viagem', 'viagens', 'viajar', 'viajando', 'viajei', 'viajou',
                'trip', 'passeio', 'passeios', 'passear', 'passeando',
                # Transport
                'voo', 'voos', 'voar', 'aviao', 'aeroporto', 'embarque',
                'desembarque', 'conexao', 'escala',
                'carro', 'dirigir', 'estrada', 'rodovia', 'pedagio',
                'onibus', 'ônibus', 'trem', 'metro', 'uber', 'taxi',
                # Accommodation
                'hotel', 'hoteis', 'pousada', 'airbnb', 'hospedagem',
                'reserva', 'reservar', 'check-in', 'checkout',
                # Tickets
                'passagem', 'passagens', 'bilhete', 'bilhetes',
                # Luggage
                'mala', 'malas', 'bagagem', 'mochila',
                # Destinations
                'praia', 'praias', 'montanha', 'campo', 'sitio', 'fazenda',
                'cidade', 'pais', 'exterior', 'internacional',
                # Vacation
                'ferias', 'férias', 'feriado', 'feriados', 'folga', 'descanso',
                # Tourism
                'turismo', 'turista', 'pontos turisticos', 'excursao',
            },
            'saude': {
                # Medical
                'medico', 'médico', 'medica', 'médica', 'doutor', 'doutora',
                'consulta', 'consultorio', 'clinica', 'clínica',
                'hospital', 'pronto socorro', 'upa', 'emergencia',
                # Medicine
                'remedio', 'remedios', 'medicamento', 'medicamentos',
                'receita', 'farmacia', 'farmácia', 'comprimido', 'xarope',
                # Conditions
                'doenca', 'doença', 'doente', 'gripe', 'resfriado', 'febre',
                'dor', 'dores', 'dor de cabeca', 'enxaqueca',
                'alergia', 'infeccao', 'inflamacao', 'virus',
                # Body parts (when related to health)
                'garganta', 'estomago', 'barriga', 'costas', 'cabeca',
                # Exams
                'exame', 'exames', 'sangue', 'raio x', 'ultrassom', 'ressonancia',
                # Treatment
                'tratamento', 'cirurgia', 'operacao', 'recuperacao', 'fisioterapia',
                # Exercise
                'exercicio', 'exercicios', 'academia', 'treino', 'treinar',
                'malhar', 'malhando', 'musculacao', 'corrida', 'caminhada',
                'yoga', 'pilates', 'alongamento',
                # Diet
                'dieta', 'emagrecer', 'peso', 'balanca', 'nutricionista',
                # Mental health
                'terapia', 'psicologo', 'psicóloga', 'ansiedade', 'depressao',
                # Sleep
                'dormir', 'sono', 'insonia', 'cansaco', 'cansada', 'cansado',
            },
            'financas': {
                # Money
                'dinheiro', 'grana', 'bufunfa', 'verba', 'valor', 'valores',
                'real', 'reais', 'dolar', 'dolares',
                # Bank
                'banco', 'conta', 'contas', 'saldo', 'extrato',
                'transferencia', 'pix', 'ted', 'doc', 'deposito',
                'saque', 'caixa', 'caixa eletronico',
                # Payments
                'pagar', 'pagando', 'paguei', 'pagamento', 'pagamentos',
                'boleto', 'boletos', 'fatura', 'faturas',
                'parcela', 'parcelas', 'parcelado', 'parcelar',
                # Cards
                'cartao', 'cartão', 'cartoes', 'credito', 'débito', 'debito',
                'limite', 'anuidade',
                # Income
                'salario', 'salário', 'pagamento', 'renda', 'receita',
                'bonus', 'comissao', 'ferias', 'decimo terceiro', '13o',
                # Expenses
                'gasto', 'gastos', 'despesa', 'despesas', 'custo', 'custos',
                'caro', 'barato', 'preco', 'preço', 'promocao', 'desconto',
                # Investments
                'investimento', 'investimentos', 'investir', 'investindo',
                'poupanca', 'poupança', 'rendimento', 'juros', 'acoes',
                'bitcoin', 'cripto', 'tesouro',
                # Bills
                'aluguel', 'condominio', 'luz', 'agua', 'gas', 'internet',
                'celular', 'seguro', 'iptu', 'ipva',
                # Debt
                'divida', 'dívida', 'dividas', 'devendo', 'emprestimo', 'financiamento',
            },
            'lazer': {
                # Entertainment
                'filme', 'filmes', 'cinema', 'assistir', 'assistindo',
                'serie', 'séries', 'netflix', 'streaming', 'prime', 'hbo',
                'episodio', 'temporada', 'maratona', 'maratonando',
                # Music
                'musica', 'música', 'show', 'shows', 'concerto', 'spotify',
                'playlist', 'banda', 'cantor', 'cantora',
                # Food and drinks out
                'restaurante', 'jantar fora', 'almoco fora', 'bar', 'boteco',
                'happy hour', 'cerveja', 'vinho', 'drink', 'drinks',
                'pizza', 'hamburguer', 'sushi', 'rodizio', 'churrasco',
                # Social
                'festa', 'festas', 'balada', 'aniversario', 'comemoracao',
                'amigos', 'amigas', 'galera', 'pessoal', 'turma',
                'encontro', 'rolê', 'role', 'sair', 'saindo',
                # Games
                'jogo', 'jogos', 'jogar', 'jogando', 'game', 'games',
                'videogame', 'playstation', 'xbox', 'nintendo',
                # Hobbies
                'hobby', 'hobbies', 'ler', 'lendo', 'livro', 'livros', 'leitura',
                'desenhar', 'pintar', 'artesanato', 'costurar',
                # Sports (watching)
                'futebol', 'jogo do', 'partida', 'campeonato',
                # Weekend
                'fim de semana', 'fds', 'sabado', 'sábado', 'domingo',
                'descansar', 'descansando', 'relaxar', 'relaxando',
            },
            'relacionamento': {
                # Love
                'amor', 'amo', 'ama', 'amando', 'amei', 'te amo',
                'paixao', 'paixão', 'apaixonado', 'apaixonada',
                # Affection
                'carinho', 'carinhoso', 'carinhosa', 'afeto', 'afetuoso',
                'querido', 'querida', 'quero', 'quer',
                'beijo', 'beijos', 'beijar', 'beijinho', 'beijao',
                'abraco', 'abraço', 'abracos', 'abraçar',
                # Terms of endearment
                'bb', 'bebe', 'bebê', 'meu amor', 'minha vida',
                'linda', 'lindo', 'princesa', 'principe', 'anjo',
                'fofo', 'fofa', 'fofinho', 'fofinha', 'gato', 'gata',
                'mozao', 'mozão', 'amorzinho',
                # Relationship
                'namorado', 'namorada', 'namoro', 'namorando',
                'casamento', 'casar', 'marido', 'esposa',
                'relacionamento', 'casal', 'juntos', 'juntas',
                # Missing
                'saudade', 'saudades', 'falta', 'miss', 'sentindo falta',
                # Together
                'nos', 'nós', 'gente', 'nosso', 'nossa', 'nossos', 'nossas',
                'junto', 'juntos', 'juntinho', 'juntinhos',
                # Special
                'especial', 'importante', 'significativo', 'unico', 'única',
                # Compliments
                'bonito', 'bonita', 'lindo', 'linda', 'gostoso', 'gostosa',
                'maravilhoso', 'maravilhosa', 'perfeito', 'perfeita',
            },
        }

    def classify_text(self, text: str) -> Dict[str, float]:
        """
        Classify a single text message into topics.

        Args:
            text: Message text to classify

        Returns:
            Dictionary mapping topic names to confidence scores (0-1)
        """
        if not text:
            return {topic: 0.0 for topic in self.topics}

        text_lower = text.lower()
        words = set(re.findall(r'\b\w+\b', text_lower))

        scores = {}
        total_matches = 0

        for topic, keywords in self.topics.items():
            matches = len(words.intersection(keywords))
            scores[topic] = matches
            total_matches += matches

        # Normalize scores to 0-1 range
        if total_matches > 0:
            for topic in scores:
                scores[topic] = scores[topic] / total_matches
        else:
            scores = {topic: 0.0 for topic in self.topics}

        return scores

    def get_primary_topic(self, text: str) -> Tuple[str, float]:
        """
        Get the primary topic for a text message.

        Args:
            text: Message text to classify

        Returns:
            Tuple of (topic_name, confidence_score)
        """
        scores = self.classify_text(text)
        if not scores or all(v == 0 for v in scores.values()):
            return ('outros', 0.0)

        primary_topic = max(scores, key=scores.get)
        return (primary_topic, scores[primary_topic])

    def analyze_dataframe(self, df: pd.DataFrame, context_aware: bool = True,
                          reset_gap_hours: float = 4.0) -> pd.DataFrame:
        """
        Add topic classification columns to DataFrame.

        Args:
            df: DataFrame with 'message' column
            context_aware: If True, use context propagation for topic assignment
            reset_gap_hours: Hours of silence before resetting active topic

        Returns:
            DataFrame with added topic columns
        """
        df = df.copy()

        # Initialize topic columns
        for topic in self.topics:
            df[f'topic_{topic}'] = 0.0

        df['primary_topic'] = 'outros'
        df['topic_confidence'] = 0.0
        df['topic_source'] = 'none'  # 'direct' or 'context'

        # Sort by datetime to ensure proper sequence
        df = df.sort_values('datetime').reset_index(drop=True)

        # Only analyze text messages
        text_mask = df['type'] == 'text'

        if context_aware:
            # Use bidirectional context for better accuracy
            self._analyze_bidirectional_context(df, text_mask, reset_gap_hours)
        else:
            # Simple per-message classification
            for idx in df[text_mask].index:
                message = df.loc[idx, 'message']
                scores = self.classify_text(message)

                for topic, score in scores.items():
                    df.loc[idx, f'topic_{topic}'] = score

                primary_topic, confidence = self.get_primary_topic(message)
                df.loc[idx, 'primary_topic'] = primary_topic
                df.loc[idx, 'topic_confidence'] = confidence
                df.loc[idx, 'topic_source'] = 'direct'

        return df

    def _analyze_with_context(self, df: pd.DataFrame, text_mask: pd.Series,
                               reset_gap_hours: float) -> None:
        """
        Analyze messages with context-aware topic propagation.

        This method modifies the DataFrame in place.

        Args:
            df: DataFrame to modify
            text_mask: Boolean mask for text messages
            reset_gap_hours: Hours of silence before resetting context
        """
        active_topic = 'outros'
        active_confidence = 0.0
        last_message_time = None

        text_indices = df[text_mask].index.tolist()

        for idx in text_indices:
            message = df.loc[idx, 'message']
            current_time = df.loc[idx, 'datetime']

            # Check for time gap - reset context if too long
            if last_message_time is not None:
                gap_hours = (current_time - last_message_time).total_seconds() / 3600
                if gap_hours > reset_gap_hours:
                    active_topic = 'outros'
                    active_confidence = 0.0

            # Classify current message
            scores = self.classify_text(message)
            for topic, score in scores.items():
                df.loc[idx, f'topic_{topic}'] = score

            direct_topic, direct_confidence = self.get_primary_topic(message)

            # Decide: use direct classification or inherit from context
            if direct_topic != 'outros' and direct_confidence > 0:
                # Message has clear topic - update active topic
                df.loc[idx, 'primary_topic'] = direct_topic
                df.loc[idx, 'topic_confidence'] = direct_confidence
                df.loc[idx, 'topic_source'] = 'direct'
                active_topic = direct_topic
                active_confidence = direct_confidence
            else:
                # No clear topic - inherit from context
                df.loc[idx, 'primary_topic'] = active_topic
                df.loc[idx, 'topic_confidence'] = active_confidence * 0.8  # Decay confidence
                df.loc[idx, 'topic_source'] = 'context' if active_topic != 'outros' else 'none'

            last_message_time = current_time

    def _analyze_bidirectional_context(self, df: pd.DataFrame, text_mask: pd.Series,
                                        reset_gap_hours: float) -> None:
        """
        Two-pass context analysis: forward then backward propagation.

        This improves accuracy by allowing topic keywords found later
        in a conversation to influence earlier ambiguous messages.

        Args:
            df: DataFrame to modify
            text_mask: Boolean mask for text messages
            reset_gap_hours: Hours of silence before resetting context
        """
        text_indices = df[text_mask].index.tolist()

        # First pass: classify all messages directly
        direct_topics = {}
        for idx in text_indices:
            message = df.loc[idx, 'message']
            scores = self.classify_text(message)
            for topic, score in scores.items():
                df.loc[idx, f'topic_{topic}'] = score
            direct_topic, direct_conf = self.get_primary_topic(message)
            direct_topics[idx] = (direct_topic, direct_conf)

        # Second pass: forward propagation with context
        active_topic = 'outros'
        active_confidence = 0.0
        last_time = None
        forward_topics = {}

        for idx in text_indices:
            current_time = df.loc[idx, 'datetime']

            # Reset on time gap
            if last_time is not None:
                gap = (current_time - last_time).total_seconds() / 3600
                if gap > reset_gap_hours:
                    active_topic = 'outros'
                    active_confidence = 0.0

            direct_topic, direct_conf = direct_topics[idx]

            if direct_topic != 'outros' and direct_conf > 0:
                active_topic = direct_topic
                active_confidence = direct_conf
                forward_topics[idx] = (direct_topic, direct_conf, 'direct')
            else:
                forward_topics[idx] = (active_topic, active_confidence * 0.9, 'context')

            last_time = current_time

        # Third pass: backward propagation to fill early gaps
        active_topic = 'outros'
        active_confidence = 0.0
        last_time = None

        for idx in reversed(text_indices):
            current_time = df.loc[idx, 'datetime']

            if last_time is not None:
                gap = (last_time - current_time).total_seconds() / 3600
                if gap > reset_gap_hours:
                    active_topic = 'outros'
                    active_confidence = 0.0

            direct_topic, direct_conf = direct_topics[idx]
            fwd_topic, fwd_conf, fwd_source = forward_topics[idx]

            if direct_topic != 'outros' and direct_conf > 0:
                active_topic = direct_topic
                active_confidence = direct_conf

            # If forward pass left it as 'outros' but backward has context, use backward
            if fwd_topic == 'outros' and active_topic != 'outros':
                df.loc[idx, 'primary_topic'] = active_topic
                df.loc[idx, 'topic_confidence'] = active_confidence * 0.8
                df.loc[idx, 'topic_source'] = 'context_backward'
            else:
                df.loc[idx, 'primary_topic'] = fwd_topic
                df.loc[idx, 'topic_confidence'] = fwd_conf
                df.loc[idx, 'topic_source'] = fwd_source

            last_time = current_time

    def get_topics_by_sender(self, df: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """
        Get topic distribution per sender.

        Args:
            df: DataFrame with topic columns

        Returns:
            Dictionary mapping sender to topic percentages
        """
        text_df = df[df['type'] == 'text']
        results = {}

        for sender in df['sender'].unique():
            sender_df = text_df[text_df['sender'] == sender]
            topic_counts = sender_df['primary_topic'].value_counts()
            total = len(sender_df)

            if total > 0:
                results[sender] = {
                    topic: (count / total * 100)
                    for topic, count in topic_counts.items()
                }
            else:
                results[sender] = {}

        return results

    def get_topics_over_time(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Get monthly topic distribution trends.

        Args:
            df: DataFrame with topic columns

        Returns:
            DataFrame with monthly topic counts
        """
        text_df = df[df['type'] == 'text'].copy()
        text_df['month_period'] = text_df['datetime'].dt.to_period('M')

        # Get counts per topic per month
        monthly_data = []

        for period in text_df['month_period'].unique():
            period_df = text_df[text_df['month_period'] == period]
            topic_counts = period_df['primary_topic'].value_counts()

            row = {'month_period': period}
            for topic in list(self.topics.keys()) + ['outros']:
                row[topic] = topic_counts.get(topic, 0)

            monthly_data.append(row)

        return pd.DataFrame(monthly_data).sort_values('month_period')

    def get_overall_topic_distribution(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Get overall topic distribution across all messages.

        Args:
            df: DataFrame with topic columns

        Returns:
            Dictionary mapping topics to percentages
        """
        text_df = df[df['type'] == 'text']
        topic_counts = text_df['primary_topic'].value_counts()
        total = len(text_df)

        if total > 0:
            return {
                topic: (count / total * 100)
                for topic, count in topic_counts.items()
            }
        return {}

    def get_conversation_topics(self, df: pd.DataFrame, gap_minutes: int = 30) -> pd.DataFrame:
        """
        Group messages into conversations and classify each conversation.

        Args:
            df: DataFrame with messages
            gap_minutes: Minutes of silence to consider a new conversation

        Returns:
            DataFrame with conversation-level topic classification
        """
        df = df.sort_values('datetime').copy()

        # Identify conversation boundaries
        df['time_diff'] = df['datetime'].diff().dt.total_seconds() / 60
        df['new_conversation'] = df['time_diff'] > gap_minutes
        df['conversation_id'] = df['new_conversation'].cumsum()

        # Aggregate by conversation
        conversations = []
        for conv_id, conv_df in df.groupby('conversation_id'):
            text_msgs = conv_df[conv_df['type'] == 'text']
            if len(text_msgs) == 0:
                continue

            # Combine all text for classification
            combined_text = ' '.join(text_msgs['message'].astype(str).tolist())
            topic, confidence = self.get_primary_topic(combined_text)

            conversations.append({
                'conversation_id': conv_id,
                'start_time': conv_df['datetime'].min(),
                'end_time': conv_df['datetime'].max(),
                'message_count': len(conv_df),
                'participants': list(conv_df['sender'].unique()),
                'primary_topic': topic,
                'topic_confidence': confidence,
            })

        return pd.DataFrame(conversations)

    def get_conversation_metrics(self, df: pd.DataFrame, gap_minutes: int = 30) -> Dict:
        """
        Get conversation-level metrics grouped by topic.

        Args:
            df: DataFrame with messages
            gap_minutes: Minutes of silence to consider a new conversation

        Returns:
            Dictionary with conversation count, avg length, avg duration by topic
        """
        conversations = self.get_conversation_topics(df, gap_minutes)

        if len(conversations) == 0:
            return {}

        # Calculate duration in minutes for each conversation
        conversations['duration_minutes'] = (
            (conversations['end_time'] - conversations['start_time']).dt.total_seconds() / 60
        )

        metrics = {}
        for topic in list(self.topics.keys()) + ['outros']:
            topic_convs = conversations[conversations['primary_topic'] == topic]
            if len(topic_convs) > 0:
                metrics[topic] = {
                    'conversation_count': len(topic_convs),
                    'avg_message_count': topic_convs['message_count'].mean(),
                    'avg_duration_minutes': topic_convs['duration_minutes'].mean(),
                    'total_messages': topic_convs['message_count'].sum(),
                }

        return metrics

    def get_topic_initiators(self, df: pd.DataFrame, gap_minutes: int = 30) -> Dict:
        """
        Analyze who initiates conversations for each topic.

        Args:
            df: DataFrame with messages
            gap_minutes: Minutes of silence to consider a new conversation

        Returns:
            Dictionary mapping topic to initiator stats
        """
        df = df.sort_values('datetime').copy()

        # Identify conversation boundaries
        df['time_diff'] = df['datetime'].diff().dt.total_seconds() / 60
        df['new_conversation'] = (df['time_diff'] > gap_minutes) | (df['time_diff'].isna())

        # Get first message of each conversation
        conv_starts = df[df['new_conversation']].copy()

        # For each conversation start, find the topic of that conversation
        # Use a window of messages after the start to determine topic
        results = {}
        participants = df['sender'].unique().tolist()

        for topic in list(self.topics.keys()) + ['outros']:
            results[topic] = {
                'total_initiations': 0,
                'by_sender': {p: 0 for p in participants}
            }

        # Assign conversation IDs
        df['conversation_id'] = df['new_conversation'].cumsum()

        # Get topic for each conversation and who started it
        for conv_id in df['conversation_id'].unique():
            conv_df = df[df['conversation_id'] == conv_id]
            text_msgs = conv_df[conv_df['type'] == 'text']

            if len(text_msgs) == 0:
                continue

            # Get who started the conversation
            initiator = conv_df.iloc[0]['sender']

            # Classify the conversation topic
            combined_text = ' '.join(text_msgs['message'].astype(str).tolist())
            topic, _ = self.get_primary_topic(combined_text)

            results[topic]['total_initiations'] += 1
            if initiator in results[topic]['by_sender']:
                results[topic]['by_sender'][initiator] += 1

        # Calculate percentages
        for topic in results:
            total = results[topic]['total_initiations']
            if total > 0:
                results[topic]['percentages'] = {
                    sender: (count / total * 100)
                    for sender, count in results[topic]['by_sender'].items()
                }
            else:
                results[topic]['percentages'] = {p: 0 for p in participants}

        return results

    def get_topic_evolution_yearly(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Get topic distribution breakdown by year.

        Args:
            df: DataFrame with topic columns

        Returns:
            DataFrame with yearly topic distribution (percentages)
        """
        text_df = df[df['type'] == 'text'].copy()

        if 'primary_topic' not in text_df.columns:
            return pd.DataFrame()

        yearly_data = []
        for year in sorted(text_df['year'].unique()):
            year_df = text_df[text_df['year'] == year]
            total = len(year_df)

            if total == 0:
                continue

            row = {'year': year, 'total_messages': total}
            topic_counts = year_df['primary_topic'].value_counts()

            for topic in list(self.topics.keys()) + ['outros']:
                count = topic_counts.get(topic, 0)
                row[f'{topic}_count'] = count
                row[f'{topic}_pct'] = (count / total * 100)

            yearly_data.append(row)

        return pd.DataFrame(yearly_data)
