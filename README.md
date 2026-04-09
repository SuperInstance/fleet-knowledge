# fleet-knowledge

Semantic search and capability discovery across millions of commits. Multi-tier indexing from local vessel to global fleet.

## Index Tiers

```
Local (vessel) → Site (multi-vessel) → Regional (geographic) → Global (fleet)
```

## Usage

```python
from knowledge import KnowledgeIndex, KnowledgeEntry, KnowledgeType, IndexTier

index = KnowledgeIndex("vessel-01", IndexTier.SITE)

# Add knowledge entries
entry = KnowledgeEntry(
    repository="vessel-bridge", commit_sha="abc123",
    knowledge_type=KnowledgeType.SKILL,
    vessel_domain="marine", title="Low-light docking",
    description="Optimized camera exposure for night dock approach",
    tags=["docking", "camera", "low-light", "night"],
    capabilities=["navigation", "perception"],
    adoption_count=12, derivative_count=3, quality_score=0.85)

index.add(entry)

# Search
results = index.search("night docking camera", domain="marine")

# Find by capability
nav_knowledge = index.find_capabilities("navigation")

# Cross-domain discovery
transfers = index.discover_cross_domain("marine", "aerial")

# Compound score: adoption × derivatives × time_decay × quality
print(entry.compound_score())
```

Part of the [Lucineer ecosystem](https://github.com/Lucineer/the-fleet).
