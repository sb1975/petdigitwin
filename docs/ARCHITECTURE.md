# PetDigiTwin Architecture

This document provides a standalone view of the PetDigiTwin system architecture.

## High-Level Diagram

```mermaid
flowchart TD
  U[Pet Owner / SPA UI] --> A[Flask API\napp.py]

  A --> E1[GET /api/pets]
  A --> E2[GET /api/pets/:id]
  A --> E3[GET /api/food-recommendations]
  A --> E4[GET /api/health-knowledge]
  A --> E5[GET /api/checkup-prediction]
  A --> E6[GET /api/find-volunteers]
  A --> E7[POST /api/query]
  A --> O1[GET /api/observability/status]
  A --> O2[POST /api/observability/feedback]
  A --> O3[GET /api/observability/self-improvement-report]

  subgraph ACT[Phase 2 - Core Action Mechanisms]
    E7 --> G[PetDigiTwin Agent\nsrc/agent.py]
    G --> T[Tool Layer\nsrc/tools.py]
  end

  subgraph GRD[Phase 2 - Knowledge and Grounding]
    M[(MongoDB Atlas\npets, volunteers, pet_foods, vet_knowledge)]
  end

  T --> M

  subgraph OBS[Phase 3 - Arize Observability and Introspection]
    OTEL[OpenTelemetry + OpenInference\nsrc/observability.py]
    PHX[Arize Phoenix\ntraces, prompts, datasets, experiments]
    MCP[Phoenix MCP Server\nruntime introspection]
    RUN[(MongoDB: agent_runs)]
    FB[(MongoDB: agent_feedback)]
  end

  G --> LLM[Gemini Model\nDirect API or Vertex SDK]
  G --> OTEL
  LLM --> G
  OTEL --> PHX
  MCP --> PHX
  E7 --> RUN
  O2 --> FB

  E1 --> M
  E2 --> M
  E3 --> T
  E4 --> T
  E5 --> T
  E6 --> T

  G --> A
  A --> U
```

## Phase 2 Mapping

- Core Action Mechanisms (Tool Use):
  - SDK tools in `src/tools.py` invoked by the agent in `src/agent.py`
  - Tool-facing APIs exposed by `app.py`
- Knowledge and Grounding:
  - MongoDB Atlas collections are the source of truth for pet, food, volunteer, and vet knowledge data
  - Agent responses are grounded with retrieved tool outputs before model reasoning

Managed-platform equivalence (if required by evaluator):
- Agent Builder Extensions  <->  SDK tool layer (`src/tools.py`)
- Agent Builder Data Stores <-> MongoDB grounding collections

## Phase 3 Mapping (Arize)

- Tracing instrumentation:
  - `src/observability.py` initializes OpenTelemetry exporter and OpenInference instrumentors
  - Agent and API spans are emitted from `src/agent.py` and `app.py`
- Phoenix destination:
  - Traces are exported to Phoenix via `PHOENIX_API_KEY` and `PHOENIX_COLLECTOR_ENDPOINT`
- Runtime introspection support:
  - Phoenix MCP server can connect to the same Phoenix project for trace/prompt/dataset introspection
- Self-improvement loop:
  - `agent_runs` captures query-level telemetry
  - `agent_feedback` captures human or judge ratings/comments
  - `/api/observability/self-improvement-report` summarizes trends and recommends tuning actions

## Runtime Flow

1. The user interacts with the SPA served from `/`.
2. The UI calls feature APIs in `app.py`.
3. For AI tasks, `/api/query` invokes `PetDigiTwinAgent`.
4. The agent calls domain tools from `src/tools.py`.
5. Tools fetch and aggregate data from MongoDB Atlas.
6. The agent combines tool output with Gemini model reasoning.
7. Flask returns structured JSON to the UI for rendering.

## Core Components

- API Layer: `app.py`
- Agent Orchestration: `src/agent.py`
- Tooling / business logic: `src/tools.py`
- Persistence: `src/db.py` + MongoDB Atlas
- UI: `src/ui.py`

## Deployment View

- Containerized with `Dockerfile`
- Runs on Google Cloud Run
- Environment-driven model path:
  - `USE_VERTEX_SDK=false`: direct Gemini API key path
  - `USE_VERTEX_SDK=true`: Vertex SDK path
