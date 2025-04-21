"""
AI mediation module for AutiConnect Telegram Bot.
Handles AI-mediated interactions in groups and private chats.
"""

from telegram import Update, ParseMode
from telegram.ext import CallbackContext
from datetime import datetime, timedelta

def handle_group_message(update: Update, context: CallbackContext) -> None:
    """
    Handle messages in group chats with AI mediation.
    
    Args:
        update: Update object from Telegram
        context: CallbackContext object from Telegram
    """
    # Get database and LLM instances from main module
    from main import db, llm, group_message_timestamps
    
    message = update.message
    user_id = message.from_user.id
    chat_id = message.chat_id
    text = message.text
    
    # Store message in database
    db.store_message(user_id, chat_id, text)
    
    # Check if this is a group chat
    if message.chat.type in ['group', 'supergroup']:
        # Get group from database
        group = db.get_group(chat_id)
        
        # If group exists and AI mediator is enabled
        if group and group.get('ai_mediator_enabled', False):
            # Check if it's time for AI to intervene
            should_intervene = should_ai_intervene(chat_id, group_message_timestamps)
            
            if should_intervene:
                # Get recent messages
                recent_messages = db.get_recent_messages(group_id=chat_id, limit=10)
                
                # Generate AI mediator response
                ai_response, alert_needed = llm.mediate_group_conversation(
                    chat_id, recent_messages, user_id
                )
                
                if ai_response:
                    # Send AI response
                    context.bot.send_message(
                        chat_id=chat_id,
                        text=f"🤖 *Mediador IA*: {ai_response}",
                        parse_mode=ParseMode.MARKDOWN
                    )
                    
                    # Update last intervention timestamp
                    group_message_timestamps[chat_id] = datetime.now()
                    
                    # If professional alert is needed
                    if alert_needed:
                        # Get AT for this group
                        at_id = group.get('created_by')
                        if at_id:
                            # Send alert to AT
                            context.bot.send_message(
                                chat_id=at_id,
                                text=(
                                    f"⚠️ *ALERTA*: Possível situação que requer atenção no grupo "
                                    f"'{group['name']}'.\n\n"
                                    f"Por favor, verifique a conversa recente e intervenha se necessário."
                                ),
                                parse_mode=ParseMode.MARKDOWN
                            )

def handle_private_message(update: Update, context: CallbackContext) -> None:
    """
    Handle private messages with AI support.
    
    Args:
        update: Update object from Telegram
        context: CallbackContext object from Telegram
    """
    # Get database and LLM instances from main module
    from main import db, llm, private_chat_sessions
    
    message = update.message
    user_id = message.from_user.id
    text = message.text
    
    # Store message in database
    db.store_message(user_id, None, text)
    
    # Get user from database
    user = db.get_user(user_id)
    
    # If user exists and is autistic
    if user and user.get('role') == 'autista':
        # Check if this is a support session
        is_support_session = user_id in private_chat_sessions
        
        # If not a command and either in support session or message suggests need for support
        if not text.startswith('/') and (is_support_session or needs_support(text)):
            # Generate AI support response
            ai_response, alert_needed = llm.provide_individual_support(user_id, text)
            
            if ai_response:
                # Send AI response
                message.reply_text(
                    f"🤖 *Assistente IA*: {ai_response}",
                    parse_mode=ParseMode.MARKDOWN
                )
                
                # Mark as support session
                if not is_support_session:
                    private_chat_sessions[user_id] = datetime.now()
                
                # If professional alert is needed
                if alert_needed:
                    # Get user's groups and their ATs
                    user_groups = user.get('groups', [])
                    ats_notified = set()
                    
                    for group_id in user_groups:
                        group = db.get_group(group_id)
                        if group:
                            at_id = group.get('created_by')
                            if at_id and at_id not in ats_notified:
                                # Send alert to AT
                                context.bot.send_message(
                                    chat_id=at_id,
                                    text=(
                                        f"⚠️ *ALERTA*: {user['name']} pode precisar de suporte profissional "
                                        f"em uma conversa privada com o assistente IA.\n\n"
                                        f"Por favor, entre em contato com o usuário quando possível."
                                    ),
                                    parse_mode=ParseMode.MARKDOWN
                                )
                                ats_notified.add(at_id)

def should_ai_intervene(group_id, group_message_timestamps):
    """
    Determine if AI should intervene in a group conversation.
    
    Args:
        group_id (int): Telegram group ID
        group_message_timestamps (dict): Dictionary tracking last AI intervention
        
    Returns:
        bool: Whether AI should intervene
    """
    # Check if we have a timestamp for this group
    last_intervention = group_message_timestamps.get(group_id)
    
    # If no previous intervention or it's been more than 5 minutes
    if not last_intervention or (datetime.now() - last_intervention) > timedelta(minutes=5):
        return True
    
    # Otherwise, don't intervene yet
    return False

def needs_support(message_text):
    """
    Simple heuristic to determine if a message suggests need for support.
    
    Args:
        message_text (str): Message text
        
    Returns:
        bool: Whether support seems needed
    """
    # Keywords that might indicate need for support
    support_keywords = [
        'ajuda', 'ansioso', 'ansiosa', 'nervoso', 'nervosa', 'triste',
        'confuso', 'confusa', 'difícil', 'não consigo', 'problema',
        'assustado', 'assustada', 'medo', 'sozinho', 'sozinha'
    ]
    
    # Check if any keyword is in the message
    message_lower = message_text.lower()
    for keyword in support_keywords:
        if keyword in message_lower:
            return True
    
    # Check for question marks or exclamation marks (might indicate confusion or distress)
    if '?' in message_text or '!' in message_text:
        return True
    
    return False
