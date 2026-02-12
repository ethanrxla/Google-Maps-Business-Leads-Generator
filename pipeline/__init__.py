"""Pipeline package for the leads swarm pipeline.

Stages:
  1. Collector  - gathers raw candidates from multiple sources
  2. Deduper    - cross-source identity resolution
  3. Verifier   - validates contact info, assigns confidence scores
  4. Assembler  - bundles verified leads into sellable packs
"""
