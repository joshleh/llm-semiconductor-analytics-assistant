# Evaluation and Quality Criteria

This document describes how the quality and usefulness of the LLM-powered assistant are evaluated.

The goal of evaluation is not to measure model accuracy in isolation, but to assess whether the system provides reliable, traceable, and actionable support for semiconductor engineering workflows.

---

## What “Good” Looks Like

A high-quality response should:
- Be grounded in retrieved source material rather than hallucinated knowledge
- Clearly reference the sources used to generate the answer
- Use precise, domain-appropriate language
- Provide concise explanations that support engineering decision-making
- Avoid overconfidence when evidence is limited

---

## When the Assistant Should Say “Insufficient Data”

The assistant should explicitly state that it lacks sufficient information when:
- Retrieved context does not address the user’s question
- Available sources are outdated, incomplete, or contradictory
- The question requires data or tools that are not currently integrated
- The user asks for real-time, proprietary, or operational data

In these cases, the assistant should describe what additional data or context would be needed.

---

## Basic Failure Modes

Known failure modes include:
- Retrieving semantically similar but contextually irrelevant documents
- Over-generalizing from a small or biased set of sources
- Misinterpreting domain-specific terminology
- Failing to distinguish correlation from causation
- Providing answers when abstention would be more appropriate

These failure modes inform future improvements to retrieval, prompting, and tool integration.