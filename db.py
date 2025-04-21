"""
Database module for AutiConnect Telegram Bot.
Handles all interactions with MongoDB database.
"""

import os
import pymongo
from datetime import datetime

class Database:
    def __init__(self):
        """Initialize database connection using environment variables."""
        # Use environment variable for MongoDB URI
        mongo_uri = os.environ.get('MONGO_URI')
        if not mongo_uri:
            raise ValueError("MONGO_URI environment variable not set")
        
        # Connect to MongoDB
        self.client = pymongo.MongoClient(mongo_uri)
        self.db = self.client.auticonnect
        
        # Create collections
        self.users = self.db.users
        self.groups = self.db.groups
        self.activities = self.db.activities
        self.messages = self.db.messages
        self.interactions = self.db.interactions
        
        # Create indexes for faster queries
        self.users.create_index("user_id", unique=True)
        self.groups.create_index("group_id", unique=True)
        self.messages.create_index([("group_id", 1), ("timestamp", -1)])
        self.messages.create_index([("user_id", 1), ("timestamp", -1)])
    
    def create_user(self, user_id, name, role, **kwargs):
        """
        Create a new user in the database with expanded profile information.
        
        Args:
            user_id (int): Telegram user ID
            name (str): User's name
            role (str): User's role ('autista' or 'at')
            **kwargs: Additional profile information
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Base user data
            user_data = {
                "user_id": user_id,
                "name": name,
                "role": role,
                "groups": [],
                "created_at": datetime.now(),
                "last_active": datetime.now()
            }
            
            # Add expanded profile information if provided
            if role == 'autista':
                # Default values for autistic user profile
                profile = {
                    "age": kwargs.get("age", None),
                    "gender": kwargs.get("gender", None),
                    "emergency_contacts": kwargs.get("emergency_contacts", []),
                    "academic_history": kwargs.get("academic_history", ""),
                    "professionals": kwargs.get("professionals", []),
                    "interests": kwargs.get("interests", []),
                    "anxiety_triggers": kwargs.get("anxiety_triggers", []),
                    "communication_preferences": kwargs.get("communication_preferences", {
                        "style": "direct",  # or "detailed"
                        "preferred_topics": [],
                        "avoided_topics": [],
                        "notes": ""
                    }),
                    "interaction_history": []
                }
                user_data["profile"] = profile
            
            # Insert or update user
            self.users.update_one(
                {"user_id": user_id},
                {"$set": user_data},
                upsert=True
            )
            return True
        except Exception as e:
            print(f"Error creating user: {e}")
            return False
    
    def update_user_profile(self, user_id, profile_data):
        """
        Update user profile information.
        
        Args:
            user_id (int): Telegram user ID
            profile_data (dict): Profile data to update
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Update only provided fields
            update_data = {}
            for key, value in profile_data.items():
                update_data[f"profile.{key}"] = value
            
            self.users.update_one(
                {"user_id": user_id},
                {"$set": update_data}
            )
            return True
        except Exception as e:
            print(f"Error updating user profile: {e}")
            return False
    
    def add_interaction_to_history(self, user_id, interaction_data):
        """
        Add an interaction to user's interaction history.
        
        Args:
            user_id (int): Telegram user ID
            interaction_data (dict): Data about the interaction
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            interaction = {
                "timestamp": datetime.now(),
                **interaction_data
            }
            
            self.users.update_one(
                {"user_id": user_id},
                {"$push": {"profile.interaction_history": interaction}}
            )
            return True
        except Exception as e:
            print(f"Error adding interaction to history: {e}")
            return False
    
    def get_user(self, user_id):
        """
        Get user information from database.
        
        Args:
            user_id (int): Telegram user ID
            
        Returns:
            dict: User data or None if not found
        """
        return self.users.find_one({"user_id": user_id})
    
    def create_group(self, group_id, name, theme, description, created_by, max_members=10):
        """
        Create a new thematic group.
        
        Args:
            group_id (int): Telegram chat ID
            name (str): Group name
            theme (str): Group theme
            description (str): Group description
            created_by (int): User ID of AT who created the group
            max_members (int): Maximum number of members
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            group_data = {
                "group_id": group_id,
                "name": name,
                "theme": theme,
                "description": description,
                "created_by": created_by,
                "members": [created_by],  # Creator is first member
                "max_members": max_members,
                "created_at": datetime.now(),
                "last_active": datetime.now(),
                "ai_mediator_enabled": True,  # Enable AI mediator by default
                "ai_mediator_settings": {
                    "intervention_frequency": "medium",  # low, medium, high
                    "activity_suggestions": True,
                    "conflict_mediation": True,
                    "support_private_chats": True
                }
            }
            
            # Insert or update group
            self.groups.update_one(
                {"group_id": group_id},
                {"$set": group_data},
                upsert=True
            )
            
            # Add group to creator's groups
            self.users.update_one(
                {"user_id": created_by},
                {"$addToSet": {"groups": group_id}}
            )
            
            return True
        except Exception as e:
            print(f"Error creating group: {e}")
            return False
    
    def update_group_ai_settings(self, group_id, ai_settings):
        """
        Update AI mediator settings for a group.
        
        Args:
            group_id (int): Telegram group ID
            ai_settings (dict): AI mediator settings
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.groups.update_one(
                {"group_id": group_id},
                {"$set": {"ai_mediator_settings": ai_settings}}
            )
            return True
        except Exception as e:
            print(f"Error updating group AI settings: {e}")
            return False
    
    def get_all_groups(self):
        """
        Get all available groups.
        
        Returns:
            list: List of group documents
        """
        return list(self.groups.find())
    
    def get_group(self, group_id):
        """
        Get group information.
        
        Args:
            group_id (int): Telegram chat ID
            
        Returns:
            dict: Group data or None if not found
        """
        return self.groups.find_one({"group_id": group_id})
    
    def add_user_to_group(self, user_id, group_id):
        """
        Add a user to a group.
        
        Args:
            user_id (int): Telegram user ID
            group_id (int): Telegram chat ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Add user to group's members
            self.groups.update_one(
                {"group_id": group_id},
                {"$addToSet": {"members": user_id}}
            )
            
            # Add group to user's groups
            self.users.update_one(
                {"user_id": user_id},
                {"$addToSet": {"groups": group_id}}
            )
            
            return True
        except Exception as e:
            print(f"Error adding user to group: {e}")
            return False
    
    def create_activity(self, group_id, activity_type, title, description, created_by, scheduled_time=None, duration=60):
        """
        Create a new activity for a group.
        
        Args:
            group_id (int): Telegram chat ID
            activity_type (str): Type of activity
            title (str): Activity title
            description (str): Activity description
            created_by (int): User ID of AT who created the activity
            scheduled_time (datetime): When the activity is scheduled
            duration (int): Duration in minutes
            
        Returns:
            str: Activity ID if successful, None otherwise
        """
        try:
            activity_data = {
                "group_id": group_id,
                "type": activity_type,
                "title": title,
                "description": description,
                "created_by": created_by,
                "participants": [],
                "status": "scheduled",
                "scheduled_time": scheduled_time or datetime.now(),
                "duration": duration,
                "created_at": datetime.now(),
                "ai_guidance_enabled": True,  # Enable AI guidance by default
                "ai_guidance_notes": ""
            }
            
            result = self.activities.insert_one(activity_data)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error creating activity: {e}")
            return None
    
    def get_group_activities(self, group_id, status="scheduled"):
        """
        Get activities for a specific group.
        
        Args:
            group_id (int): Telegram chat ID
            status (str): Activity status filter
            
        Returns:
            list: List of activity documents
        """
        return list(self.activities.find({
            "group_id": group_id,
            "status": status
        }).sort("scheduled_time", 1))
    
    def get_user_activities(self, user_id):
        """
        Get activities for groups that a user is part of.
        
        Args:
            user_id (int): Telegram user ID
            
        Returns:
            list: List of activity documents
        """
        # Get user's groups
        user = self.get_user(user_id)
        if not user or not user.get("groups"):
            return []
        
        # Get activities for those groups
        return list(self.activities.find({
            "group_id": {"$in": user["groups"]},
            "status": "scheduled"
        }).sort("scheduled_time", 1))
    
    def store_message(self, user_id, group_id, message_text, message_type="text"):
        """
        Store a message in the database.
        
        Args:
            user_id (int): Telegram user ID
            group_id (int): Telegram group ID (or None for private messages)
            message_text (str): Message content
            message_type (str): Type of message (text, image, etc.)
            
        Returns:
            str: Message ID if successful, None otherwise
        """
        try:
            message_data = {
                "user_id": user_id,
                "group_id": group_id,
                "text": message_text,
                "type": message_type,
                "timestamp": datetime.now()
            }
            
            result = self.messages.insert_one(message_data)
            
            # Update last active timestamp
            self.update_last_active(user_id)
            if group_id:
                self.groups.update_one(
                    {"group_id": group_id},
                    {"$set": {"last_active": datetime.now()}}
                )
            
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error storing message: {e}")
            return None
    
    def get_recent_messages(self, group_id=None, user_id=None, limit=20):
        """
        Get recent messages for a group or from/to a user.
        
        Args:
            group_id (int, optional): Telegram group ID
            user_id (int, optional): Telegram user ID
            limit (int): Maximum number of messages to return
            
        Returns:
            list: List of message documents
        """
        query = {}
        if group_id is not None:
            query["group_id"] = group_id
        if user_id is not None:
            query["user_id"] = user_id
        
        return list(self.messages.find(query).sort("timestamp", -1).limit(limit))
    
    def store_ai_interaction(self, interaction_type, context, input_data, output_data, metadata=None):
        """
        Store an AI interaction for analysis and improvement.
        
        Args:
            interaction_type (str): Type of interaction
            context (dict): Context information
            input_data (dict): Input data for the interaction
            output_data (dict): Output data from the interaction
            metadata (dict, optional): Additional metadata
            
        Returns:
            str: Interaction ID if successful, None otherwise
        """
        try:
            interaction_data = {
                "type": interaction_type,
                "context": context,
                "input": input_data,
                "output": output_data,
                "metadata": metadata or {},
                "timestamp": datetime.now()
            }
            
            result = self.interactions.insert_one(interaction_data)
            return str(result.inserted_id)
        except Exception as e:
            print(f"Error storing AI interaction: {e}")
            return None
    
    def update_last_active(self, user_id):
        """
        Update user's last active timestamp.
        
        Args:
            user_id (int): Telegram user ID
        """
        self.users.update_one(
            {"user_id": user_id},
            {"$set": {"last_active": datetime.now()}}
        )
