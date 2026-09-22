# FinTrace Architecture

## Purpose

FinTrace is an evidence-first Retrieval-Augmented Generation system
for answering questions over financial filings.

## Core pipeline

```text
Financial Filings
       ↓
    Ingestion
       ↓
Parsing / Normalization
       ↓
     Chunking
       ↓
 Dense + Sparse Indexing
       ↓
     Retrieval
       ↓
       RRF
       ↓
    Reranking
       ↓
 Evidence Context
       ↓
    Generation
       ↓
 Claim Extraction
       ↓
 Claim Verification
       ↓
 Final Answer + Citations