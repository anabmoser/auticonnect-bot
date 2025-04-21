"""
Main module for AutiConnect Telegram Bot with AI mediators.
Handles all bot commands, conversation flows, and AI-mediated interactions.
"""

import os
import logging
import json
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from telegram.ext import (
    Updater, CommandHandler, MessageHandler, Filters, 
    ConversationHandler, CallbackQueryHandler, CallbackContext
)
from dotenv import load_dotenv
from db import Database
from llm_integration import LLMIntegration

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Initialize database
db = Database()

# Initialize LLM integration
llm = LLMIntegration(db)

# Conversation states
NAME, ROLE, GROUP_NAME, GROUP_THEME, GROUP_DESC, GROUP_MAX = range(6)
ACTIVITY_TYPE, ACTIVITY_TITLE, ACTIVITY_DESC, ACTIVITY_DURATION = range(6, 10)
PROFILE_AGE, PROFILE_GENDER, PROFILE_CONTACTS, PROFILE_ACADEMIC, PROFILE_PROFESSIONALS = range(10, 15)
PROFILE_INTERESTS, PROFILE_TRIGGERS, PROFILE_COMMUNICATION = range(15, 18)

# Global variables
group_message_timestamps = {}  # Track last AI intervention in groups
private_chat_sessions = {}  # Track active private support sessions

def start(update: Update, context: CallbackContext) -> int:
    """
    Start command handler. Initiates user registration if not registered.
    
    Args:
        update: Update object from Telegram
        context: CallbackContext object from Telegram
        
    Returns:
        int: Next conversation state
    """
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if user:
        # User already registered
        update.message.reply_text(
            f"Olá, {user['name']}! Bem-vindo de volta ao AutiConnect Bot.\n\n"
            f"O que você gostaria de fazer hoje?\n\n"
            f"Use /grupos para ver grupos disponíveis\n"
            f"Use /atividades para ver atividades programadas\n"
            f"Use /perfil para atualizar seu perfil"
        )
        return ConversationHandler.END
    
    # New user registration
    update.message.reply_text(
        "Olá! Sou o AutiConnect Bot. Estou aqui para ajudar pessoas autistas "
        "a interagirem em um ambiente seguro e estruturado.\n\n"
        "Vamos criar seu perfil. Qual é o seu nome?"
    )
    return NAME

