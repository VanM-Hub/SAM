# Models



Version: 1.0



Status: Draft



Knowledge Type: Concept



Evidence Level: Verified



Confidence: High



Owner: OpenClaw Module



Related Documents



Module



\- providers.md

\- runtime.md

\- configuration.md



Architecture



\- ../architecture/provider-model.md

\- ../architecture/runtime-flow.md

\- ../architecture/data-flow.md



Framework



\- docs/documentation/KNOWLEDGE\_STANDARD.md

\- docs/models/TRUST\_MODEL.md

\- docs/models/DECISION\_MODEL.md



---



# Purpose



This document defines the Model concept within the OpenClaw Module.



Models perform inference.



Providers expose Models.



The distinction between these concepts is fundamental to the architecture of the OpenClaw Module.



---



# Definition



A Model is an AI system capable of performing inference.



Models may differ in:



\- capability,

\- reasoning,

\- modality,

\- latency,

\- resource requirements,

\- operational cost.



The Model performs reasoning.



The Provider delivers access to the Model.



---



# Scope



Model knowledge includes:



\- capabilities

\- limitations

\- supported modalities

\- operational characteristics

\- compatibility considerations



Benchmark results and provider-specific implementation details belong in specialized documents.



---



# Relationship with Providers



Models are accessed through Providers.



Multiple Providers may expose the same Model family.



Likewise, one Provider may expose multiple Models.



This many-to-many relationship is an important architectural principle.



---



# Relationship with Runtime



The Runtime invokes Models through the selected Provider.



Runtime should remain independent from the internal implementation of individual Models.



---



# Relationship with Configuration



Configuration determines which Model should be requested.



Changing Models should not require changes to Runtime architecture.



---



# Operational Considerations



When selecting a Model, operators should evaluate:



\- reasoning capability

\- response quality

\- execution speed

\- context limitations

\- operational cost

\- compatibility with the intended task



Model selection should follow the Framework Decision Model and be supported by evidence whenever practical.



---



# Future Evolution



As the number of supported Models increases, this document may evolve into:



knowledge/models/



README.md



gpt.md



claude.md



gemini.md



llama.md



nemotron.md



deepseek.md



qwen.md



mistral.md



The current document will remain the conceptual entry point for the model domain.



---



# Summary



Models provide the reasoning capabilities used by OpenClaw.



By separating the concepts of Provider and Model, the OpenClaw Module preserves architectural flexibility while supporting a growing ecosystem of AI technologies.

