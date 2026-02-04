import logging
import threading
from datetime import datetime
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class ConversationStateManager:
    """
    Manages conversation state across chat messages.
    State persists per conversationId throughout the conversation lifecycle.
    """

    def __init__(self):
        self._states: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        logger.info("ConversationStateManager initialized")

    def get_state(self, conversation_id: str) -> Dict[str, Any]:
        """
        Get the state for a conversation. Creates default state if not exists.

        Args:
            conversation_id: Unique conversation identifier

        Returns:
            Dictionary containing conversation state
        """
        with self._lock:
            if conversation_id not in self._states:
                logger.info(f"Creating new state for conversation: {conversation_id}")
                self._states[conversation_id] = self._create_default_state(conversation_id)

            return self._states[conversation_id].copy()

    def update_state(self, conversation_id: str, **fields) -> Dict[str, Any]:
        """
        Update specific fields in conversation state.

        Args:
            conversation_id: Unique conversation identifier
            **fields: Key-value pairs to update in state

        Returns:
            Updated state dictionary
        """
        with self._lock:
            if conversation_id not in self._states:
                logger.info(f"Creating new state for conversation: {conversation_id}")
                self._states[conversation_id] = self._create_default_state(conversation_id)

            # Special handling for context - merge instead of replace
            if "context" in fields:
                if "context" not in self._states[conversation_id]:
                    self._states[conversation_id]["context"] = {}
                self._states[conversation_id]["context"].update(fields["context"])
                # Remove context from fields to avoid double-updating
                fields = {k: v for k, v in fields.items() if k != "context"}

            # Update remaining fields
            self._states[conversation_id].update(fields)

            # Always update last_updated timestamp
            self._states[conversation_id]["last_updated"] = datetime.utcnow().isoformat()

            logger.debug(f"Updated state for {conversation_id}: {list(fields.keys())}")

            return self._states[conversation_id].copy()

    def is_ready(self, conversation_id: str) -> bool:
        """
        Check if a conversation is ready for querying (has dataset loaded).

        Args:
            conversation_id: Unique conversation identifier

        Returns:
            True if conversation has a dataset and is ready, False otherwise
        """
        state = self.get_state(conversation_id)
        has_dataset = state.get("dataset_id") is not None
        is_ready_flag = state.get("ready", False)

        ready = has_dataset and is_ready_flag

        logger.debug(f"Conversation {conversation_id} ready check: {ready} (dataset={has_dataset}, flag={is_ready_flag})")

        return ready

    def clear_state(self, conversation_id: str) -> bool:
        """
        Remove state for a conversation.

        Args:
            conversation_id: Unique conversation identifier

        Returns:
            True if state was removed, False if didn't exist
        """
        with self._lock:
            if conversation_id in self._states:
                del self._states[conversation_id]
                logger.info(f"Cleared state for conversation: {conversation_id}")
                return True
            return False

    def list_conversations(self) -> list[str]:
        """
        Get list of all active conversation IDs.

        Returns:
            List of conversation IDs
        """
        with self._lock:
            return list(self._states.keys())

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about active conversations.

        Returns:
            Dictionary with conversation statistics
        """
        with self._lock:
            return {
                "total_conversations": len(self._states),
                "conversations": list(self._states.keys())
            }

    def _create_default_state(self, conversation_id: str) -> Dict[str, Any]:
        """
        Create default state structure for a new conversation.

        Args:
            conversation_id: Unique conversation identifier

        Returns:
            Default state dictionary
        """
        return {
            "conversation_id": conversation_id,
            "dataset_id": None,
            "dataset_name": None,
            "ready": False,
            "message_count": 0,
            "created_at": datetime.utcnow().isoformat(),
            "last_updated": datetime.utcnow().isoformat(),
            "context": {},
            "metadata": {}
        }


# Global singleton instance
state_manager = ConversationStateManager()