def process_name(update: Update, context: CallbackContext) -> int:
    """
    Process user's name input and ask for role.
    
    Args:
        update: Update object from Telegram
        context: CallbackContext object from Telegram
        
    Returns:
        int: Next conversation state
    """
    context.user_data['name'] = update.message.text
    
    keyboard = [
        [InlineKeyboardButton("Pessoa Autista", callback_data='autista')],
        [InlineKeyboardButton("Auxiliar Terapêutico (AT)", callback_data='at')]
    ]
    
    update.message.reply_text(
        f"Obrigado, {context.user_data['name']}.\n\n"
        f"Você é uma pessoa autista ou um Auxiliar Terapêutico (AT)?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return ROLE

def process_role(update: Update, context: CallbackContext) -> int:
    """
    Process user's role selection and complete registration or continue profile setup.
    
    Args:
        update: Update object from Telegram
        context: CallbackContext object from Telegram
        
    Returns:
        int: Next conversation state
    """
    query = update.callback_query
    query.answer()
    
    user_id = update.effective_user.id
    role = query.data
    name = context.user_data['name']
    
    # Save basic user info to database
    success = db.create_user(user_id, name, role)
    
    if not success:
        query.edit_message_text(
            "Desculpe, ocorreu um erro ao criar seu perfil. "
            "Por favor, tente novamente com /start."
        )
        return ConversationHandler.END
    
    # For autistic users, continue with expanded profile setup
    if role == 'autista':
        query.edit_message_text(
            f"Perfil básico criado, {name}! Agora vamos personalizar seu perfil "
            f"para que possamos oferecer uma experiência melhor adaptada às suas necessidades.\n\n"
            f"Qual é a sua idade? (Digite apenas o número)"
        )
        return PROFILE_AGE
    else:  # AT
        query.edit_message_text(
            f"Perfil de AT criado com sucesso, {name}!\n\n"
            f"Como Auxiliar Terapêutico, você pode:\n"
            f"• Ver grupos disponíveis com /grupos\n"
            f"• Ver atividades programadas com /atividades\n"
            f"• Criar novos grupos com /criar_grupo\n"
            f"• Iniciar atividades estruturadas com /iniciar_atividade\n\n"
            f"Seu papel é fundamental para supervisionar os agentes de IA e "
            f"intervir quando necessário."
        )
        return ConversationHandler.END

def process_profile_age(update: Update, context: CallbackContext) -> int:
    """
    Process user's age input and ask for gender.
    
    Args:
        update: Update object from Telegram
        context: CallbackContext object from Telegram
        
    Returns:
        int: Next conversation state
    """
    try:
        age = int(update.message.text)
        if age < 5 or age > 100:
            update.message.reply_text(
                "Por favor, digite uma idade válida entre 5 e 100 anos."
            )
            return PROFILE_AGE
    except ValueError:
        update.message.reply_text(
            "Por favor, digite apenas números para sua idade."
        )
        return PROFILE_AGE
    
    # Store in context for later database update
    context.user_data['profile_age'] = age
    
    # Ask for gender
    keyboard = [
        [InlineKeyboardButton("Masculino", callback_data='masculino')],
        [InlineKeyboardButton("Feminino", callback_data='feminino')],
        [InlineKeyboardButton("Não-binário", callback_data='nao-binario')],
        [InlineKeyboardButton("Prefiro não informar", callback_data='nao-informado')]
    ]
    
    update.message.reply_text(
        "Obrigado! Qual é o seu gênero?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return PROFILE_GENDER

def process_profile_gender(update: Update, context: CallbackContext) -> int:
    """
    Process user's gender selection and ask for emergency contacts.
    
    Args:
        update: Update object from Telegram
        context: CallbackContext object from Telegram
        
    Returns:
        int: Next conversation state
    """
    query = update.callback_query
    query.answer()
    
    gender = query.data
    context.user_data['profile_gender'] = gender
    
    query.edit_message_text(
        "Obrigado! Agora, por favor, forneça contatos de emergência (pais, responsáveis ou cuidadores).\n\n"
        "Digite no formato: Nome - Relação - Telefone\n"
        "Exemplo: Maria Silva - Mãe - (11) 98765-4321\n\n"
        "Você pode adicionar múltiplos contatos, um por linha."
    )
    return PROFILE_CONTACTS

def process_profile_contacts(update: Update, context: CallbackContext) -> int:
    """
    Process user's emergency contacts and ask for academic history.
    
    Args:
        update: Update object from Telegram
        context: CallbackContext object from Telegram
        
    Returns:
        int: Next conversation state
    """
    contacts_text = update.message.text
    contacts = [contact.strip() for contact in contacts_text.split('\n') if contact.strip()]
    context.user_data['profile_contacts'] = contacts
    
    update.message.reply_text(
        "Obrigado! Agora, conte-nos brevemente sobre seu histórico acadêmico.\n"
        "Por exemplo: escolas que frequentou, nível de escolaridade, etc."
    )
    return PROFILE_ACADEMIC

def process_profile_academic(update: Update, context: CallbackContext) -> int:
    """
    Process user's academic history and ask for professionals.
    
    Args:
        update: Update object from Telegram
        context: CallbackContext object from Telegram
        
    Returns:
        int: Next conversation state
    """
    academic_history = update.message.text
    context.user_data['profile_academic'] = academic_history
    
    update.message.reply_text(
        "Obrigado! Agora, por favor, liste os profissionais com quem você já trabalhou "
        "ou trabalha atualmente (terapeutas, psicólogos, etc.).\n\n"
        "Digite no formato: Nome - Especialidade\n"
        "Exemplo: Dr. João - Psicólogo\n\n"
        "Você pode adicionar múltiplos profissionais, um por linha."
    )
    return PROFILE_PROFESSIONALS

def process_profile_professionals(update: Update, context: CallbackContext) -> int:
    """
    Process user's professionals and ask for interests.
    
    Args:
        update: Update object from Telegram
        context: CallbackContext object from Telegram
        
    Returns:
        int: Next conversation state
    """
    professionals_text = update.message.text
    professionals = [prof.strip() for prof in professionals_text.split('\n') if prof.strip()]
    context.user_data['profile_professionals'] = professionals
    
    update.message.reply_text(
        "Obrigado! Agora, conte-nos sobre seus interesses especiais, hobbies ou tópicos favoritos.\n"
        "Isso nos ajudará a sugerir grupos e atividades relevantes para você.\n\n"
        "Por favor, liste seus interesses separados por vírgulas."
    )
    return PROFILE_INTERESTS

def process_profile_interests(update: Update, context: CallbackContext) -> int:
    """
    Process user's interests and ask for anxiety triggers.
    
    Args:
        update: Update object from Telegram
        context: CallbackContext object from Telegram
        
    Returns:
        int: Next conversation state
    """
    interests_text = update.message.text
    interests = [interest.strip() for interest in interests_text.split(',') if interest.strip()]
    context.user_data['profile_interests'] = interests
    
    update.message.reply_text(
        "Obrigado! Para nos ajudar a criar um ambiente confortável, "
        "poderia nos informar sobre gatilhos conhecidos de ansiedade ou desconforto?\n\n"
        "Por exemplo: barulhos altos, interrupções frequentes, certos tópicos, etc.\n"
        "Por favor, liste-os separados por vírgulas."
    )
    return PROFILE_TRIGGERS

def process_profile_triggers(update: Update, context: CallbackContext) -> int:
    """
    Process user's anxiety triggers and ask for communication preferences.
    
    Args:
        update: Update object from Telegram
        context: CallbackContext object from Telegram
        
    Returns:
        int: Next conversation state
    """
    triggers_text = update.message.text
    triggers = [trigger.strip() for trigger in triggers_text.split(',') if trigger.strip()]
    context.user_data['profile_triggers'] = triggers
    
    # Ask for communication preferences
    keyboard = [
        [InlineKeyboardButton("Direta e objetiva", callback_data='direta')],
        [InlineKeyboardButton("Detalhada e explicativa", callback_data='detalhada')]
    ]
    
    update.message.reply_text(
        "Quase terminando! Como você prefere que nos comuniquemos com você?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return PROFILE_COMMUNICATION

def process_profile_communication(update: Update, context: CallbackContext) -> int:
    """
    Process user's communication preferences and complete profile setup.
    
    Args:
        update: Update object from Telegram
        context: CallbackContext object from Telegram
        
    Returns:
        int: Next conversation state
    """
    query = update.callback_query
    query.answer()
    
    comm_style = query.data
    context.user_data['profile_communication'] = comm_style
    
    user_id = update.effective_user.id
    
    # Update user profile in database
    profile_data = {
        "age": context.user_data.get('profile_age'),
        "gender": context.user_data.get('profile_gender'),
        "emergency_contacts": context.user_data.get('profile_contacts', []),
        "academic_history": context.user_data.get('profile_academic', ''),
        "professionals": context.user_data.get('profile_professionals', []),
        "interests": context.user_data.get('profile_interests', []),
        "anxiety_triggers": context.user_data.get('profile_triggers', []),
        "communication_preferences": {
            "style": context.user_data.get('profile_communication', 'direta')
        }
    }
    
    success = db.update_user_profile(user_id, profile_data)
    
    if success:
        query.edit_message_text(
            f"Perfil completo criado com sucesso!\n\n"
            f"Agora você pode:\n"
            f"• Ver grupos disponíveis com /grupos\n"
            f"• Ver atividades programadas com /atividades\n\n"
            f"Nossos agentes de IA estão disponíveis 24/7 para ajudar nas interações "
            f"e oferecer suporte quando necessário. Se precisar de ajuda individual, "
            f"você pode iniciar uma conversa privada a qualquer momento."
        )
    else:
        query.edit_message_text(
            "Desculpe, ocorreu um erro ao salvar seu perfil completo. "
            "No entanto, seu perfil básico foi criado e você pode começar a usar o bot. "
            "Você pode atualizar seu perfil mais tarde com o comando /perfil."
        )
    
    return ConversationHandler.END

def update_profile_command(update: Update, context: CallbackContext) -> int:
    """
    Command to update user profile.
    
    Args:
        update: Update object from Telegram
        context: CallbackContext object from Telegram
        
    Returns:
        int: Next conversation state
    """
    user_id = update.effective_user.id
    user = db.get_user(user_id)
    
    if not user:
        update.message.reply_text(
            "Você precisa se registrar primeiro. Use /start para criar seu perfil."
        )
        return ConversationHandler.END
    
    # For autistic users, offer profile update options
    if user.get('role') == 'autista':
        keyboard = [
            [InlineKeyboardButton("Interesses", callback_data='update_interests')],
            [InlineKeyboardButton("Gatilhos de ansiedade", callback_data='update_triggers')],
            [InlineKeyboardButton("Preferências de comunicação", callback_data='update_communication')],
            [InlineKeyboardButton("Contatos de emergência", callback_data='update_contacts')]
        ]
        
        update.message.reply_text(
            f"Olá, {user['name']}! O que você gostaria de atualizar em seu perfil?",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return PROFILE_INTERESTS
    else:
        update.message.reply_text(
            f"Olá, {user['name']}! Como AT, seu perfil é mais simples e não requer atualizações adicionais."
        )
        return ConversationHandler.END

def list_groups(update: Update, context: CallbackContext) -> None:
    """
    List all available thematic groups.
    
    Args:
        update: Update object from Telegram
        context: CallbackContext object from Telegram
    """
    user_id = update.effective_user.id
    db.update_last_active(user_id)
    
    groups = db.get_all_groups()
    
    if not groups:
        update.message.reply_text(
            "Não há grupos disponíveis no momento.\n\n"
            "Se você é um AT, pode criar um novo grupo com /criar_grupo."
        )
        return
    
    message = "📋 *Grupos Disponíveis:*\n\n"
    
    for group in groups:
        members_count = len(group.get('members', []))
        max_members = group.get('max_members', 10)
        
        # Get AT name
        at_id = group.get('created_by')
        at = db.get_user(at_id)
        at_name = a
(Content truncated due to size limit. Use line ranges to read in chunks)