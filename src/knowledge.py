"""Fleet Knowledge — Semantic search for millions of commits.

Multi-tier index: local → site → regional → global.
Capability discovery, cross-domain knowledge translation.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from enum import Enum
import time
import json
import hashlib
import math


class IndexTier(Enum):
    LOCAL = 0       # Single vessel
    SITE = 1        # Multi-vessel site
    REGIONAL = 2    # Geographic region
    GLOBAL = 3      # Entire fleet


class KnowledgeType(Enum):
    SKILL = "skill"
    CONFIGURATION = "configuration"
    ARCHITECTURE = "architecture"
    INTEGRATION = "integration"
    SAFETY = "safety"
    TRAINING = "training"
    CROSS_DOMAIN = "cross_domain"


@dataclass
class KnowledgeEntry:
    entry_id: str = ""
    repository: str = ""
    commit_sha: str = ""
    knowledge_type: KnowledgeType = KnowledgeType.SKILL
    vessel_domain: str = "marine"
    title: str = ""
    description: str = ""
    tags: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    embedding: List[float] = field(default_factory=list)
    adoption_count: int = 0
    derivative_count: int = 0
    tier: IndexTier = IndexTier.LOCAL
    timestamp: float = 0.0
    quality_score: float = 0.0

    def __post_init__(self):
        if not self.entry_id:
            self.entry_id = hashlib.sha256(
                f"{self.repository}:{self.commit_sha}:{self.title}".encode()
            ).hexdigest()[:16]
        if not self.timestamp:
            self.timestamp = time.time()

    def to_dict(self) -> dict:
        return {
            "id": self.entry_id,
            "repo": self.repository,
            "sha": self.commit_sha,
            "type": self.knowledge_type.value,
            "domain": self.vessel_domain,
            "title": self.title,
            "desc": self.description[:200],
            "tags": self.tags,
            "capabilities": self.capabilities,
            "adoption": self.adoption_count,
            "derivative": self.derivative_count,
            "tier": self.tier.value,
            "quality": self.quality_score,
        }

    def compound_score(self) -> float:
        """Value = adoption × derivatives × time_decay × quality."""
        age_days = (time.time() - self.timestamp) / 86400
        time_decay = 1.0 / (1.0 + 0.001 * age_days)  # Slow decay
        adoption = 1.0 + self.adoption_count * 0.1
        derivatives = 1.0 + self.derivative_count * 0.2
        return round(adoption * derivatives * time_decay * self.quality_score, 3)


class KnowledgeIndex:
    """Multi-tier knowledge index with simple keyword and capability search."""

    def __init__(self, vessel_id: str, tier: IndexTier = IndexTier.LOCAL):
        self.vessel_id = vessel_id
        self.tier = tier
        self._entries: Dict[str, KnowledgeEntry] = {}
        self._tag_index: Dict[str, List[str]] = {}
        self._capability_index: Dict[str, List[str]] = {}
        self._domain_index: Dict[str, List[str]] = {}

    def add(self, entry: KnowledgeEntry):
        self._entries[entry.entry_id] = entry
        # Update indices
        for tag in entry.tags:
            if tag not in self._tag_index:
                self._tag_index[tag] = []
            self._tag_index[tag].append(entry.entry_id)
        for cap in entry.capabilities:
            if cap not in self._capability_index:
                self._capability_index[cap] = []
            self._capability_index[cap].append(entry.entry_id)
        if entry.vessel_domain not in self._domain_index:
            self._domain_index[entry.vessel_domain] = []
        self._domain_index[entry.vessel_domain].append(entry.entry_id)

    def search(self, query: str, domain: str = None,
               knowledge_type: KnowledgeType = None,
               limit: int = 20) -> List[KnowledgeEntry]:
        ql = query.lower().split()
        scored = []

        for eid, entry in self._entries.items():
            if domain and entry.vessel_domain != domain:
                continue
            if knowledge_type and entry.knowledge_type != knowledge_type:
                continue

            # Simple TF scoring against query terms
            searchable = f"{entry.title} {entry.description} {' '.join(entry.tags)} {' '.join(entry.capabilities)}".lower()
            score = 0
            for term in ql:
                score += searchable.count(term)

            if score > 0:
                # Boost by compound score
                final = score * (1.0 + entry.compound_score())
                scored.append((final, entry))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [e for _, e in scored[:limit]]

    def find_capabilities(self, capability: str) -> List[KnowledgeEntry]:
        eids = self._capability_index.get(capability.lower(), [])
        return [self._entries[eid] for eid in eids if eid in self._entries]

    def discover_cross_domain(self, source_domain: str,
                              target_domain: str) -> List[KnowledgeEntry]:
        """Find knowledge that could transfer between domains."""
        results = []
        for eid, entry in self._entries.items():
            if entry.knowledge_type == KnowledgeType.CROSS_DOMAIN:
                if (source_domain in entry.tags or target_domain in entry.tags):
                    results.append(entry)
        return sorted(results, key=lambda e: e.compound_score(), reverse=True)

    def merge(self, other: "KnowledgeIndex"):
        """Merge another index into this one (for aggregation)."""
        for eid, entry in other._entries.items():
            if eid in self._entries:
                # Keep higher quality
                if entry.quality_score > self._entries[eid].quality_score:
                    self._entries[eid] = entry
            else:
                self.add(entry)

    def stats(self) -> Dict[str, Any]:
        return {
            "vessel_id": self.vessel_id,
            "tier": self.tier.name,
            "entries": len(self._entries),
            "tags": len(self._tag_index),
            "capabilities": len(self._capability_index),
            "domains": {k: len(v) for k, v in self._domain_index.items()},
            "top_compound": [
                e.to_dict() for e in sorted(
                    self._entries.values(),
                    key=lambda e: e.compound_score(),
                    reverse=True,
                )[:5]
            ],
        }
