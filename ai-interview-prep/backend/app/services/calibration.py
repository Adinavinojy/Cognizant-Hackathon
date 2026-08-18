"""
Calibration Service
===================
Scores a small set of hand-rated answer examples through the live scoring
pipeline and computes Pearson and Spearman correlations between the fused
score and the human rating.

Running this turns "we built a scorer" into "we validated our scorer against
human judgment" — a meaningfully stronger claim.

Usage:
    from app.services.calibration import run_calibration
    report = run_calibration()
    # report = {
    #     "pearson_r":   0.87,
    #     "spearman_r":  0.84,
    #     "n_samples":   10,
    #     "pairs":       [{"human_score": 0.9, "fused_score": 0.82, ...}, ...]
    # }
"""

from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Hand-rated calibration dataset
# Each entry: (question_text, reference_answer, student_answer, human_score)
# human_score is in [0, 1] — 1.0 = perfect, 0.0 = completely wrong.
# These were rated by the team and should remain stable as a benchmark.
# ---------------------------------------------------------------------------
_CALIBRATION_SAMPLES: list[dict[str, Any]] = [
    {
        "question_text":    "What is the difference between a process and a thread?",
        "reference_answer": (
            "A process is an independent program in execution with its own memory space, "
            "file handles, and system resources. A thread is the smallest unit of execution "
            "within a process; threads share the same memory space and resources of the "
            "parent process. Processes are isolated from each other (inter-process "
            "communication is required), while threads communicate through shared memory. "
            "Context switching between threads is faster than between processes because "
            "threads share the same address space. However, a bug in one thread can corrupt "
            "the shared memory of the whole process."
        ),
        "student_answer": (
            "A process is a program running on the OS. A thread is a lighter execution unit "
            "inside a process. Threads share memory, processes don't. Threads are faster to "
            "switch between because they share the same address space."
        ),
        "human_score": 0.80,
    },
    {
        "question_text":    "What is the difference between a process and a thread?",
        "reference_answer": (
            "A process is an independent program in execution with its own memory space, "
            "file handles, and system resources. A thread is the smallest unit of execution "
            "within a process; threads share the same memory space and resources of the "
            "parent process. Processes are isolated from each other (inter-process "
            "communication is required), while threads communicate through shared memory. "
            "Context switching between threads is faster than between processes because "
            "threads share the same address space. However, a bug in one thread can corrupt "
            "the shared memory of the whole process."
        ),
        "student_answer": "Processes and threads are both ways to run code at the same time.",
        "human_score": 0.20,
    },
    {
        "question_text":    "Explain the CAP theorem.",
        "reference_answer": (
            "The CAP theorem states that a distributed system can guarantee at most two of "
            "three properties simultaneously: Consistency (every read receives the most "
            "recent write or an error), Availability (every request receives a non-error "
            "response, though it may not be the latest), and Partition Tolerance (the system "
            "continues operating despite arbitrary network partitions). In practice, network "
            "partitions are unavoidable, so distributed systems must choose between "
            "consistency (CP) and availability (AP) when a partition occurs. Examples: "
            "HBase is CP; Cassandra and DynamoDB are AP."
        ),
        "student_answer": (
            "CAP theorem says distributed systems can only guarantee two of three: "
            "Consistency, Availability, Partition tolerance. Since partitions always happen "
            "in real networks, you trade off between consistency and availability. "
            "Cassandra favors availability, HBase favors consistency."
        ),
        "human_score": 0.90,
    },
    {
        "question_text":    "Explain the CAP theorem.",
        "reference_answer": (
            "The CAP theorem states that a distributed system can guarantee at most two of "
            "three properties simultaneously: Consistency (every read receives the most "
            "recent write or an error), Availability (every request receives a non-error "
            "response, though it may not be the latest), and Partition Tolerance (the system "
            "continues operating despite arbitrary network partitions). In practice, network "
            "partitions are unavoidable, so distributed systems must choose between "
            "consistency (CP) and availability (AP) when a partition occurs. Examples: "
            "HBase is CP; Cassandra and DynamoDB are AP."
        ),
        "student_answer": "CAP stands for something about databases being consistent and available.",
        "human_score": 0.15,
    },
    {
        "question_text":    "What is a hash map and what is its average time complexity for lookup?",
        "reference_answer": (
            "A hash map (also called a hash table or dictionary) is a data structure that "
            "stores key-value pairs. It uses a hash function to compute an index into an "
            "array of buckets, where the value is stored. Average-case time complexity for "
            "lookup, insertion, and deletion is O(1) because the hash function maps keys "
            "to buckets in constant time. Worst-case is O(n) when all keys hash to the "
            "same bucket (collision). Good hash functions and load-factor management (e.g. "
            "resizing when load factor > 0.75) keep performance near O(1) in practice."
        ),
        "student_answer": (
            "A hash map stores key-value pairs. It uses a hash function to find the bucket. "
            "Lookup is O(1) on average, O(n) worst case due to collisions."
        ),
        "human_score": 0.75,
    },
    {
        "question_text":    "What is a hash map and what is its average time complexity for lookup?",
        "reference_answer": (
            "A hash map (also called a hash table or dictionary) is a data structure that "
            "stores key-value pairs. It uses a hash function to compute an index into an "
            "array of buckets, where the value is stored. Average-case time complexity for "
            "lookup, insertion, and deletion is O(1) because the hash function maps keys "
            "to buckets in constant time. Worst-case is O(n) when all keys hash to the "
            "same bucket (collision). Good hash functions and load-factor management (e.g. "
            "resizing when load factor > 0.75) keep performance near O(1) in practice."
        ),
        "student_answer": "Hash maps let you store data by key. They're fast.",
        "human_score": 0.25,
    },
    {
        "question_text":    "Explain the difference between SQL and NoSQL databases.",
        "reference_answer": (
            "SQL databases are relational: data is stored in tables with a fixed schema, "
            "and relationships between tables are enforced via foreign keys. They support "
            "ACID transactions. Examples: PostgreSQL, MySQL. "
            "NoSQL databases are non-relational: they can be document, key-value, column-family, "
            "or graph stores, and they are schema-flexible. They typically sacrifice some ACID "
            "guarantees for horizontal scalability and high availability. Examples: MongoDB "
            "(document), Redis (key-value), Cassandra (column-family). The choice depends on "
            "the data model, consistency requirements, and scale."
        ),
        "student_answer": (
            "SQL is relational, uses tables and schemas, supports ACID. NoSQL is non-relational "
            "and can be document or key-value. SQL is for structured data, NoSQL for unstructured "
            "or flexible data at scale. PostgreSQL is SQL; MongoDB is NoSQL."
        ),
        "human_score": 0.85,
    },
    {
        "question_text":    "Explain the difference between SQL and NoSQL databases.",
        "reference_answer": (
            "SQL databases are relational: data is stored in tables with a fixed schema, "
            "and relationships between tables are enforced via foreign keys. They support "
            "ACID transactions. Examples: PostgreSQL, MySQL. "
            "NoSQL databases are non-relational: they can be document, key-value, column-family, "
            "or graph stores, and they are schema-flexible. They typically sacrifice some ACID "
            "guarantees for horizontal scalability and high availability. Examples: MongoDB "
            "(document), Redis (key-value), Cassandra (column-family). The choice depends on "
            "the data model, consistency requirements, and scale."
        ),
        "student_answer": "SQL uses tables. NoSQL doesn't. NoSQL is newer and better for big data.",
        "human_score": 0.20,
    },
    {
        "question_text":    "What is a REST API?",
        "reference_answer": (
            "REST (Representational State Transfer) is an architectural style for designing "
            "networked applications. A RESTful API uses HTTP methods (GET, POST, PUT, DELETE, "
            "PATCH) to perform CRUD operations on resources identified by URIs. Key constraints "
            "include: statelessness (no client session stored server-side), uniform interface, "
            "client-server separation, and cacheability. REST APIs typically exchange data in "
            "JSON or XML format. They are widely used because they are simple, scalable, and "
            "work well with standard HTTP infrastructure."
        ),
        "student_answer": (
            "A REST API is an interface for communication between client and server using HTTP. "
            "It's stateless, uses standard HTTP methods like GET and POST, and resources are "
            "identified by URLs. Data is usually exchanged as JSON."
        ),
        "human_score": 0.80,
    },
    {
        "question_text":    "What is a REST API?",
        "reference_answer": (
            "REST (Representational State Transfer) is an architectural style for designing "
            "networked applications. A RESTful API uses HTTP methods (GET, POST, PUT, DELETE, "
            "PATCH) to perform CRUD operations on resources identified by URIs. Key constraints "
            "include: statelessness (no client session stored server-side), uniform interface, "
            "client-server separation, and cacheability. REST APIs typically exchange data in "
            "JSON or XML format. They are widely used because they are simple, scalable, and "
            "work well with standard HTTP infrastructure."
        ),
        "student_answer": "REST API is a type of API that websites use to send data.",
        "human_score": 0.25,
    },
]


