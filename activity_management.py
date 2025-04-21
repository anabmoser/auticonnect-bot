"""
Activity management module for AutiConnect Telegram Bot.
Handles activity creation and management.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, ConversationHandler

def list_activities(update: Update, context: CallbackContext) -> None:
    """
    List upcoming activities for the user's groups.
    
    Args:
        update: Update object from Telegram
        context: CallbackContext object from Telegram
    """
    # Get database instance from main module
    from main import db
    
    user_id = update.effective_user.id
    db.update_last_active(user_id)
    
    activities = db.get_user_activities(user_id)
    
    if not activities:
        update.message.reply_text(
            "Não há atividades programadas para seus grupos no momento.\n\n"
            "Se você é um AT, pode iniciar uma nova atividade com /iniciar_atividade."
        )
        return
    
    message = "📅 *Atividades Programadas:*\n\n"
    
    for activity in activities:
        # Get group name
        group_id = activity.get('group_id')
        group = db.get_group(group_id)
        group_name = group.get('name', 'Desconhecido') if group else 'Desconhecido'
        
        # Format scheduled time
        scheduled_time = activity.get('scheduled_time', 'Não definido')
        if scheduled_time != 'Não definido':
            scheduled_time = scheduled_time.strftime("%d/%m/%Y às %H:%M")
        
        # Check if AI guidance is enabled
        ai_enabled = activity.get('ai_guidance_enabled', False)
        ai_status = "✅ Ativo" if ai_enabled else "❌ Inativo"
        
        message += (
            f"*{activity['title']}*\n"
            f"📝 Tipo: {activity['type']}\n"
            f"👥 Grupo: {group_name}\n"
            f"🕒 Quando: {scheduled_time}\n"
            f"⏱️ Duração: {activity.get('duration', 60)} minutos\n"
            f"🤖 Guia IA: {ai_status}\n"
            f"ℹ️ {activity['description']}\n\n"
        )
    
    update.message.reply_text(message, parse_mode='MARKDOWN')

def start_activity_command(update: Update, context: CallbackContext) -> int:
    """
    Start the activity creation process (AT only).
    
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
            "Desculpe, apenas Auxiliares Terapêuticos (ATs) podem iniciar atividades."
        )
        return ConversationHandler.END
    
    # Get groups where user is AT
    groups = db.get_all_groups()
    at_groups = [g for g in groups if g.get('created_by') == user_id]
    
    if not at_groups:
        update.message.reply_text(
            "Você não tem nenhum grupo como AT. Crie um grupo primeiro com /criar_grupo."
        )
        return ConversationHandler.END
    
    # Store groups in context for later use
    context.user_data['at_groups'] = at_groups
    
    # Create keyboard with group options
    keyboard = []
    for group in at_groups:
        keyboard.append([InlineKeyboardButton(group['name'], callback_data=f"group_{group['group_id']}")])
    
    update.message.reply_text(
        "Vamos iniciar uma nova atividade estruturada.\n\n"
        "Primeiro, selecione o grupo para esta atividade:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return 6  # ACTIVITY_TYPE

def process_activity_group(update: Update, context: CallbackContext) -> int:
    """
    Process group selection for activity and ask for activity type.
    
    Args:
        update: Update object from Telegram
        context: CallbackContext object from Telegram
        
    Returns:
        int: Next conversation state
    """
    query = update.callback_query
    query.answer()
    
    group_id = int(query.data.split('_')[1])
    context.user_data['activity_group_id'] = group_id
    
    # Find group name
    group_name = next((g['name'] for g in context.user_data['at_groups'] if g['group_id'] == group_id), "Grupo")
    context.user_data['activity_group_name'] = group_name
    
    # Activity type options
    keyboard = [
        [InlineKeyboardButton("Discussão Temática", callback_data="type_discussao")],
        [InlineKeyboardButton("Projeto Colaborativo", callback_data="type_projeto")],
        [InlineKeyboardButton("Jogo Social", callback_data="type_jogo")],
        [InlineKeyboardButton("Compartilhamento de Interesses", callback_data="type_compartilhamento")]
    ]
    
    query.edit_message_text(
        f"Grupo selecionado: {group_name}\n\n"
        f"Qual tipo de atividade você deseja iniciar?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    
    return 7  # ACTIVITY_TITLE

def process_activity_type(update: Update, context: CallbackContext) -> int:
    """
    Process activity type selection and ask for title.
    
    Args:
        update: Update object from Telegram
        context: CallbackContext object from Telegram
        
    Returns:
        int: Next conversation state
    """
    query = update.callback_query
    query.answer()
    
    activity_type = query.data.split('_')[1]
    context.user_data['activity_type'] = activity_type
    
    # Map type codes to readable names
    type_names = {
        'discussao': 'Discussão Temática',
        'projeto': 'Projeto Colaborativo',
        'jogo': 'Jogo Social',
        'compartilhamento': 'Compartilhamento de Interesses'
    }
    
    context.user_data['activity_type_name'] = type_names.get(activity_type, activity_type)
    
    query.edit_message_text(
        f"Tipo de atividade: {context.user_data['activity_type_name']}\n\n"
        f"Qual será o título desta atividade?"
    )
    
    return 8  # ACTIVITY_DESC

def process_activity_title(update: Update, context: CallbackContext) -> int:
    """
    Process activity title input and ask for description.
    
    Args:
        update: Update object from Telegram
        context: CallbackContext object from Telegram
        
    Returns:
        int: Next conversation state
    """
    context.user_data['activity_title'] = update.message.text
    
    update.message.reply_text(
        f"Título: {context.user_data['activity_title']}\n\n"
        f"Por favor, forneça uma breve descrição desta atividade:"
    )
    
    return 9  # ACTIVITY_DURATION

def process_activity_desc(update: Update, context: CallbackContext) -> int:
    """
    Process activity description input and ask for duration.
    
    Args:
        update: Update object from Telegram
        context: CallbackContext object from Telegram
        
    Returns:
        int: Next conversation state
    """
    context.user_data['activity_desc'] = update.message.text
    
    update.message.reply_text(
        f"Descrição registrada. Qual será a duração desta atividade em minutos? (ex: 30, 60)"
    )
    
    return ConversationHandler.END

def process_activity_duration(update: Update, context: CallbackContext) -> int:
    """
    Process activity duration input and create the activity.
    
    Args:
        update: Update object from Telegram
        context: CallbackContext object from Telegram
        
    Returns:
        int: Next conversation state
    """
    # Get database instance from main module
    from main import db
    
    try:
        duration = int(update.message.text)
        if duration < 5 or duration > 180:
            update.message.reply_text(
                "Por favor, escolha uma duração entre 5 e 180 minutos."
            )
            return 9  # ACTIVITY_DURATION
    except ValueError:
        update.message.reply_text(
            "Por favor, digite apenas números para a duração em minutos."
        )
        return 9  # ACTIVITY_DURATION
    
    context.user_data['activity_duration'] = duration
    
    user_id = update.effective_user.id
    
    # Create activity in database
    activity_id = db.create_activity(
        group_id=context.user_data['activity_group_id'],
        activity_type=context.user_data['activity_type'],
        title=context.user_data['activity_title'],
        description=context.user_data['activity_desc'],
        created_by=user_id,
        duration=context.user_data['activity_duration']
    )
    
    if activity_id:
        # Ask about AI guidance
        keyboard = [
            [InlineKeyboardButton("Ativar guia IA", callback_data=f"ai_guide_on_{activity_id}")],
            [InlineKeyboardButton("Desativar guia IA", callback_data=f"ai_guide_off_{activity_id}")]
        ]
        
        update.message.reply_text(
            f"✅ Atividade '{context.user_data['activity_title']}' criada com sucesso para o grupo "
            f"'{context.user_data['activity_group_name']}'!\n\n"
            f"Você gostaria de ativar o guia de IA para esta atividade? "
            f"O guia de IA pode ajudar a estruturar a atividade, gerenciar turnos "
            f"e manter o foco no objetivo.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        update.message.reply_text(
            "Desculpe, ocorreu um erro ao criar a atividade. Por favor, tente novamente."
        )
    
    return ConversationHandler.END

def toggle_ai_guidance(update: Update, context: CallbackContext) -> None:
    """
    Toggle AI guidance for an activity.
    
    Args:
        update: Update object from Telegram
        context: CallbackContext object from Telegram
    """
    query = update.callback_query
    query.answer()
    
    data_parts = query.data.split('_')
    ai_status = data_parts[2]  # 'on' or 'off'
    activity_id = data_parts[3]
    
    # In a real implementation, this would update the activity in the database
    # For this MVP, we'll just acknowledge the selection
    
    status_text = "ativado" if ai_status == 'on' else "desativado"
    query.edit_message_text(
        f"Guia de IA {status_text} para esta atividade.\n\n"
        f"Em uma implementação completa, todos os membros do grupo seriam notificados. "
        f"Para este MVP, considere a atividade criada e pronta para começar.\n\n"
        f"Use /atividades para ver todas as atividades programadas."
    )
