# Google GenAI Agent Development Kit (ADK) 2.0 Specifications

The GenAI Agent Development Kit (ADK) 2.0 is Google's code-first orchestration framework designed specifically to build, evaluate, and deploy multi-agent systems, deterministic workflows, and state-driven conversational graphs.

---

## 1. Core Architecture Concepts

ADK 2.0 transitions from general-purpose LLM call chains to structured, multi-turn state machines. It defines three principal entities:

### 1.1 Session State
* Session state behaves as the persistence layer across conversation turns. 
* In python-adk, agents and tools manipulate this state through contextual arguments (such as `ToolContext` or `CallbackContext`):
  ```python
  def my_tool(context: ToolContext, parameter: str):
      state = context.state
      state["last_parameter"] = parameter
      return {"result": "success"}
  ```

### 1.2 Agents
* An `Agent` is a node configured with a role, system instructions, and a set of bound tools. 
* Unlike general LLMs, ADK agents are task-bound and delegate execution when their specific trigger conditions are satisfied.

### 1.3 Workflows
* A `Workflow` connects agents and tools using directed edges (`edges=[("START", agent_a, agent_b)]`).
* Workflows support sequential pipelines, loops, conditional routing, and fan-out/fan-in topologies.
* The state flows between nodes, and changes are committed via transactional session deltas.

---

## 2. ADK 2.0 vs Custom Python Agent Graphs

In production environments, developers choose between two deployment pathways for the ADK pattern:

| Feature | Official `google-adk` Package | Custom Pydantic Graph (Current Code) |
| :--- | :--- | :--- |
| **Orchestration** | Framework-driven (`Workflow` / `edges`) | Imperative code control (`Orchestrator.run()`) |
| **State Validation** | Key-value dictionary (`context.state`) | Rigid Pydantic model (`ConversationState`) |
| **Dependencies** | Requires `google-adk` and gRPC services | Pure Python, lightweight and zero-overhead |
| **Inter-agent routing** | Graph engine handles edge callbacks | Class methods (`can_execute` / `execute`) |

---

## 3. Best Practices for ADK Graph Design
1. **Deterministic Edge Triggers**: Avoid letting the LLM decide routing unless necessary. Use deterministic rules in code (e.g. `if state.image_uploaded: route_to_vision`).
2. **Strict State Schema**: Define a typed model (like `ConversationState` using Pydantic) to avoid runtime key errors in long-running sessions.
3. **Decoupled Business Tools**: Keep utility functions (like routes, weather, and databases) decoupled in separate modules (`app/tools/`) so they can be tested independently of agent logic.
