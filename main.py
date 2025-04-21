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

# Importar os módulos adicionais
from user_profile import (
    process_profile_age, process_profile_gender, process_profile_contacts,
    process_profile_academic, process_profile_professionals, process_profile_interests,
    process_profile_triggers, process_profile_communication, update_profile_command
)

from group_management import (
    list_groups, join_group_callback, create_group_start, process_group_name,
    process_group_theme, process_group_desc, process_group_max, toggle_ai_mediator
)

from activity_management import (
    list_activities, start_activity_command, process_activity_group,
    process_activity_type, process_activity_title, process_activity_desc,
    process_activity_duration, toggle_ai_guidance
)

from ai_mediation import (
    handle_group_message, handle_private_message, should_ai_intervene, needs_support
)

def help_command(update: Update, context: CallbackContext) -> None:
    """
    Display help information about available commands.
    
    Args:
        update: Update object from Telegram
        context: CallbackContext object from Telegram
    """
    user_id = update.effective_user.id
    db.update_last_active(user_id)
    
    user = db.get_user(user_id)
    
    if not user:
        # Basic help for unregistered users
        update.message.reply_text(
            "🤖 *AutiConnect Bot - Ajuda*\n\n"
            "Este bot ajuda pessoas autistas a interagirem em um ambiente seguro e estruturado, "
            "com mediação de agentes de IA disponíveis 24/7.\n\n"
            "*Comandos disponíveis:*\n"
            "/start - Iniciar o bot e criar seu perfil\n"
            "/ajuda - Mostrar esta mensagem de ajuda\n\n"
            "Por favor, use /start para criar seu perfil primeiro.",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    
    # Help message based on user role
    if user.get('role') == 'at':
        # Help for ATs
        update.message.reply_text(
            "🤖 *AutiConnect Bot - Ajuda para ATs*\n\n"
            "*Comandos disponíveis:*\n"
            "/start - Iniciar o bot\n"
            "/ajuda - Mostrar esta mensagem de ajuda\n"
            "/grupos - Listar grupos disponíveis\n"
            "/atividades - Ver atividades programadas\n"
            "/criar_grupo - Criar um novo grupo temático\n"
            "/iniciar_atividade - Iniciar uma atividade estruturada\n\n"
            "Como AT, você supervisiona os agentes de IA e intervém quando necessário. "
            "Você receberá alertas quando situações potencialmente problemáticas "
            "forem detectadas pelos agentes de IA.",
            parse_mode=ParseMode.MARKDOWN
        )
    else:
        # Help for autistic users
        update.message.reply_text(
            "🤖 *AutiConnect Bot - Ajuda*\n\n"
            "*Comandos disponíveis:*\n"
            "/start - Iniciar o bot\n"
            "/ajuda - Mostrar esta mensagem de ajuda\n"
            "/grupos - Listar grupos disponíveis\n"
            "/atividades - Ver atividades programadas\n"
            "/perfil - Atualizar seu perfil\n\n"
            "Você pode conversar diretamente com o assistente de IA a qualquer momento "
            "para obter suporte individual. Os agentes de IA também estão presentes nos "
            "grupos para facilitar conversas e atividades.",
            parse_mode=ParseMode.MARKDOWN
        )

def cancel(update: Update, context: CallbackContext) -> int:
    """
    Cancel current conversation.
    
    Args:
        update: Update object from Telegram
        context: CallbackContext object from Telegram
        
    Returns:
        int: ConversationHandler.END
    """
    update.message.reply_text(
        "Operação cancelada. O que você gostaria de fazer agora?\n\n"
        "Use /grupos para ver grupos disponíveis\n"
        "Use /atividades para ver atividades programadas"
    )
    return ConversationHandler.END

def error_handler(update: Update, context: CallbackContext) -> None:
    """
    Handle errors in the dispatcher.
    
    Args:
        update: Update object from Telegram
        context: CallbackContext object from Telegram
    """
    logger.error(f"Update {update} caused error {context.error}")
    
    # Send message to user
    if update and update.effective_message:
        update.effective_message.reply_text(
            "Desculpe, ocorreu um erro ao processar seu comando. "
            "Por favor, tente novamente mais tarde."
        )

def main() -> None:
    """Start the bot."""
    # Get bot token from environment variable
    token = os.environ.get('BOT_TOKEN')
    if not token:
        logger.error("BOT_TOKEN environment variable not set")
        return
    
    # Create the Updater
    updater = Updater(token)
    
    # Get the dispatcher
    dispatcher = updater.dispatcher
    
    # Registration conversation handler
    registration_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start)],
        states={
            NAME: [MessageHandler(Filters.text & ~Filters.command, process_name)],
            ROLE: [CallbackQueryHandler(process_role)],
            PROFILE_AGE: [MessageHandler(Filters.text & ~Filters.command, process_profile_age)],
            PROFILE_GENDER: [CallbackQueryHandler(process_profile_gender)],
            PROFILE_CONTACTS: [MessageHandler(Filters.text & ~Filters.command, process_profile_contacts)],
            PROFILE_ACADEMIC: [MessageHandler(Filters.text & ~Filters.command, process_profile_academic)],
            PROFILE_PROFESSIONALS: [MessageHandler(Filters.text & ~Filters.command, process_profile_professionals)],
            PROFILE_INTERESTS: [MessageHandler(Filters.text & ~Filters.command, process_profile_interests)],
            PROFILE_TRIGGERS: [MessageHandler(Filters.text & ~Filters.command, process_profile_triggers)],
            PROFILE_COMMUNICATION: [CallbackQueryHandler(process_profile_communication)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    # Profile update conversation handler
    profile_update_handler = ConversationHandler(
        entry_points=[CommandHandler('perfil', update_profile_command)],
        states={
            PROFILE_INTERESTS: [CallbackQueryHandler(lambda u, c: PROFILE_INTERESTS)],
            # Additional states would be implemented in a full version
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    # Group creation conversation handler
    group_creation_handler = ConversationHandler(
        entry_points=[CommandHandler('criar_grupo', create_group_start)],
        states={
            GROUP_NAME: [MessageHandler(Filters.text & ~Filters.command, process_group_name)],
            GROUP_THEME: [MessageHandler(Filters.text & ~Filters.command, process_group_theme)],
            GROUP_DESC: [MessageHandler(Filters.text & ~Filters.command, process_group_desc)],
            GROUP_MAX: [MessageHandler(Filters.text & ~Filters.command, process_group_max)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    # Activity creation conversation handler
    activity_creation_handler = ConversationHandler(
        entry_points=[CommandHandler('iniciar_atividade', start_activity_command)],
        states={
            ACTIVITY_TYPE: [CallbackQueryHandler(process_activity_group, pattern=r'^group_')],
            ACTIVITY_TITLE: [CallbackQueryHandler(process_activity_type, pattern=r'^type_')],
            ACTIVITY_DESC: [MessageHandler(Filters.text & ~Filters.command, process_activity_title)],
            ACTIVITY_DURATION: [MessageHandler(Filters.text & ~Filters.command, process_activity_desc)]
        },
        fallbacks=[CommandHandler('cancel', cancel)]
    )
    
    # Add handlers to dispatcher
    dispatcher.add_handler(registration_handler)
    dispatcher.add_handler(profile_update_handler)
    dispatcher.add_handler(group_creation_handler)
    dispatcher.add_handler(activity_creation_handler)
    dispatcher.add_handler(CommandHandler('grupos', list_groups))
    dispatcher.add_handler(CommandHandler('atividades', list_activities))
    dispatcher.add_handler(CommandHandler('ajuda', help_command))
    
    # Callback query handlers
    dispatcher.add_handler(CallbackQueryHandler(join_group_callback, pattern=r'^join_'))
    dispatcher.add_handler(CallbackQueryHandler(toggle_ai_mediator, pattern=r'^ai_(on|off)_'))
    dispatcher.add_handler(CallbackQueryHandler(toggle_ai_guidance, pattern=r'^ai_guide_(on|off)_'))
    
    # Message handlers
    dispatcher.add_handler(MessageHandler(
        Filters.text & ~Filters.command & Filters.chat_type.groups, 
        handle_group_message
    ))
    dispatcher.add_handler(MessageHandler(
        Filters.text & ~Filters.command & Filters.chat_type.private, 
        handle_private_message
    ))
    
    # Add error handler
    dispatcher.add_error_handler(error_handler)
    
    # Start the Bot
    updater.start_polling()
    logger.info("Bot started with AI mediators enabled")
    
    # Run the bot until the user presses Ctrl-C
    updater.idle()

if __name__ == '__main__':
    main()
