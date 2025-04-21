"""
Group management module for AutiConnect Telegram Bot.
Handles group creation and management.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode
from telegram.ext import CallbackContext, ConversationHandler
import time

def list_groups(update: Update, context: CallbackContext) -> None:
    """
    List all available thematic groups.
    
    Args:
        update: Update object from Telegram
        context: CallbackContext object from Telegram
    """
    # Get database instance from main module
    from main import db
    
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
        at_name = at.get('name', 'Desconhecido') if at else 'Desconhecido'
        
        # Check if AI mediator is enabled
        ai_enabled = group.get('ai_mediator_enabled', False)
        ai_status = "✅ Ativo" if ai_enabled else "❌ Inativo"
        
        message += (
            f"*{group['name']}*\n"
            f"📝 Tema: {group['theme']}\n"
            f"👥 Membros: {members_count}/{max_members}\n"
            f"👨‍⚕️ AT: {at_name}\n"
            f"🤖 Mediador IA: {ai_status}\n"
            f"ℹ️ {group['description']}\n\n"
        )
    
    # Add join button
    keyboard = []
    for group in groups:
        if len(group.get('members', [])) < group.get('max_members', 10):
            keyboard.append([InlineKeyboardButton(
                f"Entrar: {group['name']}", 
                callback_data=f"join_{group['group_id']}"
            )])
    
    if keyboard:
        update.message.reply_text(
            message, 
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        update.message.reply_text(message, parse_mode=ParseMode.MARKDOWN)

def join_group_callback(update: Update, context: CallbackContext) -> None:
    """
    Handle group join button callback.
    
    Args:
        update: Update object from Telegram
        context: CallbackContext object from Telegram
    """
    # Get database instance from main module
    from main import db
    
    query = update.callback_query
    query.answer()
    
    user_id = update.effective_user.id
    group_id = int(query.data.split('_')[1])
    
    # Add user to group
    success = db.add_user_to_group(user_id, group_id)
    
    if success:
        group = db.get_group(group_id)
        group_name = group.get('name', 'Grupo') if group else 'Grupo'
        
        query.edit_message_text(
            f"Você entrou no grupo '{group_name}' com sucesso!\n\n"
            f"Em uma implementação completa, você seria adicionado ao grupo do Telegram. "
            f"Para este MVP, considere-se membro do grupo e use /atividades para "
            f"ver as atividades programadas."
        )
    else:
        query.edit_message_text(
            "Desculpe, ocorreu um erro ao entrar no grupo. Por favor, tente novamente."
        )

def create_group_start(update: Update, context: CallbackContext) -> int:
    """
    Start the group creation process (AT only).
    
    Args:
        update: Update object from Telegram
        context: CallbackContext object from Telegram
        
    Returns:
        int: Next conversation state
    """
    # Get database instance from main module
    from main import db
    
    user_id = update.effective_user.id
    db.update_last_active(user_id)
    
    user = db.get_user(user_id)
    
    if not user:
        update.message.reply_text(
            "Você precisa se registrar primeiro. Use /start para criar seu perfil."
        )
        return ConversationHandler.END
    
    if user.get('role') != 'at':
        update.message.reply_text(
            "Desculpe, apenas Auxiliares Terapêuticos (ATs) podem criar grupos."
        )
        return ConversationHandler.END
    
    update.message.reply_text(
        "Vamos criar um novo grupo temático.\n\n"
        "Qual será o nome do grupo?"
    )
    return 2  # GROUP_NAME

def process_group_name(update: Update, context: CallbackContext) -> int:
    """
    Process group name input and ask for theme.
    
    Args:
        update: Update object from Telegram
        context: CallbackContext object from Telegram
        
    Returns:
        int: Next conversation state
    """
    context.user_data['group_name'] = update.message.text
    
    update.message.reply_text(
        f"Ótimo! O nome do grupo será: {context.user_data['group_name']}\n\n"
        f"Agora, qual será o tema principal deste grupo? (ex: videogames, música, ciência)"
    )
    return 3  # GROUP_THEME

def process_group_theme(update: Update, context: CallbackContext) -> int:
    """
    Process group theme input and ask for description.
    
    Args:
        update: Update object from Telegram
        context: CallbackContext object from Telegram
        
    Returns:
        int: Next conversation state
    """
    context.user_data['group_theme'] = update.message.text
    
    update.message.reply_text(
        f"Tema definido: {context.user_data['group_theme']}\n\n"
        f"Por favor, forneça uma breve descrição do propósito deste grupo:"
    )
    return 4  # GROUP_DESC

def process_group_desc(update: Update, context: CallbackContext) -> int:
    """
    Process group description input and ask for max members.
    
    Args:
        update: Update object from Telegram
        context: CallbackContext object from Telegram
        
    Returns:
        int: Next conversation state
    """
    context.user_data['group_desc'] = update.message.text
    
    update.message.reply_text(
        f"Descrição registrada. Qual será o número máximo de participantes? (recomendado: 8-12)"
    )
    return 5  # GROUP_MAX

def process_group_max(update: Update, context: CallbackContext) -> int:
    """
    Process max members input and create the group.
    
    Args:
        update: Update object from Telegram
        context: CallbackContext object from Telegram
        
    Returns:
        int: Next conversation state
    """
    # Get database instance from main module
    from main import db
    
    try:
        max_members = int(update.message.text)
        if max_members < 2 or max_members > 50:
            update.message.reply_text(
                "Por favor, escolha um número entre 2 e 50. Qual será o número máximo de participantes?"
            )
            return 5  # GROUP_MAX
    except ValueError:
        update.message.reply_text(
            "Por favor, digite apenas números. Qual será o número máximo de participantes?"
        )
        return 5  # GROUP_MAX
    
    context.user_data['group_max'] = max_members
    
    # Create a temporary group ID (in a real implementation, this would be the actual Telegram group ID)
    # For this MVP, we'll use a timestamp-based ID
    group_id = int(time.time())
    
    user_id = update.effective_user.id
    
    # Create group in database
    success = db.create_group(
        group_id=group_id,
        name=context.user_data['group_name'],
        theme=context.user_data['group_theme'],
        description=context.user_data['group_desc'],
        created_by=user_id,
        max_members=context.user_data['group_max']
    )
    
    if success:
        # Ask about AI mediator settings
        keyboard = [
            [InlineKeyboardButton("Ativar mediador IA", callback_data=f"ai_on_{group_id}")],
            [InlineKeyboardButton("Desativar mediador IA", callback_data=f"ai_off_{group_id}")]
        ]
        
        update.message.reply_text(
            f"✅ Grupo '{context.user_data['group_name']}' criado com sucesso!\n\n"
            f"Você gostaria de ativar o mediador de IA para este grupo? "
            f"O mediador de IA pode facilitar conversas, oferecer suporte e "
            f"alertar quando intervenção profissional for necessária.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        update.message.reply_text(
            "Desculpe, ocorreu um erro ao criar o grupo. Por favor, tente novamente."
        )
    
    return ConversationHandler.END

def toggle_ai_mediator(update: Update, context: CallbackContext) -> None:
    """
    Toggle AI mediator for a group.
    
    Args:
        update: Update object from Telegram
        context: CallbackContext object from Telegram
    """
    # Get database instance from main module
    from main import db
    
    query = update.callback_query
    query.answer()
    
    data_parts = query.data.split('_')
    ai_status = data_parts[1]  # 'on' or 'off'
    group_id = int(data_parts[2])
    
    # Update group AI settings
    ai_enabled = (ai_status == 'on')
    ai_settings = {
        "intervention_frequency": "medium",
        "activity_suggestions": True,
        "conflict_mediation": True,
        "support_private_chats": True
    }
    
    success = db.update_group_ai_settings(group_id, ai_settings)
    
    if success:
        group = db.get_group(group_id)
        group_name = group.get('name', 'Grupo') if group else 'Grupo'
        
        status_text = "ativado" if ai_enabled else "desativado"
        query.edit_message_text(
            f"Mediador de IA {status_text} para o grupo '{group_name}'.\n\n"
            f"Em uma implementação completa, você receberia um link para convidar participantes. "
            f"Para este MVP, considere o grupo criado e pronto para uso.\n\n"
            f"Use /iniciar_atividade para começar uma atividade neste grupo."
        )
    else:
        query.edit_message_text(
            "Desculpe, ocorreu um erro ao atualizar as configurações do mediador de IA. "
            "Por favor, tente novamente."
        )
