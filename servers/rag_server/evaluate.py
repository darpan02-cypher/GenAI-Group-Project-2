Here is the full code for **`servers/rag_server/evaluate.py`**:

```python
import os
import json
import time
from typing import List, Dict, Any, Callable

# Expanded evaluation benchmark dataset covering conceptual definitions,
# system architecture, ingestion configurations, and API endpoints.
EVALUATION_DATASET: List[Dict[str, Any]] = [
    {
        "id": "q1",
        "query": "What is context precision in RAG evaluation?",
        "expected_doc": "metrics/context_precision.md",
        "category": "metrics_definition"
    },
    {
        "id": "q2",
        "query": "How is context recall calculated when evaluating chunk relevance?",
        "expected_doc": "metrics/context_recall.md",
        "category": "metrics_definition"
    },
    {
        "id": "q3",
        "query": "Explain the difference between faithfulness and answer relevance.",
        "expected_doc": "metrics/faithfulness.md",
        "category": "conceptual_comparison"
    },
    {
        "id": "q4",
        "query": "What chunk size and overlap are recommended for technical API documentation?",
        "expected_doc": "ingestion/chunking_strategies.md",
        "category": "ingestion_config"
    },
    {
        "id": "q5",
        "query": "How does Model Context Protocol (MCP) route vector search requests?",
        "expected_doc": "architecture/mcp_routing.md",
        "category": "system_architecture"
    },
    {
        "id": "q6",
        "query": "What parameters are passed to the rag_server query endpoint?",
        "expected_doc": "api/rag_server_endpoints.md",
        "category": "api_spec"
    }
]

def calculate_reciprocal_rank(retrieved_sources: List[str], expected_doc: str) -> float:
    """Calculates Reciprocal Rank (1/Rank) for a single query."""
    for rank, source_path in enumerate(retrieved_sources, start=1):
        if expected_doc in source_path:
            return 1.0 / rank
    return 0.0

def calculate_hit_rate(retrieved_sources: List[str], expected_doc: str) -> float:
    """Calculates Hit Rate@k."""
    return 1.0 if any(expected_doc in doc for doc in retrieved_sources) else 0.0

def calculate_context_precision(retrieved_sources: List[str], expected_doc: str) -> float:
    """Calculates Context Precision at rank positions."""
    relevant_found = 0
    precision_sum = 0.0
    for rank, source in enumerate(retrieved_sources, start=1):
        if expected_doc in source:
            relevant_found += 1
            precision_sum += relevant_found / rank
    return precision_sum / max(relevant_found, 1) if relevant_found > 0 else 0.0

def evaluate_retrieval_engine(retriever_fn: Callable, k: int = 5) -> Dict[str, Any]:
    """Executes the benchmark evaluation over EVALUATION_DATASET using the provided retriever function."""
    total_queries = len(EVALUATION_DATASET)
    mrr_total = 0.0
    hit_total = 0.0
    precision_total = 0.0
    detailed_results = []

    for item in EVALUATION_DATASET:
        start_time = time.time()
        results = retriever_fn(query=item["query"], k=k)
        latency = time.time() - start_time

        retrieved_doc_paths = [
            res.get("metadata", {}).get("source", "") if isinstance(res, dict) else str(res)
            for res in results
        ]

        rr = calculate_reciprocal_rank(retrieved_doc_paths, item["expected_doc"])
        hit = calculate_hit_rate(retrieved_doc_paths, item["expected_doc"])
        precision = calculate_context_precision(retrieved_doc_paths, item["expected_doc"])

        mrr_total += rr
        hit_total += hit
        precision_total += precision

        detailed_results.append({
            "id": item["id"],
            "query": item["query"],
            "category": item["category"],
            "expected_doc": item["expected_doc"],
            "top_1_retrieved": retrieved_doc_paths[0] if retrieved_doc_paths else None,
            "all_retrieved": retrieved_doc_paths,
            "hit_at_k": bool(hit),
            "reciprocal_rank": round(rr, 4),
            "context_precision": round(precision, 4),
            "latency_sec": round(latency, 4)
        })

    return {
        "summary": {
            "mean_reciprocal_rank": round(mrr_total / total_queries, 4),
            "hit_rate_at_k": round(hit_total / total_queries, 4),
            "mean_context_precision": round(precision_total / total_queries, 4),
            "total_queries": total_queries,
            "k": k
        },
        "details": detailed_results
    }

if __name__ == "__main__":
    print("Evaluation benchmark module configured with expanded query set.")