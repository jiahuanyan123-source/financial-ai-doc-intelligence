# Lesson 01: Build AI From Task, Data, Baseline, Evaluation

The first mistake many AI beginners make is starting with the model.

A serious AI project starts with five questions:

1. What task are we solving?
2. What input does the system receive?
3. What output should it produce?
4. How do we know whether the output is correct?
5. What simple baseline can we build before using a model?

For financial AI, this discipline matters more than usual. A fluent answer is
not enough. The system must preserve facts, numbers, citations, risk logic, and
reviewability.

## Our First Task

Input:

- an issuer credit note in text or Markdown format.

Output:

- extracted issuer facts,
- calculated credit metrics,
- risk flags with source-line citations,
- analyst questions for follow-up,
- a Markdown memo and JSON artifact.

## Why No LLM Yet

This v0 project does not call an LLM. That is deliberate.

Before adding a model, we need a baseline that is:

- deterministic,
- inspectable,
- cheap to run,
- easy to test,
- good enough to expose real failure cases.

When we add LLM/RAG later, this baseline becomes the benchmark we must beat.

## Core AI Concept

An AI system is not just a model. It is a pipeline:

```text
raw document -> parsed evidence -> structured facts -> derived metrics -> risk logic -> report -> evaluation
```

LLMs can improve several stages, but they should not erase the pipeline.

## Your First Mental Model

Think like an AI builder, not only a model user:

- The document is data.
- Each line is evidence.
- Each extracted field is a claim.
- Each metric is a calculation.
- Each risk flag needs a reason.
- Each report sentence should be traceable.

This is the foundation of trustworthy financial AI.

