\# SAM Architectural Planning Standard



Version: 2.0.0



Status: Engineering Standard



Authority: Chief Architect



Applies To:



\- Chief Architect

\- Software Architect

\- Lead Engineer



Depends On:



\- SAM 2.0 Development Strategy

\- SAM 2.x Roadmap

\- SAM Platform Readiness Model



\---



\# Purpose



This document defines how architectural priorities are determined during SAM 2.x.



It prevents engineering effort from drifting toward implementation convenience.



Architecture shall always advance Platform Readiness.



\---



\# Architectural Objective



Every architectural decision shall answer one question.



Does this move SAM closer to becoming a production-ready governance platform?



If the answer is no,



the work should be reconsidered.



\---



\# Planning Hierarchy



Planning shall follow this hierarchy.



Mission



↓



Development Strategy



↓



Roadmap



↓



Platform Readiness



↓



Capability Readiness



↓



Engineering



↓



Release



↓



Sprint



Lower levels shall never redefine higher levels.



\---



\# Planning Units



Planning is performed using Capabilities.



Never using folders.



Never using modules.



Never using packages.



Implementation changes.



Capabilities remain.



\---



\# Priority Rules



Architectural priorities shall follow this order.



\---



Priority 1



Increase Governance Readiness.



\---



Priority 2



Increase Operational Readiness.



\---



Priority 3



Increase Production Readiness.



\---



Priority 4



Increase Developer Readiness.



\---



Priority 5



Reduce Technical Debt.



\---



Priority 6



Optimize implementation.



Optimization shall never delay readiness.



\---



\# Runtime Rule



Architectural planning shall never ask:



"What Runtime should we build?"



Instead it shall ask:



"What existing Runtime should become operational?"



\---



\# Capability Rule



Every capability shall have:



Current Readiness



Target Readiness



Blocking Issues



Required Evidence



Owning Program



Owning Runtime



\---



\# Work Selection



Software Architects shall select work according to:



Highest architectural impact



Highest readiness improvement



Lowest constitutional risk



Greatest reduction of technical uncertainty



Greatest benefit for future engineering



\---



\# Architectural Debt



Architectural debt is defined as:



Any implementation that prevents Platform Readiness.



Architectural debt has priority over implementation optimization.



\---



\# Technical Debt



Technical debt includes:



repository organization



legacy modules



duplicate implementation



obsolete tests



dead code



unused dependencies



Technical debt shall be removed when it improves readiness.



\---



\# Work Classification



Every proposed work item shall belong to exactly one category.



Foundation Convergence



Runtime Realization



Operational Intelligence



Production Readiness



Developer Experience



If a task belongs to none,



it should probably not exist.



\---



\# Readiness Review



Every architectural review shall answer:



What readiness increased?



What readiness remains blocked?



What evidence supports promotion?



What constitutional risks remain?



\---



\# Success



Architectural planning succeeds when:



Engineering effort consistently increases Platform Readiness,



while preserving the Foundation.



\---



\# Final Statement



Architecture is no longer discovering SAM.



Architecture is realizing SAM.



Every planning decision should shorten the distance between constitutional design and operational reality.

