"""
LLM Integration module for AutiConnect Telegram Bot.
Handles interactions with LLM APIs for AI-mediated conversations.
"""

import os
import json
import logging
from datetime import datetime
import requests

class LLMIntegration:
    def __init__(self, db):
        """
        Initialize LLM integration with database connection.
        
        Args:
            db: Database instance for storing and retrieving data
        """
        self.db = db
        self.api_key = os.environ.get('LLM_API_KEY')
        self.api_endpoint = os.environ.get('LLM_API_ENDPOINT', 'https://api.openai.com/v1/chat/completions')
        self.model = os.environ.get('LLM_MODEL', 'gpt-4')
        self.alert_threshold = int(os.environ.get('ALERT_THRESHOLD', 70))
        
        # Load prompt templates
        try:
            with open('prompt_templates.json', 'r', encoding='utf-8') as f:
                self.templates = json.load(f)
        except Exception as e:
            logging.error(f"Error loading prompt templates: {e}")
            # Fallback to basic templates
            self.templates = {
                "group_mediation": "Você é um mediador de IA para um grupo de pessoas autistas. Seu objetivo é facilitar a conversa de forma respeitosa e inclusiva.",
                "individual_support": "Você é um assistente de IA para pessoas autistas. Seu objetivo é oferecer suporte emocional e ajudar com estratégias de regulação.",
                "activity_guidance": "Você é um guia de IA para atividades estruturadas. Seu objetivo é ajudar a manter o foco e garantir que todos participem."
            }
    
    def mediate_group_conversation(self, group_id, recent_messages, current_user_id):
        """
        Generate AI mediator response for group conversation.
        
        Args:
            group_id (int): Telegram group ID
            recent_messages (list): Recent messages in the group
            current_user_id (int): User ID of the message sender
            
        Returns:
            tuple: (AI response text, whether professional alert is needed)
        """
        try:
            # Get group information
            group = self.db.get_group(group_id)
            if not group:
                return None, False
            
            # Get user information for all participants in recent messages
            user_ids = set(msg.get('user_id') for msg in recent_messages)
            users = {}
            for user_id in user_ids:
                user = self.db.get_user(user_id)
                if user:
                    users[user_id] = user
            
            # Prepare conversation history for prompt
            conversation = []
            for msg in reversed(recent_messages):  # Oldest first
                user_id = msg.get('user_id')
                user = users.get(user_id, {"name": "Desconhecido", "role": "unknown"})
                
                conversation.append({
                    "role": "user" if user.get('role') == 'autista' else "assistant" if user.get('role') == 'at' else "user",
                    "name": user.get('name', 'Desconhecido'),
                    "content": msg.get('text', '')
                })
            
            # Get AI mediator settings
            settings = group.get('ai_mediator_settings', {})
            intervention_frequency = settings.get('intervention_frequency', 'medium')
            
            # Prepare prompt
            base_prompt = self.templates.get('group_mediation', "Você é um mediador de IA para um grupo de pessoas autistas.")
            
            # Add group context
            prompt = f"{base_prompt}\n\nGrupo: {group.get('name')}\nTema: {group.get('theme')}\nDescrição: {group.get('description')}\n\n"
            
            # Add information about participants
            prompt += "Participantes:\n"
            for user_id, user in users.items():
                if user.get('role') == 'autista':
                    profile = user.get('profile', {})
                    interests = ", ".join(profile.get('interests', []))
                    triggers = ", ".join(profile.get('anxiety_triggers', []))
                    comm_style = profile.get('communication_preferences', {}).get('style', 'direta')
                    
                    prompt += f"- {user.get('name')}: Pessoa autista. "
                    if interests:
                        prompt += f"Interesses: {interests}. "
                    if triggers:
                        prompt += f"Gatilhos: {triggers}. "
                    prompt += f"Prefere comunicação {comm_style}.\n"
                elif user.get('role') == 'at':
                    prompt += f"- {user.get('name')}: Auxiliar Terapêutico (AT).\n"
                else:
                    prompt += f"- {user.get('name')}: Papel desconhecido.\n"
            
            # Add conversation history
            prompt += "\nConversa recente:\n"
            for msg in conversation:
                prompt += f"{msg['name']}: {msg['content']}\n"
            
            # Add instructions based on settings
            prompt += "\nInstruções:\n"
            prompt += "1. Facilite a conversa de forma respeitosa e inclusiva.\n"
            prompt += "2. Mantenha o foco no tema do grupo quando apropriado.\n"
            prompt += "3. Ajude a incluir participantes que estão em silêncio.\n"
            prompt += "4. Ofereça suporte se alguém parecer confuso ou ansioso.\n"
            
            if settings.get('activity_suggestions', True):
                prompt += "5. Sugira atividades relacionadas ao tema quando apropriado.\n"
            
            if settings.get('conflict_mediation', True):
                prompt += "6. Medeie conflitos ou mal-entendidos de forma construtiva.\n"
            
            # Add specific instructions for intervention frequency
            if intervention_frequency == 'low':
                prompt += "\nIntervenha apenas quando necessário, mantendo-se em segundo plano na maior parte do tempo."
            elif intervention_frequency == 'high':
                prompt += "\nIntervenha proativamente para manter a conversa fluindo e garantir que todos participem."
            else:  # medium
                prompt += "\nMantenha um equilíbrio entre intervir quando necessário e permitir que a conversa flua naturalmente."
            
            # Make API call
            response = self._call_llm_api(prompt)
            
            # Analyze response for potential issues requiring professional attention
            alert_needed = self._analyze_for_alert(response, recent_messages)
            
            # Store interaction for analysis
            self.db.store_ai_interaction(
                interaction_type="group_mediation",
                context={"group_id": group_id, "user_count": len(users)},
                input_data={"prompt": prompt},
                output_data={"response": response, "alert_needed": alert_needed}
            )
            
            return response, alert_needed
        
        except Exception as e:
            logging.error(f"Error in group mediation: {e}")
            return "Desculpe, estou tendo dificuldades para processar a conversa neste momento.", False
    
    def provide_individual_support(self, user_id, message_text):
        """
        Generate AI support response for individual conversation.
        
        Args:
            user_id (int): Telegram user ID
            message_text (str): User's message
            
        Returns:
            tuple: (AI response text, whether professional alert is needed)
        """
        try:
            # Get user information
            user = self.db.get_user(user_id)
            if not user or user.get('role') != 'autista':
                return None, False
            
            # Get recent messages
            recent_messages = self.db.get_recent_messages(user_id=user_id, limit=10)
            
            # Prepare conversation history for prompt
            conversation = []
            for msg in reversed(recent_messages):  # Oldest first
                if msg.get('user_id') == user_id:
                    conversation.append({
                        "role": "user",
                        "content": msg.get('text', '')
                    })
                else:
                    conversation.append({
                        "role": "assistant",
                        "content": msg.get('text', '')
                    })
            
            # Prepare prompt
            base_prompt = self.templates.get('individual_support', "Você é um assistente de IA para pessoas autistas.")
            
            # Add user context
            profile = user.get('profile', {})
            prompt = f"{base_prompt}\n\nUsuário: {user.get('name')}\n"
            
            # Add profile information
            prompt += f"Idade: {profile.get('age', 'Não informada')}\n"
            prompt += f"Gênero: {profile.get('gender', 'Não informado')}\n"
            
            interests = ", ".join(profile.get('interests', []))
            if interests:
                prompt += f"Interesses: {interests}\n"
            
            triggers = ", ".join(profile.get('anxiety_triggers', []))
            if triggers:
                prompt += f"Gatilhos de ansiedade: {triggers}\n"
            
            comm_style = profile.get('communication_preferences', {}).get('style', 'direta')
            prompt += f"Preferência de comunicação: {comm_style}\n"
            
            # Add conversation history
            prompt += "\nConversa recente:\n"
            for msg in conversation:
                role = "Usuário" if msg['role'] == 'user' else "Assistente"
                prompt += f"{role}: {msg['content']}\n"
            
            # Add instructions
            prompt += "\nInstruções:\n"
            prompt += "1. Ofereça suporte emocional e ajude com estratégias de regulação.\n"
            prompt += "2. Adapte sua comunicação ao estilo preferido do usuário.\n"
            prompt += "3. Evite tópicos que possam ser gatilhos de ansiedade.\n"
            prompt += "4. Conecte-se com os interesses do usuário quando apropriado.\n"
            prompt += "5. Seja claro, paciente e respeitoso.\n"
            
            # Make API call
            response = self._call_llm_api(prompt)
            
            # Analyze response for potential issues requiring professional attention
            alert_needed = self._analyze_for_alert(message_text, [])
            
            # Store interaction for analysis
            self.db.store_ai_interaction(
                interaction_type="individual_support",
                context={"user_id": user_id},
                input_data={"prompt": prompt, "message": message_text},
                output_data={"response": response, "alert_needed": alert_needed}
            )
            
            return response, alert_needed
        
        except Exception as e:
            logging.error(f"Error in individual support: {e}")
            return "Desculpe, estou tendo dificuldades para processar sua mensagem neste momento.", False
    
    def guide_activity(self, activity_id, group_id, message_text=None):
        """
        Generate AI guidance for structured activity.
        
        Args:
            activity_id (str): Activity ID
            group_id (int): Telegram group ID
            message_text (str, optional): Context message
            
        Returns:
            tuple: (AI guidance text, whether professional alert is needed)
        """
        # Implementation would be similar to the methods above
        # This is a placeholder for future implementation
        return "Vamos começar esta atividade! Lembrem-se de respeitar o tempo de fala de cada pessoa.", False
    
    def _call_llm_api(self, prompt):
        """
        Call LLM API with prompt.
        
        Args:
            prompt (str): Prompt text
            
        Returns:
            str: LLM response
        """
        try:
            if not self.api_key:
                return "Erro: API_KEY não configurada. Por favor, configure a variável de ambiente LLM_API_KEY."
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": "Por favor, responda como o mediador/assistente de IA."}
                ],
                "temperature": 0.7,
                "max_tokens": 500
            }
            
            response = requests.post(
                self.api_endpoint,
                headers=headers,
                json=data
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['choices'][0]['message']['content']
            else:
                logging.error(f"API error: {response.status_code} - {response.text}")
                return "Desculpe, estou tendo dificuldades técnicas no momento."
        
        except Exception as e:
            logging.error(f"Error calling LLM API: {e}")
            return "Desculpe, ocorreu um erro ao processar sua solicitação."
    
    def _analyze_for_alert(self, text, context_messages=None):
        """
        Analyze text for signs that professional intervention might be needed.
        
        Args:
            text (str): Text to analyze
            context_messages (list, optional): Context messages
            
        Returns:
            bool: Whether professional alert is needed
        """
        # Simple keyword-based analysis
        alert_keywords = [
            'suicídio', 'suicida', 'matar', 'morrer', 'machucar',
            'desespero', 'desesperado', 'desesperada', 'emergência',
            'crise', 'pânico', 'violência', 'abuso', 'socorro'
        ]
        
        # Check for alert keywords
        text_lower = text.lower()
        for keyword in alert_keywords:
            if keyword in text_lower:
                return True
        
        # More sophisticated analysis could be implemented here
        # For now, we'll use a simple approach
        
        return False