def run_calibration() -> dict:
    """
    Scores every calibration sample through the live scoring pipeline,
    then computes Pearson and Spearman correlation between fused_score
    and human_score.

    Returns:
        {
          "pearson_r":  float,
          "spearman_r": float,
          "n_samples":  int,
          "pairs": [
            {
              "question":     str,
              "human_score":  float,
              "fused_score":  float,
              "similarity_score": float,
              "concept_match_score": float,
              "llm_judge_score": float | None,
            },
            ...
          ]
        }
    """
    from app.services.scoring import score_answer

    pairs = []
    human_scores  = []
    fused_scores  = []

    for sample in _CALIBRATION_SAMPLES:
        try:
            result = score_answer(
                answer_text=sample["student_answer"],
                reference_answer=sample["reference_answer"],
                question_text=sample["question_text"],
            )
            pair = {
                "question":           sample["question_text"][:80],
                "student_answer":     sample["student_answer"][:80],
                "human_score":        sample["human_score"],
                "fused_score":        result["fused_score"],
                "similarity_score":   result["similarity_score"],
                "concept_match_score": result["concept_match_score"],
                "llm_judge_score":    result.get("llm_judge_score"),
            }
            pairs.append(pair)
            human_scores.append(sample["human_score"])
            fused_scores.append(result["fused_score"])
        except Exception as exc:  # noqa: BLE001
            log.warning("Calibration sample failed: %s", exc)

    if len(human_scores) < 2:
        return {
            "pearson_r":  None,
            "spearman_r": None,
            "n_samples":  len(human_scores),
            "pairs":      pairs,
            "error":      "Not enough successful samples to compute correlation.",
        }

    try:
        from scipy import stats as sp_stats
        pearson_r,  _ = sp_stats.pearsonr(human_scores, fused_scores)
        spearman_r, _ = sp_stats.spearmanr(human_scores, fused_scores)
    except Exception as exc:
        log.warning("Correlation computation failed: %s", exc)
        pearson_r  = None
        spearman_r = None

    return {
        "pearson_r":  round(float(pearson_r),  4) if pearson_r  is not None else None,
        "spearman_r": round(float(spearman_r), 4) if spearman_r is not None else None,
        "n_samples":  len(human_scores),
        "pairs":      pairs,
    }
