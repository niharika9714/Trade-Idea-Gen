# AI Investment Research Platform

Synthetic investment-research chatbot prototype.

The project demonstrates an agentic architecture where the AI
retrieves evidence directly from native data sources rather than
depending on mandatory document chunking, embeddings, or a vector DB.

## Planned data sources

- PDF research reports
- PowerPoint presentations
- Word documents
- Outlook emails
- Email attachments
- News stored as XML
- End-of-day market data in SQL
- Internal pricing / valuation API responses

## Planned architecture

User Query
    ↓
Agent / LLM
    ↓
Tool Selection
    ↓
Native Data Sources
    ↓
Evidence + Provenance
    ↓
Calculations / Reasoning
    ↓
Answer + Citations

All generated research data will be explicitly synthetic.
