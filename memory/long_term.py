# memory/long_term.py
# Long-term memory using ChromaDB vector store.
# Stores all interactions and can recall relevant past context.

import os
from datetime import datetime
from typing import Optional

from config import Config
from utils.logger import get_logger

log = get_logger("memory.long_term")


class LongTermMemory:
    """
    Persistent memory using ChromaDB.
    Stores interactions as embeddings for semantic retrieval.
    Hinata can recall relevant past conversations and facts.
    """

    def __init__(self):
        self._client = None
        self._collection = None
        self._initialized = False
        self._init_db()

    def _init_db(self):
        """Initialize ChromaDB."""
        try:
            import chromadb
            from chromadb.config import Settings

            persist_dir = os.path.abspath(Config.CHROMA_DB_PATH)
            os.makedirs(persist_dir, exist_ok=True)

            self._client = chromadb.PersistentClient(path=persist_dir)
            self._collection = self._client.get_or_create_collection(
                name="hinata_memory",
                metadata={"description": "Hinata's long-term memory"},
            )
            self._initialized = True
            log.info(f"Long-term memory initialized ({self._collection.count()} entries)")

        except ImportError:
            log.warning("ChromaDB not installed — long-term memory disabled. Run: pip install chromadb")
            self._initialized = False
        except Exception as e:
            log.error(f"Failed to initialize long-term memory: {e}")
            self._initialized = False

    async def store_interaction(self, user_input: str, response: str, user_id: str = "default"):
        """Store a user interaction in long-term memory."""
        if not self._initialized:
            return

        try:
            doc_id = f"{user_id}_{int(datetime.now().timestamp() * 1000)}"
            document = f"User said: {user_input}\nHinata replied: {response}"

            self._collection.add(
                documents=[document],
                metadatas=[{
                    "user_id": user_id,
                    "user_input": user_input[:500],
                    "timestamp": datetime.now().isoformat(),
                    "type": "conversation",
                }],
                ids=[doc_id],
            )
        except Exception as e:
            log.error(f"Failed to store interaction: {e}")

    async def store_fact(self, fact: str, category: str = "general", user_id: str = "default"):
        """Store a learned fact about the user."""
        if not self._initialized:
            return

        try:
            doc_id = f"fact_{user_id}_{int(datetime.now().timestamp() * 1000)}"
            self._collection.add(
                documents=[fact],
                metadatas=[{
                    "user_id": user_id,
                    "category": category,
                    "timestamp": datetime.now().isoformat(),
                    "type": "fact",
                }],
                ids=[doc_id],
            )
            log.debug(f"Stored fact: {fact[:80]}")
        except Exception as e:
            log.error(f"Failed to store fact: {e}")

    async def recall(self, query: str, n_results: int = 5, user_id: str = None) -> list[str]:
        """
        Recall relevant memories based on a query.
        Uses semantic similarity to find the most relevant past interactions.
        """
        if not self._initialized:
            return []

        try:
            where_filter = {"user_id": user_id} if user_id else None
            results = self._collection.query(
                query_texts=[query],
                n_results=n_results,
                where=where_filter,
            )

            documents = results.get("documents", [[]])[0]
            return documents

        except Exception as e:
            log.error(f"Recall error: {e}")
            return []

    async def search_facts(self, category: str = None, user_id: str = "default") -> list[str]:
        """Search for stored facts."""
        if not self._initialized:
            return []

        try:
            where_filter = {"type": "fact"}
            if user_id:
                where_filter["user_id"] = user_id

            results = self._collection.get(
                where=where_filter,
                limit=50,
            )
            return results.get("documents", [])
        except Exception as e:
            log.error(f"Search facts error: {e}")
            return []

    def count(self) -> int:
        """Number of entries in long-term memory."""
        if not self._initialized:
            return 0
        return self._collection.count()

    def clear(self):
        """Clear all long-term memory (use with caution)."""
        if self._initialized and self._client:
            self._client.delete_collection("hinata_memory")
            self._collection = self._client.get_or_create_collection("hinata_memory")
            log.info("Long-term memory cleared")
