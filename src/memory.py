"""FAISS DB Logic."""
from typing import Optional

import faiss
import logging
import pickle
import uuid
from datetime import datetime
import numpy as np
import os
from sentence_transformers import SentenceTransformer
from src.setup import config, INDEX_PATH, META_PATH
from src.models import MemoryEntryModel, AddEntryModel, LLMUserProfileModel

logger = logging.getLogger(__name__)


class MemoryStore():
    """FAISS memory store class."""

    def __init__(self) -> None:
        self.dedup_threshold = config.memory_config.dedup_threshold
        self.top_k = config.memory_config.top_k
        self.min_score = config.memory_config.min_score
        self.embedding_model = config.memory_config.embedding_model

        self.embedder = self._get_embedder()

    @property
    def is_empty(self) -> bool:
        _, metadata = self._load()
        return not any(not e.is_deleted for e in metadata)

    def _get_embedder(self) -> None:
        """Load embedder."""
        return SentenceTransformer(self.embedding_model)

    def _embed(self, text: str) -> np.ndarray:
        """Return a normalised float32 embedding vector."""
        vector = self.embedder.encode(text, normalize_embeddings=True)
        return np.array(vector, dtype=np.float32)

    def _load(self) -> tuple:
        """Load index + metadata from disk, or create empty."""
        if os.path.exists(INDEX_PATH) and os.path.exists(META_PATH):
            logger.debug("Loading memory index from disk.")
            index = faiss.read_index(INDEX_PATH)
            with open(META_PATH, "rb") as f:
                metadata: list[MemoryEntryModel] = pickle.load(f)

        else:
            logger.info("No memory index found - creating fresh index")

            dimension = self.embedder.get_sentence_embedding_dimension()
            index = faiss.IndexFlatIP(dimension)
            metadata = []
        return index, metadata

    def _save(self,
              index: faiss.IndexFlatIP,
              metadata: list[MemoryEntryModel]) -> None:
        """Save index and metadata."""
        faiss.write_index(index, INDEX_PATH)
        with open(META_PATH, "wb") as f:
            pickle.dump(metadata, f)
        logger.debug(f"Memory index persisted ({len(metadata)} entries)")

    def wipe(self) -> None:
        """Wipe the entire index and metadata."""
        if os.path.exists(INDEX_PATH):
            os.remove(INDEX_PATH)
        if os.path.exists(META_PATH):
            os.remove(META_PATH)
        logger.info("Memory index wiped")

    def delete_source(self, source: str) -> None:
        """Soft delete all entries in a source."""
        index, metadata = self._load()

        cleared = 0
        for entry in metadata:
            if entry.source == source:
                entry.is_deleted = True
                cleared += 1
        self._save(index, metadata)
        logger.info(f"Deleted {cleared} {source} entries")

    def delete_category(self, category: str) -> None:
        """Soft delete all entries in a category."""
        index, metadata = self._load()

        cleared = 0
        for entry in metadata:
            if entry.category == category:
                entry.is_deleted = True
                cleared += 1
        self._save(index, metadata)
        logger.info(f"Deleted {cleared} {category} entries")

    def delete_entry(self, id: str) -> None:
        """Soft delete a single entry by id."""
        index, metadata = self._load()
        is_found = False

        for entry in metadata:
            if entry.id == id:
                entry.is_deleted = True
                is_found = True
                break
        if is_found:
            self._save(index, metadata)
            logger.info(f"Deleted entry {id}")
        else:
            logger.info(f"{id} not found in DB")

    def restore_entry(self, id: str) -> None:
        """Restore soft deleted entry by id."""
        index, metadata = self._load()
        is_found, is_updated = False, False

        for entry in metadata:
            if entry.id == id:
                if entry.is_deleted:
                    entry.is_deleted = False
                    is_updated = True
                is_found = True
                break
        if is_updated:
            self._save(index, metadata)
            logger.info(f"{id} is restored")
        elif is_found:
            logger.info(f"Entry {id} is already active")
        else:
            logger.info(f"{id} not found in DB")

    def clear_profile(self) -> None:
        self.delete_source("profile")

    def get_metadata(self) -> Optional[list[MemoryEntryModel]]:
        """Return Metadata."""
        _, metadata = self._load()
        return metadata

    def add_entry(self, entry: AddEntryModel) -> Optional[MemoryEntryModel]:
        """Add entry."""
        index, metadata = self._load()
        vector = self._embed(entry.content).reshape(1, -1)

        if index.ntotal > 0:
            scores, _ = index.search(vector, k=1)
            if float(scores[0][0]) >= self.dedup_threshold:
                logger.debug(
                    f"Skipping duplicate entry (score {scores[0][0]:3f})")
                return None
        memory_entry = MemoryEntryModel(
            id=str(uuid.uuid1()),
            category=entry.category,
            content=entry.content,
            created_at=datetime.now().isoformat(),
            source=entry.source
        )

        index.add(vector)
        metadata.append(memory_entry)
        self._save(index, metadata)

        logger.info(f"Added memory entry [{memory_entry.id}]"
                    f"category: {entry.category}")

        return memory_entry

    def search(self, query: str) -> list[MemoryEntryModel]:
        """Return up to *top_k* entries most similar to *query*."""
        index, metadata = self._load()

        if index.ntotal == 0:
            return []

        vector = self._embed(query).reshape(1, -1)
        k = min(self.top_k, index.ntotal)
        scores, indices = index.search(vector, k=k)

        results: list[MemoryEntryModel] = []

        for score, idx in zip(scores[0], indices[0]):
            if idx == -1 or metadata[idx].is_deleted:
                continue

            if float(score) < self.min_score:
                continue

            entry = metadata[idx]
            results.append(
                MemoryEntryModel(
                    id=entry.id,
                    category=entry.category,
                    content=entry.content,
                    created_at=entry.created_at,
                    score=float(score)
                )
            )
        return results

    def seed_from_profile(self, profile: LLMUserProfileModel) -> None:
        """Populate the index from a structured profile."""
        inserted = 0

        if profile.summary:
            if self.add_entry(
                AddEntryModel(
                    source="profile",
                    category="summary",
                    content=profile.summary)):
                inserted += 1

        for skill in profile.technical_skills or []:
            if self.add_entry(
                AddEntryModel(source="profile",
                              category="skills",
                              content=skill)):
                inserted += 1

        if profile.current_title:
            if self.add_entry(
                AddEntryModel(
                    source="profile",
                    category="experience",
                    content=f"Current title: {profile.current_title}")):
                inserted += 1

        for title in profile.title_history or []:
            if self.add_entry(
                AddEntryModel(source="profile",
                              category="experience",
                              content=f"Previous title: {title}")):
                inserted += 1

        for cert in profile.certifications or []:
            if self.add_entry(
                AddEntryModel(source="profile",
                              category="certifications",
                              content=cert)):
                inserted += 1

        if profile.years_of_experience is not None:
            if self.add_entry(
                AddEntryModel(
                    source="profile",
                    category="summary",
                    content=(
                        f"{profile.years_of_experience} years "
                        "of professional experience"))):
                inserted += 1

        logger.info(f"seed_from_profile: inserted {inserted} entries")


memory_store = MemoryStore()
