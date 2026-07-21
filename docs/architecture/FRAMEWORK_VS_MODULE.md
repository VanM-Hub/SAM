# FRAMEWORK\_VS\_MODULE



Version: 0.1.0

Status: Draft

Owner: SAM Framework

Last Updated: 2026-07-20



---



# Purpose



One of the most common architectural mistakes in long-lived software projects is

placing functionality in the wrong location.



When architectural boundaries become unclear, frameworks slowly evolve into

monoliths.



This document defines the permanent boundary between the SAM Framework and every

SAM Module.



Whenever contributors ask:



"Where should this feature belong?"



this document provides the answer.



---



# Philosophy



The Framework answers:



**How should intelligent operations be performed?**



Modules answer:



**How does this specific platform behave?**



This distinction should remain valid regardless of future technologies.



---



# The Framework Is Universal



The Framework contains concepts that remain true regardless of platform.



Examples:



Decision making



Risk evaluation



Evidence evaluation



Trust model



Execution model



Thinking protocol



Reasoning workflow



Governance



Architecture



Vocabulary



Documentation standards



These concepts should be reusable for every module.



If removing OpenClaw would break a Framework component,

that component probably belongs inside a Module instead.



---



# Modules Are Specialized



Modules represent operational domains.



Examples



OpenClaw



Docker



Windows



Linux



GitHub



Kubernetes



Future AI Providers



Each module owns knowledge that is meaningful only inside that domain.



Removing a module should never reduce the Framework's ability to reason.



It only reduces its knowledge of that platform.



---



# Decision Rule



Before creating a new component, ask:



Can this concept exist without OpenClaw?



YES



↓



Framework Candidate



NO



↓



Module Candidate



This simple rule resolves most architectural uncertainty.



---



# What Belongs in the Framework



The Framework owns concepts that are:



Platform-independent



Reusable



Stable



Conceptual



Examples



Decision Engine



Thinking Protocol



Trust Engine



Risk Engine



Execution Strategy



Memory Model



Evidence Model



Vocabulary



Governance



Architecture



Documentation Standards



Dependency Rules



Module Interface



These concepts define *how* intelligent operations occur.



---



# What Belongs in Modules



Modules own knowledge that depends upon a platform.



Examples



Configuration Files



Provider APIs



Model Lists



CLI Commands



Log Formats



Error Codes



Authentication



Installation



Diagnostics



Known Bugs



Provider Limitations



Operational Playbooks



These define *what* is known about one platform.



---



# What Must Never Enter the Framework



The Framework must never contain:



Platform names



Configuration formats



Provider endpoints



Authentication methods



Runtime logs



Version-specific behavior



CLI syntax



Product documentation



Vendor recommendations



Implementation workarounds



These items have short lifecycles.



The Framework is designed to have a long lifecycle.



---



# What Must Never Enter Modules



Modules must never redefine:



Governance



Architecture



Decision Model



Thinking Protocol



Repository Standards



Documentation Rules



Risk Philosophy



Trust Philosophy



If every module invents its own rules,

the framework ceases to exist.



---



# Shared Functionality



Sometimes multiple modules require similar behavior.



Decision process



Is it conceptual?



↓



Framework



Is it platform-specific?



↓



Module



Examples



Evidence evaluation



↓



Framework



Reading OpenClaw configuration



↓



OpenClaw Module



Reading Docker Compose



↓



Docker Module



Reading Kubernetes manifests



↓



Kubernetes Module



Although all involve configuration,

each belongs to its respective module.



---



# Knowledge vs Reasoning



This distinction deserves special attention.



Knowledge answers:



"What is true?"



Reasoning answers:



"What should we conclude?"



Knowledge belongs to modules.



Reasoning belongs to the Framework.



Example



Module



"The provider returned HTTP 401."



Framework



"The authentication process failed."



Module



"The model is deprecated."



Framework



"This configuration introduces operational risk."



The Framework never invents knowledge.



Modules never make final operational decisions.



---



# Replaceability Test



A useful architectural test is:



Imagine deleting the module.



If the Framework still functions,

the architecture is healthy.



Imagine deleting the Framework.



If the module can no longer reason,

that is expected.



Framework



↓



Required



Module



↓



Optional



This dependency direction is intentional.



---



# Future Growth



Suppose ten new platforms are added.



OpenClaw



Docker



Linux



Windows



GitHub



Azure



AWS



Kubernetes



GitLab



Terraform



The Framework should require almost no modification.



Growth occurs by adding Modules,

not expanding the Framework.



This is one of the primary scalability goals of SAM.



---



# Anti-Patterns



The following indicate architectural erosion.



Framework imports OpenClaw code.



Framework understands provider APIs.



Framework contains CLI commands.



Framework parses configuration files.



Modules implement their own reasoning engine.



Modules redefine governance.



Modules communicate directly.



Knowledge is duplicated.



Playbooks contain reasoning logic.



These situations should trigger an architectural review.



---



# Decision Matrix



| Question | Framework | Module |

|-----------|-----------|---------|

| Is it reusable across platforms? | ✔ | |

| Is it platform-specific? | | ✔ |

| Is it reasoning? | ✔ | |

| Is it knowledge? | | ✔ |

| Is it governance? | ✔ | |

| Is it diagnostics? | | ✔ |

| Is it architecture? | ✔ | |

| Is it configuration? | | ✔ |

| Is it provider behavior? | | ✔ |

| Is it operational philosophy? | ✔ | |



When uncertainty exists,

prefer keeping the Framework smaller.



Modules are expected to grow.



The Framework is expected to remain stable.



---



# Summary



The Framework is the mind.



Modules are the experts.



The Framework teaches every module how to think.



Each Module teaches the Framework about one operational domain.



Maintaining this separation is the single most important architectural rule in the SAM Framework.

