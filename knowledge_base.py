"""
knowledge_base.py — Vector store for PortSwigger's established legal positions.

Uses ChromaDB (local, no server needed) with sentence-transformer embeddings.
The playbook is the source of truth — the AI only applies positions that exist here.
"""

import json
import os
from typing import List, Dict

PLAYBOOK_PATH = os.path.join(os.path.dirname(__file__), "data", "playbook.json")
COLLECTION_NAME = "contract_playbook"


def load_playbook() -> List[Dict]:
    with open(PLAYBOOK_PATH, "r") as f:
        return json.load(f)


def build_knowledge_base():
    """
    Initialise ChromaDB in-memory and load the playbook as searchable documents.
    Called once at startup; cached by Streamlit.
    """
    import chromadb
    from chromadb.utils import embedding_functions

    client = chromadb.Client()

    # Default embedding function uses all-MiniLM-L6-v2 locally — no API key needed
    ef = embedding_functions.DefaultEmbeddingFunction()

    # Fresh collection each run (in-memory)
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        embedding_function=ef,
    )

    playbook = load_playbook()
    documents, metadatas, ids = [], [], []

    for i, entry in enumerate(playbook):
        # Rich document text for semantic search
        doc_text = (
            f"Clause type: {entry['clause_type']}\n"
            f"Issue: {entry['issue']}\n"
            f"Triggers: {', '.join(entry.get('trigger_phrases', []))}\n"
            f"Standard position: {entry['standard_position']}"
        )
        documents.append(doc_text)
        metadatas.append(
            {
                "clause_type": entry["clause_type"],
                "issue": entry["issue"],
                "standard_position": entry["standard_position"],
                "suggested_redline": entry.get("suggested_redline", ""),
                "action": entry.get("default_action", "review"),
                "precedent_count": entry.get("precedent_count", 0),
                "contract_types": ",".join(entry.get("contract_types", [])),
            }
        )
        ids.append(f"entry_{i}")

    collection.add(documents=documents, metadatas=metadatas, ids=ids)
    return collection


def search_precedents(collection, query_text: str, n_results: int = 10) -> List[Dict]:
    """Return the most relevant playbook entries for the given contract text."""
    results = collection.query(
        query_texts=[query_text[:2000]],  # Embed a representative excerpt
        n_results=min(n_results, collection.count()),
    )

    precedents = []
    if results["documents"] and results["documents"][0]:
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i]
            precedents.append({"document": doc, "metadata": meta})

    return precedents
