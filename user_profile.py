"""
User profile module for AutiConnect Telegram Bot.
Handles user profile creation and management.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import CallbackContext, ConversationHandler

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
            return 10  # PROFILE_AGE
    except ValueError:
        update.message.reply_text(
            "Por favor, digite apenas números para sua idade."
        )
        return 10  # PROFILE_AGE
    
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
    return 11  # PROFILE_GENDER

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
    return 12  # PROFILE_CONTACTS

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
    return 13  # PROFILE_ACADEMIC

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
    return 14  # PROFILE_PROFESSIONALS

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
    return 15  # PROFILE_INTERESTS

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
    return 16  # PROFILE_TRIGGERS

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
    return 17  # PROFILE_COMMUNICATION

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
    
    # Get database instance from main module
    from main import db
    
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
    # Get database instance from main module
    from main import db
    
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
        return 15  # PROFILE_INTERESTS
    else:
        update.message.reply_text(
            f"Olá, {user['name']}! Como AT, seu perfil é mais simples e não requer atualizações adicionais."
        )
        return ConversationHandler.END
