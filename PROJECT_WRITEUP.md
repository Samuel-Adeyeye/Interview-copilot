# Interview Copilot: AI-Powered Technical Interview Prep

## Problem Statement

Technical interview preparation is fragmented and ineffective. Candidates face three critical gaps:
1. **Generic preparation doesn't work**: LeetCode and similar platforms provide one-size-fits-all practice that ignores company-specific interview styles, tech stacks, and cultural expectations.
2. **No intelligent feedback**: Existing tools give binary pass/fail results without explaining *why* solutions work, analyzing complexity, or identifying improvement areas.
3. **Zero personalisation**: No system tracks progress across sessions, identifies skill gaps, or adapts difficulty based on candidate performance.

**Why this matters:**
* A large number of engineers report that interview anxiety significantly impacts performance.
* Professional interview coaching is expensive, making it inaccessible.
* Failed interviews often mean 2-3 additional months of job searching.

**The Insight**: Interview success requires three things working together: (1) company-specific research, (2) expert technical feedback on code, and (3) longitudinal progress tracking. No existing tool integrates all three at an affordable price.

## Why Agents?

**Specialised Intelligence Required**
Each preparation aspect needs distinct expertise:
* **Research**: Needs web search + synthesis + pattern recognition.
* **Code Evaluation**: Needs execution + complexity analysis + pedagogical feedback.
* **Progress Tracking**: Needs data analysis + skill assessment + personalization.
→ **Solution**: Three specialised agents, each expert in their domain, coordinated by an orchestrator.

**Dynamic Context Awareness**
Every candidate-company pair is unique (e.g., Netflix backend vs. Startup frontend).
→ **Solution**: Agents use tools (search, code execution) for real-time, context-aware responses rather than static content.

**Complex Multi-Step Workflows**
Research Company → Select Questions → Practice → Execute Code → Evaluate → Provide Feedback → Track Progress.
→ **Solution**: Orchestrator coordinates agents through workflows with state management and intelligent routing.

## System Architecture

**Three Specialized Agents**

1. **ResearchAgent**
   * **Input**: Job description + company name
   * **Process**: Searches web using Google Search (via ADK) for company info, interview experiences, and tech stack. Synthesizes findings into a structured research packet.
   * **Output**: Company overview, interview process, tech stack, preparation tips.

2. **TechnicalAgent**
   * **Input**: JD requirements OR submitted code
   * **Process (Selection)**: Generates relevant problems based on difficulty and company style using the **Gemini 2.0 Flash (Experimental)** model for high-speed generation.
   * **Process (Evaluation)**:
     * Executes code via **BuiltInCodeExecutor** (sandboxed Python execution).
     * LLM analyzes correctness, complexity (time/space), and code quality.
     * Generates detailed feedback with improvement suggestions.
   * **Output**: Selected questions OR comprehensive evaluation with scores.

3. **CompanionAgent**
   * **Input**: Session data + user history
   * **Process**: Monitors real-time session progress, analyzes performance patterns, and compares to historical data.
   * **Output**: Session summaries, progress analysis, personalized recommendations.

**Key Design Decisions**
* **Google ADK for Orchestration**: Production-ready framework with built-in state management, streaming, and automatic tool integration.
* **Structured Output (Pydantic)**: Guarantees type-safe, validated responses (reduced parsing errors from 15% → 0%).
* **Hybrid Memory**: In-memory for live sessions (speed) + ADK MemoryService for historical data (semantic search) + PostgreSQL for structured metadata.
* **Tool-First Design**: Agents use real APIs (search, code execution) to eliminate hallucinations.

## Demo & Deployment

* **YouTube Demo**: [Link](https://youtu.be/tiSHlahG5FQ)
* **Streamlit UI**: [https://interview-copilot-agent.streamlit.app/](https://interview-copilot-agent.streamlit.app/)
* **API Endpoint**: `https://interview-copilot-api-staging-270912131800.us-central1.run.app/`

## The Build

### Technology Stack

**Core Framework**:
* **Python 3.11** + **FastAPI** (async REST API)
* **Google Agent Development Kit (ADK) 0.2+** (multi-agent orchestration)
* **Pydantic 2.9+** (structured outputs)

**LLM & AI**:
* **Google Gemini 2.0 Flash (Experimental)**: Optimized for speed and reasoning.
* **Temperature**: 0.7 for research/synthesis, 0.3 for evaluation.

**Tools & ADK Integration**:
* **Google Search**: Built-in ADK tool for real-time company research.
* **BuiltInCodeExecutor**: ADK tool for sandboxed code execution.
* **Judge0 API**: Optional multi-language execution support.

**Infrastructure**:
* **Google Cloud Run**: Serverless container deployment (auto-scaling).
* **Google Cloud Build**: CI/CD pipeline with automated testing.
* **Secret Manager**: Secure API key management.

### Architecture Evolution: LangChain → Google ADK

**Why We Migrated**:
The initial implementation used LangChain, which was great for prototyping but had limitations for production:
* **Manual State Management**: Required explicit handling across agent transitions.
* **Limited Streaming**: Complex to implement real-time response streaming.
* **Dependency Issues**: Legacy packages caused build failures.

**ADK Migration Benefits**:
* **36% Code Reduction**: Orchestrator complexity significantly decreased.
* **Automatic State Management**: ADK handles session state and context propagation.
* **Native Streaming**: Built-in SSE support for real-time responses.
* **Production-Ready**: Enterprise-grade features (monitoring, error handling).

## Future Roadmap

**Immediate Priorities**
* **Behavioral Interview Agent**: STAR framework evaluation and soft skills assessment.
* **Voice Interview Mode**: Speech-to-text/Text-to-speech for realistic practice.

**Medium-Term**
* **Advanced Progress Tracking**: Skill proficiency graphs and peer benchmarking.
* **Company-Specific Training**: RAG pipeline on engineering blogs using ADK MemoryService.

**Long-Term**
* **Collaborative Features**: Peer mock interviews and mentor dashboards.
* **Panel Interview Simulation**: Multiple agents simulating different interviewer personalities.
