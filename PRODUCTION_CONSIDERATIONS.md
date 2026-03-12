# Production Considerations

This document outlines what would need to change to take this 
HR AI Assistant from a working prototype to a production system 
serving 3,000+ employees.

---

## 1. Input Validation

**Current:** Hardcoded blocklist of phrases.

**Production:** 
- Use OpenAI Moderation API (free) as first pass
- LLM-based intent classifier as second pass
- Hardcoded list catches obvious attacks only
- Sophisticated attacks bypass simple string matching

---

## 2. Vector Search

**Current:** NumPy cosine similarity — works for small datasets.

**Production:**
- Replace with pgvector (PostgreSQL extension) or Pinecone
- NumPy loads everything into memory — fails at scale
- pgvector persists index to disk — survives server restarts
- Pinecone scales to millions of documents with millisecond search

---

## 3. Sensitive Data Architecture

**Current:** Employee records including SSNs loaded into knowledge base.

**Production:**
- SSNs and truly sensitive PII never enter the chatbot knowledge base
- Sensitive records stay in dedicated HR systems (Workday, SAP)
- Chatbot handles policies and general HR data only
- PII scanning at upload time with auto-redaction not just rejection

---

## 4. Authentication

**Current:** Hardcoded username/password in app.py.

**Production:**
- SSO integration with company Active Directory or Okta
- JWT tokens with expiration
- MFA for admin accounts
- Session management with proper timeout

---

## 5. Role Based Access Control

**Current:** Two hardcoded roles — admin and employee.

**Production:**
- Granular roles — employee, manager, HR, HR admin, executive
- Managers see their direct reports data only
- Executives see aggregate data
- Role tied to Active Directory groups
- Document-level permissions — tag chunks as PUBLIC or RESTRICTED
- Restricted chunks excluded from employee searches at query time

---

## 6. LLM and Data Privacy

**Current:** All queries sent to OpenAI API.

**Production:**
- Sign OpenAI Enterprise Data Processing Agreement
- OpenAI Enterprise guarantees data not used for training
- For highly sensitive data — evaluate on-premise LLM (LLaMA, Mistral)
- On-premise means zero data leaves company network

---

## 7. Audit Logging

**Current:** No logging of who asked what.

**Production:**
- Every query logged with user ID, timestamp, question, answer
- Admin queries logged separately with stricter retention
- Logs stored in tamper-proof audit trail
- Required for compliance in regulated industries
- Alerts for suspicious query patterns

---

## 8. Caching

**Current:** Every question hits OpenAI API.

**Production:**
- Cache common questions and answers (Redis)
- Semantic cache — similar questions return cached answer
- Reduces API costs significantly at 3k+ users
- Reduces latency from 2-3 seconds to milliseconds for cached queries

---

## 9. Scalability

**Current:** Single Flask server, single process.

**Production:**
- Deploy behind load balancer
- Multiple Flask workers (Gunicorn)
- Containerize with Docker
- Orchestrate with Kubernetes for auto-scaling
- Separate embedding service from query service
- Async processing for non-urgent requests

---

## 10. Knowledge Base Management

**Current:** Manual file upload, re-indexes entire knowledge base.

**Production:**
- Incremental indexing — only re-index changed documents
- Document versioning — track policy changes over time
- Scheduled re-indexing when documents update
- HR workflow integration — policy approval triggers automatic update
- Document expiry — flag outdated policies automatically

---

## 11. Monitoring and Observability

**Current:** No monitoring.

**Production:**
- Track response latency per query
- Monitor API costs per day/week/month
- Alert on spike in thumbs down ratings
- Track query volume by department
- Measure answer quality with automated evals
- Dashboard for engineering team separate from HR dashboard

---

## 12. Answer Quality

**Current:** Thumbs up/down feedback only.

**Production:**
- Automated evaluation pipeline
- Sample answers reviewed by HR weekly
- A/B test different system prompts
- Track which chunks get retrieved most — optimize knowledge base
- Confidence scoring — flag low confidence answers for human review

---

## Summary

The prototype proves the architecture works. 
Production requires treating this as a mission-critical system —
because for 3,000 employees asking HR questions daily, 
a wrong answer about benefits or PTO is a real liability.

Build the right foundation first. Retrofitting security and 
scalability is always harder than building it in from the start.
