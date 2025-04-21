"""
LLM Integration module for AutiConnect Telegram Bot.
Handles interactions with LLM APIs for AI-mediated conversations.
"""

import os
import json
import logging
from datetime import datetime
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class LLMIntegration:
    def __init__(self, db_instance):
        """
        Initialize LLM integration with database connection.
        
        Args:
            db_instance: Database instance for storing conversation history and user profiles
        """
        self.db = db_instance
        
        # Get API key from environment variable
        self.api_key = os.environ.get('LLM_API_KEY')
        if not self.api_key:
            logger.warning("LLM_API_KEY environment variable not set. LLM integration will not function.")
        
        # LLM API endpoint
        self.api_endpoint = os.environ.get('LLM_API_ENDPOINT', 'https://api.openai.com/v1/chat/completions')
        
        # Default model
        self.model = os.environ.get('LLM_MODEL', 'gpt-4')
        
        # Alert threshold for professional intervention (0-100)
        self.alert_threshold = int(os.environ.get('ALERT_THRESHOLD', '70'))
        
        # Load prompt templates
        self.load_prompt_templates()
    
    def load_prompt_templates(self):
        """Load prompt templates from file or create default ones."""
        try:
            with open('prompt_templates.json', 'r') as f:
                self.prompt_templates = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            # Create default prompt templates
            self.prompt_templates = {
                "system_base": (
                    "Você é um assistente especializado em mediar conversas entre pessoas autistas. "
                    "Seu objetivo é facilitar a comunicação, garantir que todos se sintam incluídos e "
                    "oferecer suporte quando necessário. Você deve ser claro, direto, paciente e evitar "
                    "linguagem ambígua ou figurada. Mantenha um tom calmo e previsível."
                ),
                "group_facilitation": (
                    "Observe a conversa do grupo e intervenha quando: "
                    "1. Houver silêncio prolongado (mais de 5 minutos) "
                    "2. Alguém parecer estar sendo ignorado "
                    "3. A conversa se tornar muito intensa ou confusa "
                    "4. Um tópico de interesse comum surgir que possa ser explorado "
                    "Suas intervenções devem ser gentis e estruturadas."
                ),
                "individual_support": (
                    "Esta é uma conversa privada com uma pessoa autista que pode estar "
                    "enfrentando dificuldades na interação em grupo. Ofereça suporte emocional, "
                    "ajude na regulação e forneça estratégias para lidar com a situação. "
                    "Pergunte se a pessoa gostaria de retornar ao grupo ou prefere continuar "
                    "a conversa individual por enquanto."
                ),
                "activity_guidance": (
                    "Você está facilitando uma atividade estruturada. Forneça instruções claras, "
                    "gerencie os turnos de participação e mantenha o foco no objetivo. "
                    "Ofereça elogios específicos por contribuições e ajude a resumir os pontos principais."
                ),
                "conflict_mediation": (
                    "Detectou-se um potencial conflito ou mal-entendido. Intervenha de forma neutra, "
                    "ajudando a esclarecer as intenções de cada pessoa. Reformule as mensagens de forma "
                    "mais clara se necessário e sugira formas construtivas de continuar a conversa."
                ),
                "professional_alert": (
                    "Analise a situação atual e determine se é necessário alertar um profissional AT. "
                    "Considere: nível de angústia, potencial para escalada de conflito, temas sensíveis "
                    "ou perigosos, e pedidos explícitos de ajuda. Atribua um nível de urgência de 0-100."
                )
            }
            # Save default templates
            with open('prompt_templates.json', 'w') as f:
                json.dump(self.prompt_templates, f, indent=2)
    
    def get_user_context(self, user_id):
        """
        Retrieve user context information for personalized interactions.
        
        Args:
            user_id (int): Telegram user ID
            
        Returns:
            dict: User context information
        """
        user = self.db.get_user(user_id)
        if not user:
            return {"name": "Usuário", "role": "unknown", "interests": [], "history": []}
        
        # Get recent message history (last 10 messages)
        # In a real implementation, this would retrieve from a messages collection
        # For this prototype, we'll return a placeholder
        history = []
        
        return {
            "name": user.get("name", "Usuário"),
            "role": user.get("role", "unknown"),
            "interests": user.get("interests", []),
            "groups": user.get("groups", []),
            "history": history
        }
    
    def get_group_context(self, group_id):
        """
        Retrieve group context information for group-based interactions.
        
        Args:
            group_id (int): Telegram group ID
            
        Returns:
            dict: Group context information
        """
        group = self.db.get_group(group_id)
        if not group:
            return {"name": "Grupo", "theme": "geral", "members": [], "history": []}
        
        # Get member information
        members = []
        for member_id in group.get("members", []):
            user = self.db.get_user(member_id)
            if user:
                members.append({
                    "id": member_id,
                    "name": user.get("name", "Usuário"),
                    "role": user.get("role", "unknown")
                })
        
        # Get recent message history (last 20 messages)
        # In a real implementation, this would retrieve from a messages collection
        # For this prototype, we'll return a placeholder
        history = []
        
        return {
            "name": group.get("name", "Grupo"),
            "theme": group.get("theme", "geral"),
            "description": group.get("description", ""),
            "members": members,
            "history": history
        }
    
    def generate_system_prompt(self, context_type, **kwargs):
        """
        Generate system prompt based on context type and additional parameters.
        
        Args:
            context_type (str): Type of context ('group_facilitation', 'individual_support', etc.)
            **kwargs: Additional parameters for prompt customization
            
        Returns:
            str: Generated system prompt
        """
        base_prompt = self.prompt_templates["system_base"]
        context_prompt = self.prompt_templates.get(context_type, "")
        
        # Add context-specific information
        if context_type == "group_facilitation" and "group" in kwargs:
            group = kwargs["group"]
            context_prompt += f"\n\nVocê está mediando o grupo '{group['name']}' com tema '{group['theme']}'. "
            context_prompt += f"Descrição do grupo: {group['description']}\n"
            context_prompt += f"Há {len(group['members'])} participantes no grupo."
        
        elif context_type == "individual_support" and "user" in kwargs:
            user = kwargs["user"]
            context_prompt += f"\n\nVocê está conversando com {user['name']}. "
            if user.get("interests"):
                context_prompt += f"Seus interesses incluem: {', '.join(user['interests'])}. "
        
        elif context_type == "activity_guidance" and "activity" in kwargs:
            activity = kwargs["activity"]
            context_prompt += f"\n\nVocê está facilitando a atividade '{activity['title']}' "
            context_prompt += f"do tipo '{activity['type']}'. "
            context_prompt += f"Descrição: {activity['description']}\n"
            context_prompt += f"Duração planejada: {activity['duration']} minutos."
        
        # Combine prompts
        full_prompt = f"{base_prompt}\n\n{context_prompt}"
        return full_prompt
    
    def call_llm_api(self, messages, temperature=0.7):
        """
        Call LLM API with prepared messages.
        
        Args:
            messages (list): List of message dictionaries (role, content)
            temperature (float): Temperature parameter for response generation
            
        Returns:
            str: LLM response text
            dict: Full API response
        """
        if not self.api_key:
            logger.error("LLM API key not set. Cannot call API.")
            return "Desculpe, não posso processar sua solicitação no momento.", {}
        
        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": 500
            }
            
            response = requests.post(
                self.api_endpoint,
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                response_data = response.json()
                message_content = response_data['choices'][0]['message']['content']
                return message_content, response_data
            else:
                logger.error(f"API call failed with status {response.status_code}: {response.text}")
                return "Desculpe, ocorreu um erro ao processar sua solicitação.", {}
                
        except Exception as e:
            logger.error(f"Error calling LLM API: {e}")
            return "Desculpe, ocorreu um erro ao processar sua solicitação.", {}
    
    def mediate_group_conversation(self, group_id, recent_messages, current_user_id=None):
        """
        Generate AI mediator response for group conversation.
        
        Args:
            group_id (int): Telegram group ID
            recent_messages (list): List of recent messages in the group
            current_user_id (int, optional): ID of user who just sent a message
            
        Returns:
            str: Mediator response
            bool: Whether professional alert is triggered
        """
        # Get group and user contexts
        group_context = self.get_group_context(group_id)
        
        # Prepare conversation history for LLM
        conversation = []
        for msg in recent_messages:
            user_name = "Desconhecido"
            for member in group_context["members"]:
                if member["id"] == msg["user_id"]:
                    user_name = member["name"]
                    break
            
            conversation.append({
                "role": "user",
                "content": f"{user_name}: {msg['text']}"
            })
        
        # Generate system prompt
        system_prompt = self.generate_system_prompt("group_facilitation", group=group_context)
        
        # Prepare messages for API call
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        # Add conversation history
        messages.extend(conversation)
        
        # Add specific instruction for mediator response
        messages.append({
            "role": "user",
            "content": (
                "Com base na conversa acima, determine se você deve intervir como mediador. "
                "Se sim, forneça uma resposta útil e apropriada. Se não for necessário intervir "
                "ainda, responda apenas com '[OBSERVANDO]'."
            )
        })
        
        # Call LLM API
        response_text, _ = self.call_llm_api(messages)
        
        # Check if intervention is needed
        if response_text.strip() == "[OBSERVANDO]":
            return None, False
        
        # Check if professional alert is needed
        alert_needed = self.check_professional_alert_needed(group_context, recent_messages, response_text)
        
        return response_text, alert_needed
    
    def provide_individual_support(self, user_id, message_text):
        """
        Generate AI support response for individual conversation.
        
        Args:
            user_id (int): Telegram user ID
            message_text (str): User's message text
            
        Returns:
            str: Support response
            bool: Whether professional alert is triggered
        """
        # Get user context
        user_context = self.get_user_context(user_id)
        
        # Generate system prompt
        system_prompt = self.generate_system_prompt("individual_support", user=user_context)
        
        # Prepare messages for API call
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message_text}
        ]
        
        # Call LLM API
        response_text, _ = self.call_llm_api(messages, temperature=0.6)
        
        # Check if professional alert is needed
        alert_needed = self.check_professional_alert_needed(
            {"type": "individual", "user": user_context},
            [{"user_id": user_id, "text": message_text}],
            response_text
        )
        
        return response_text, alert_needed
    
    def guide_activity(self, group_id, activity_id, current_stage, recent_messages):
        """
        Generate AI guidance for structured activity.
        
        Args:
            group_id (int): Telegram group ID
            activity_id (str): Activity ID
            current_stage (str): Current stage of the activity
            recent_messages (list): Recent messages in the activity
            
        Returns:
            str: Activity guidance response
            bool: Whether professional alert is triggered
        """
        # Get group context
        group_context = self.get_group_context(group_id)
        
        # Get activity details (in a real implementation, this would come from the database)
        # For this prototype, we'll create a placeholder
        activity = {
            "id": activity_id,
            "title": "Atividade Estruturada",
            "type": "discussão",
            "description": "Uma discussão temática sobre interesses comuns",
            "duration": 30,
            "stages": ["introdução", "discussão", "conclusão"],
            "current_stage": current_stage
        }
        
        # Generate system prompt
        system_prompt = self.generate_system_prompt("activity_guidance", 
                                                   group=group_context,
                                                   activity=activity)
        
        # Prepare conversation history for LLM
        conversation = []
        for msg in recent_messages:
            user_name = "Desconhecido"
            for member in group_context["members"]:
                if member["id"] == msg["user_id"]:
                    user_name = member["name"]
                    break
            
            conversation.append({
                "role": "user",
                "content": f"{user_name}: {msg['text']}"
            })
        
        # Prepare messages for API call
        messages = [
            {"role": "system", "content": system_prompt}
        ]
        
        #
(Content truncated due to size limit. Use line ranges to read in chunks)