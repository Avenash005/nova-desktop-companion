# NOVA — Product Requirements Document (PRD)

**Product:** NOVA — Neural Desktop Companion  
**Repository:** [Avenash005/nova-desktop-companion](https://github.com/Avenash005/nova-desktop-companion)  
**Document status:** Product definition aligned to the current repository, with future requirements clearly marked  
**Version basis:** Current `main` branch; package metadata v1.2.1  
**Related documents:** [HLD.md](./HLD.md) · [LLD.md](./LLD.md)

## 1. Product overview

NOVA is a configurable AI desktop companion that combines a conversational assistant with an animated Live2D character. Users can interact by text and, when configured, by voice. NOVA can be displayed in a browser, a regular desktop window, or a transparent floating desktop-pet window.

The product is intended to make AI assistance feel present and approachable while allowing users to choose local or external AI providers, customize the character persona, and retain conversation history locally.

## 2. Problem statement

Most AI assistants are accessed through a conventional browser or chat interface. That experience can feel disconnected from the user's working environment, and some services require sending prompts or audio to hosted providers. Users who want a persistent animated companion, provider flexibility, or more control over local processing need a configurable desktop-first experience.

NOVA addresses this by combining:
- A floating animated desktop companion and standard web interface.
- Text and optional voice conversation.
- A configurable character/persona and Live2D model.
- Replaceable LLM, speech recognition, and speech synthesis providers.
- Local conversation history and optional tool integration.

## 3. Product vision

**Make a helpful, expressive AI companion available on the desktop without forcing users into one model provider or one interaction mode.**

NOVA should be:
- **Approachable:** warm, respectful, concise, and character-driven.
- **Useful:** able to help with learning, conversation, and everyday planning.
- **Configurable:** adaptable to user-selected models, voices, and characters.
- **Privacy-conscious:** transparent about local versus remote processing.
- **Non-intrusive:** the companion should support the user's work rather than disrupt it.

## 4. Goals and success measures

### 4.1 Product goals

1. Deliver reliable text chat in a desktop/browser interface.
2. Provide an optional floating companion presentation with Live2D animation.
3. Support a voice pipeline when users configure compatible ASR and TTS engines.
4. Let users configure character identity and supported AI providers without code changes.
5. Preserve and manage conversation history on the local machine.
6. Support interruption and responsive turn-taking.
7. Allow optional, explicitly configured MCP tool integrations.

### 4.2 Success measures

The following are proposed product targets for release validation; they are not claims of measured production performance.

| Measure | Proposed target / definition |
|---|---|
| Desktop launch reliability | At least 95 successful launches in 100 clean test runs on supported test machines |
| Text interaction | A successful text prompt produces a visible response in the configured happy-path provider test |
| First response latency | Establish baseline by hardware/provider; target p95 under 5 seconds for a small local model under reference conditions |
| Voice interaction | For supported ASR+LLM+TTS combinations, 9 of 10 scripted voice scenarios complete end-to-end |
| Interruption | Active response can be stopped in the supported single-client scenario without requiring app restart |
| History integrity | Create, save, list, reload, and delete test history without data loss in 100 consecutive test cycles |
| Provider selection | Every provider advertised in the configuration docs has a smoke test or is explicitly labeled experimental |
| Privacy transparency | UI/documentation clearly identifies when configured providers may send data off-device |

These values should be revisited after collecting repeatable benchmark data across a defined hardware matrix.

## 5. Target users and personas

### Persona A — Student / learner
Wants a friendly companion for explanations, revision, and study planning. Values easy access, conversational continuity, and voice interaction when hands-free.

### Persona B — Developer / knowledge worker
Wants a quick assistant while coding or working. Prefers a small floating interface, keyboard-first text chat, and the ability to use a local model.

### Persona C — AI hobbyist / power user
Wants to experiment with local and hosted LLMs, voices, personas, and tool integrations. Values provider modularity and editable configuration.

### Persona D — Privacy-conscious user
Wants to understand where prompts, audio, images, and history are processed and prefers local providers when available.

## 6. User stories

- As a user, I want to launch NOVA as a floating desktop pet so that I can interact without keeping a full browser tab open.
- As a user, I want a normal desktop window or browser mode so that I can choose the presentation that suits my workflow.
- As a user, I want to send text and receive a streamed response so that the interaction feels responsive.
- As a user, I want to speak to NOVA when ASR is configured so that I can interact hands-free.
- As a user, I want NOVA to speak responses when TTS is configured so that the character feels conversational.
- As a user, I want to interrupt a response so that I can correct myself or change direction.
- As a user, I want to change the character configuration so that the companion reflects my preferences.
- As a user, I want to select supported LLM and speech providers so that I can balance cost, speed, quality, and privacy.
- As a user, I want to revisit or delete previous conversations so that I can manage continuity and privacy.
- As a user, I want to enable tools deliberately so that I control what capabilities the assistant can access.

## 7. Functional requirements

Priority definitions: **P0** = essential for a usable core release; **P1** = important enhancement; **P2** = optional/advanced.

### 7.1 Launch and presentation

| ID | Priority | Requirement | Acceptance criteria |
|---|---|---|---|
| FR-001 | P0 | The application shall start its backend when launched in a desktop mode and no compatible server is already running, unless server startup is disabled. | Given no server is running, launching the desktop script starts the backend and waits for readiness before opening the client. |
| FR-002 | P0 | The application shall provide browser, regular-window, and floating-pet presentation modes. | Each mode opens the frontend at the configured local server URL; pet mode requests transparent/frameless/on-top behavior. |
| FR-003 | P1 | The launcher shall allow users to configure host, port, and desktop-window dimensions. | Command-line options are parsed and passed to readiness checks/window creation. |
| FR-004 | P0 | The server shall serve the frontend and required static assets. | Frontend, avatars, backgrounds, Live2D models, cache, and web-tool paths respond when corresponding assets exist. |

### 7.2 Conversation

| ID | Priority | Requirement | Acceptance criteria |
|---|---|---|---|
| FR-005 | P0 | Users shall be able to submit text prompts. | A valid `text-input` message reaches the conversation worker and results in response messages. |
| FR-006 | P0 | The system shall stream or incrementally deliver generated output where supported by the selected agent/provider. | The client receives display/output events without waiting for the entire response when the provider streams. |
| FR-007 | P1 | Users shall be able to include supported image data with a message. | A valid image data URL is included in the agent request for providers that support image input; unsupported providers fail clearly. |
| FR-008 | P0 | Users shall be able to interrupt an active response. | An interruption message cancels the active task and the agent receives the interruption context. |
| FR-009 | P1 | The system shall support proactive companion speech when enabled/configured. | A proactive-speech request loads the configured prompt or a documented fallback and is excluded from memory/history when flagged. |

### 7.3 Voice and character

| ID | Priority | Requirement | Acceptance criteria |
|---|---|---|---|
| FR-010 | P1 | The system shall accept microphone audio when a compatible ASR configuration is enabled. | A supported audio flow produces recognized text and routes it through conversation processing. |
| FR-011 | P1 | The system shall detect speech activity when a VAD provider is configured. | Configured VAD processes audio chunks and emits the expected speech/pause behavior. |
| FR-012 | P1 | The system shall synthesize speech when a compatible TTS engine is configured. | A valid response segment produces playable audio and the associated display text. |
| FR-013 | P1 | The character shall display configured model/avatar information and supported expressions/actions. | The initial config payload includes character/model metadata and response actions are consumable by the frontend. |
| FR-014 | P1 | The system shall preprocess text before TTS according to configured filters. | Configured bracket/special-character filters are applied to speech text without unintentionally removing display text. |

### 7.4 Personalization and providers

| ID | Priority | Requirement | Acceptance criteria |
|---|---|---|---|
| FR-015 | P0 | Users shall be able to configure character name, persona prompt, avatar, and Live2D model through configuration. | A valid configuration loads and the client receives the selected character/model metadata. |
| FR-016 | P0 | Users shall be able to select a supported agent and LLM provider through configuration. | The configured factories instantiate the provider or return a clear configuration/provider error. |
| FR-017 | P1 | Users shall be able to select supported ASR, TTS, and VAD providers independently. | Each selected provider is created from its corresponding typed settings; disabled ASR/VAD are handled without initialization. |
| FR-018 | P1 | Users shall be able to list and switch among alternative character configurations. | Client requests receive available configuration entries and a valid switch updates the active context. |
| FR-019 | P1 | The product shall support optional MCP tool integrations. | When enabled with trusted configured servers, tool metadata is made available to the agent and tool execution is routed through the configured MCP components. |

### 7.5 History and multi-user interaction

| ID | Priority | Requirement | Acceptance criteria |
|---|---|---|---|
| FR-020 | P0 | Users shall be able to create, list, retrieve, and delete conversation histories. | Each operation updates local history files and returns the corresponding client response. |
| FR-021 | P1 | The system shall restore agent working memory from a selected history. | Loading a history retrieves its messages and passes them to the agent memory loader. |
| FR-022 | P1 | The system shall support chat groups with member add/remove and group information operations. | Group state is updated and the client receives a group-update message. |
| FR-023 | P1 | Group responses shall be broadcast to the applicable group members. | A group conversation event is sent through the group broadcast path and respects the active group membership. |
| FR-024 | P1 | The system shall clean up active tasks and connection state after disconnect. | Disconnect cancels the active task and removes the client from runtime tracking. |

## 8. Non-functional requirements

| ID | Category | Requirement |
|---|---|---|
| NFR-001 | Performance | The WebSocket receive loop must remain responsive while conversation work executes asynchronously. |
| NFR-002 | Performance | Sentence segmentation and provider streaming should be used where supported to reduce perceived response latency. |
| NFR-003 | Reliability | Invalid configuration must fail visibly during startup rather than silently creating a partially initialized runtime. |
| NFR-004 | Reliability | Disconnects, provider errors, and malformed client messages must be logged and handled without corrupting unrelated sessions. |
| NFR-005 | Security | The default deployment should bind to localhost; remote deployment requires authentication, TLS, and restrictive CORS/origin policy. |
| NFR-006 | Privacy | The product must explain that remote LLM/ASR/TTS/translation/MCP services may receive submitted data. |
| NFR-007 | Privacy | Conversation history must remain in the documented local storage location unless a separately configured integration sends data elsewhere. |
| NFR-008 | Maintainability | Provider integrations must use the appropriate interfaces/factories and typed configuration. |
| NFR-009 | Portability | The browser mode should work wherever the Python backend and supported browser are available; desktop-window behavior is platform-dependent. |
| NFR-010 | Accessibility | Core text conversation and controls should remain usable without relying solely on Live2D animation or audio. |
| NFR-011 | Compatibility | Runtime dependency and Python version constraints must match package metadata and installation documentation. |
| NFR-012 | Observability | Startup, provider initialization, connection failures, and runtime errors must be diagnosable through structured logs. |

## 9. User experience requirements

1. The companion should be visually present but not obstruct the user's work.
2. Pet mode should have a clear draggable area and should not unexpectedly steal focus.
3. Text must remain visible when audio is disabled or unavailable.
4. Loading, disconnected, provider-error, and microphone-permission states should be communicated clearly.
5. The user must be able to stop speech/response output without restarting the application.
6. Character configuration names and model information should be surfaced consistently.
7. Voice use should be opt-in through configuration and runtime permission, not silently activated by an unrelated action.

## 10. Privacy, security, and trust requirements

- Do not store secrets in tracked configuration files; use environment variables or an appropriate local secret store.
- Show which configured components are local and which use remote APIs.
- Do not imply that data stays on-device when the user selects a hosted provider.
- Keep MCP servers disabled unless the user explicitly configures and enables them.
- Avoid running arbitrary tools without a visible capability definition and user-understandable purpose.
- Provide a clear way to remove local conversation histories.
- Tighten permissive CORS settings and add authentication before supporting LAN/public exposure.
- Apply size limits and validation to inbound audio, image, and JSON payloads as the product matures.

## 11. Scope

### 11.1 Current repository scope

The repository currently contains the desktop launcher modes, FastAPI server, frontend/static serving, WebSocket message routing, configurable character and provider setup, an agent abstraction with a basic memory agent, provider factories for model and speech engines, local JSON conversation history, interruption handling, chat-group handling, optional MCP components, and model training/evaluation assets.

### 11.2 Recommended next-release scope

- Formalize the WebSocket protocol with versioned schemas and compatibility tests.
- Add clear in-app provider status/error feedback.
- Add history retention/export/delete UX and explicit privacy messaging.
- Add a supported-provider compatibility matrix and per-provider smoke tests.
- Review session engine ownership to ensure independent conversation memory and safe concurrent use.
- Harden remote deployment with authentication, CORS restrictions, and transport security.

### 11.3 Out of scope for the core release

- Cloud account synchronization and cross-device history sync.
- Built-in hosted model inference infrastructure.
- Guaranteed compatibility with every third-party model/service.
- Unrestricted operating-system automation or silent background monitoring.
- Enterprise multi-tenant management and centralized user administration.

## 12. Dependencies and assumptions

- Users provide compatible model files, local model servers, provider credentials, and external services when required.
- Some ASR/TTS/LLM configurations require internet access.
- A frontend submodule and Live2D/model assets must be present for the full visual experience.
- Hardware acceleration depends on the user's operating system, drivers, installed frameworks, and selected models.
- Provider API behavior, pricing, and rate limits are external dependencies and can change independently of NOVA.

## 13. Risks and mitigations

| Risk | Product impact | Mitigation |
|---|---|---|
| Model too large for available hardware | Slow or failed inference | Document tested configurations and hardware-aware model choices |
| Remote provider outage / rate limit | Conversation failure | Display actionable errors and allow provider switching |
| Inconsistent provider streaming/tool semantics | Feature differences between backends | Maintain provider capability matrix and integration tests |
| Audio permissions/device mismatch | Voice interaction unavailable | Provide device/permission troubleshooting and keep text fallback |
| Broad network exposure | Unauthorized access or data leakage | Localhost default; add auth/TLS and restrictive origin policy before remote use |
| Shared runtime engine references | Potential cross-client state/resource contention | Define lifecycle/ownership and add concurrency tests |
| Local JSON write interruption | History file corruption | Add atomic file replacement and recovery tests |

## 14. Release acceptance checklist

A release candidate is acceptable when:

- [ ] A clean install can launch in browser mode.
- [ ] A clean install can launch in regular-window and pet modes on the supported desktop platform.
- [ ] Invalid configuration produces a clear startup error.
- [ ] Text conversation works with at least one documented LLM provider.
- [ ] Interruption stops an active response in the supported single-client flow.
- [ ] History can be created, listed, restored, and deleted.
- [ ] A documented ASR + TTS combination completes one end-to-end voice scenario, or voice is clearly marked optional/unavailable in that build.
- [ ] Character/avatar/model information is loaded correctly.
- [ ] Tests pass for configuration, dataset handling, LLM factory, and localization.
- [ ] Remote exposure warnings and provider privacy disclosure are documented.
- [ ] No real API keys, access tokens, or session cookies are committed.

## 15. Open product decisions

These require maintainer confirmation before they become firm release commitments:

1. Which operating systems are officially supported for the floating desktop-pet mode?
2. Which exact LLM/ASR/TTS provider combinations are designated stable versus experimental?
3. Should the default NOVA profile prioritize fully local inference, or retain the current configurable default provider?
4. What retention period, export format, and deletion guarantees should be offered for local history?
5. Is LAN access a supported use case, and if so, what authentication model will be required?
6. Which MCP tools are approved for inclusion in a default profile?

---
*End of Product Requirements Document.*
