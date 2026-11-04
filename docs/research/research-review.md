# Research review: measurement-driven development

Reading date: 3 November 2026. Related proposal: [measurement-driven-development.md](../measurement-driven-development.md).

Companion documents: [related books and reading order](books.md) and [the conceptual evaluation pattern](../../evaluation-pattern.yaml).

This review covers the six research entries discussed in chat, the two older foundations, and the additional CEGIS reference. It distinguishes reported findings from proposed applications to Zou. The reading used accessible full-text bodies, methodological details, results, limitations, and relevant appendices. Experiments and implementations were not independently reproduced. PDF figure rendering was unavailable; figure-related interpretations rely on captions and surrounding text. For Palladio, the full text read was its official 28-page introduction chapter, rather than the separately mentioned 2009 journal article. SACM is a specification, not an empirical research paper. The recent arXiv papers are assessed as the particular preprint versions linked below.

## 1. Palladio: predicting performance from architecture

**Read:** Koziolek, Happe, Becker, and Reussner, [Evaluating Performance of Software Architecture Models with the Palladio Component Model](https://www.palladio-simulator.com/assets/files/Introduction-Chapter-PCM.pdf), particularly Sections 3–7.

Palladio separates component behavior, assembly, deployment resources, and expected usage. Resource demands depend on input characteristics and external calls; execution time additionally depends on deployment and contention. Different transformations support analytical prediction, simulation, and generated implementation skeletons.

Its MediaStore example calibrates component models using measurements, predicts a response-time distribution, and compares it with an implemented system. This is evidence from a specific case, not a universal prediction-accuracy result. The chapter's resource model and architecture assumptions are explicitly limited.

Section 7 already proposes combining modelling with measurement, retaining performance knowledge, and improving feedback to designers. Those elements of the proposal have direct prior art.

**Implication for Zou:** represent operation demands separately from the workload and deployment that determine observed performance. Evaluate any claimed contribution beyond this existing modelling-and-measurement approach.

## 2. Online performance model extraction

**Read:** Spinner, Walter, and Kounev, [A Reference Architecture for Online Performance Model Extraction in Virtualized Environments](https://research.spec.org/icpe_proceedings/2016/companion/p57.pdf), ICPE Companion 2016, all six pages.

The architecture separates agents that extract partial system models, obtain monitoring data, and estimate model parameters. A shared repository combines their contributions. Parameters distinguish explicit descriptions from values inferred empirically. Sensors identify metrics, units, and aggregation methods.

Ownership rules prevent conflicting updates. The implementation includes VMware and WildFly integrations and LibReDE for resource-demand estimation. Some information, including usage profiles and database descriptions, still comes from manually prepared models.

This is an architecture and implementation paper; it does not establish a general accuracy bound or demonstrate autonomous application development.

**Implication for Zou:** a useful empirical knowledge base needs typed observations, source ownership, versioned models, and explicit gaps. The paper's agents are software components, not modern LLM agents.

## 3. Clover: checking agreement among code and specifications

**Read:** Sun et al., [Clover: Closed-Loop Verifiable Code Generation](https://arxiv.org/html/2310.17807v4), version 4, including the evaluation and appendix discussion of assumptions and limitations.

Clover checks six directed relationships among code, formal annotations, and natural-language descriptions. It combines deductive verification with reconstruction: generate one representation from another, then compare them.

Its 60 textbook programs have four adversarial variants each. With repeated attempts, the checker accepts 52/60 correct examples and rejects all 240 constructed incorrect variants. That observed rejection rate is not a general false-acceptance guarantee. Code equivalence uses five test inputs; natural-language equivalence uses an LLM. The theoretical argument assumes favorable reconstruction behavior and idealized equivalence checking.

The appendix acknowledges that a shared omission across all three representations can escape detection. Performance is outside this study's scope.

**Implication for Zou:** cross-representation checks can expose weak contracts, but internal agreement cannot establish that the original requirements were right or complete.

## 4. MAGS: frozen semantics and verifier-guided repair

**Read:** Wu et al., [MAGS: Multi-agent Auto-formalization Guarantees Safety for Agentic Outputs](https://arxiv.org/html/2609.19391v1), September 2026 preprint, especially Sections 3–4.

MAGS constructs reusable domain semantics, audits and freezes them, then translates, repairs, and verifies programs using Dafny. It blocks proof-bypassing constructs and evaluates final executables with separate safety and functional checks. The guarantee depends on the model and its mapping to actual APIs.

All 220 examples obtain formal certificates. Independent safety checks pass for 100/100 CUDA kernels, 82/100 terminal programs, and 20/20 robot policies. Missing terminal semantics explain the disagreement. Initially, robot functional preservation is 0/20 despite successful safety checks; additional task-success constraints improve it to 11/20. Per-program verification averages roughly 36–68 minutes, excluding initial domain construction.

**Implication for Zou:** protect acceptance semantics, assess functionality separately from safety, and test the semantic model against independent evidence. Formal certification alone is insufficient for accepting a useful application change.

## 5. SpecBench: finding defects in requirements

**Read:** Hamblin et al., [SpecBench: Evaluating Specification-Level Reasoning for Software Engineering LLM Agents](https://arxiv.org/html/2605.30314v1), May 2026 preprint, including benchmark construction, scoring, and the worked RFC example.

Agents inspect initial RFCs, contemporaneous code, and earlier project discussions to identify specification deficiencies. Reference deficiencies come from later historical reviews across Kubernetes, React, Rust, TVM, and vLLM.

The current task evaluates issue discovery, not successful specification repair. LLMs determine importance tiers and match predictions to reference items. Unmatched predictions remain unjudged; a bounded prediction budget limits indiscriminate suggestions.

The reported best score is 44.4%. It is a weighted recovery score under this protocol, not a measured probability that arbitrary requirements are correct or complete. Human validation of the judging pipeline is future work.

**Implication for Zou:** use project history and classify omissions, ambiguities, inconsistencies, and errors. Assess both missed defects and the burden of reviewing proposed concerns.

## 6. Testing the specifications themselves with Alloy

**Read:** Cunha and Macedo, [Validating Formal Specifications with LLM-generated Test Cases](https://arxiv.org/html/2510.23350v2), February 2026 revision, including the study design and threats to validity.

The method generates positive and negative model instances from natural-language requirements. Positive cases challenge overly restrictive specifications; negative cases challenge overly permissive ones.

The study uses four educational domain models with 43 structural requirements. In one few-shot run, 247/258 generated tests are valid. With five positive and five negative cases per requirement, the mean missed-wrong-specification proportion is 6.43% among requirements receiving complete valid suites. This is a per-requirement mean with a restricted denominator, not an unconditional application failure rate. Only five requirements achieve complete detection of their known wrong specifications.

Validation uses reference oracles. Temporal behavior and production-scale generalization remain unestablished.

**Implication for Zou:** validate contracts with both required and forbidden scenarios, independently of the generated implementation. Generated validation cases also need checking.

## 7. Older foundation: quantitative verification at runtime

**Read:** Calinescu, Ghezzi, Kwiatkowska, and Mirandola, [Self-adaptive Software Needs Quantitative Verification at Runtime](https://www.prismmodelchecker.org/papers/cacm-runtime.pdf), 2012 author manuscript.

The framework distinguishes desired real-world requirements, software specifications, and environmental assumptions. Satisfaction requires the specification and assumptions jointly to support the requirements.

Runtime observations update probabilistic model parameters. Verification detects or predicts violations and helps select corrective configurations. Bayesian estimation, symbolic precomputation, and incremental verification connect measurement with affordable repeated analysis. Examples include service selection, resource allocation, and power management.

The treatment chiefly concerns changing environments and modelled adaptation choices. It does not demonstrate unrestricted generation of new software. Guarantees depend on the abstraction and assumptions, while scalability motivates specialized techniques.

**Implication for Zou:** route discrepancies according to their cause: implementation defect, inaccurate model, changed environment, or changed requirements. Repeatedly editing code is not always the correct response.

## 8. Older foundation: assurance cases and SACM

**Read:** OMG, [Structured Assurance Case Metamodel, version 2.1](https://www.omg.org/spec/SACM/2.1/PDF), April 2020, including the common, argumentation, and artifact metamodels and example descriptions.

SACM represents claims, reasoning, evidence, contextual assumptions, counterevidence, and evidence provenance. It distinguishes unsupported and assumed assertions from assertions defeated by counterevidence. Claims can also concern confidence in other assertions.

Its artifact model describes versions, lifecycle events, participants, techniques, and evidence-producing activities. Modular packages support reuse and exchange.

Crucially, SACM specifies representation and interchange. It explicitly does not establish that a represented argument is valid or complete, or decide whether another party should accept it. A well-formed evidence graph can still contain unsound reasoning.

**Implication for Zou:** supplement individual constraint records with explicit relationships explaining which evidence supports which claims under which assumptions. Implement evidence evaluation separately from graph storage. Do not treat SACM conformance as correctness certification.

## 9. Additional foundation: CEGIS

**Read:** Solar-Lezama, [Introduction to functional synthesis, Lecture 10](https://people.csail.mit.edu/asolar/SynthesisCourse/old_htms/Lecture10.htm), 2018 course notes explaining the earlier CEGIS work.

Counterexample-guided synthesis alternates candidate generation and verification. Each discovered counterexample constrains later candidates, eliminating more than the single rejected program. It is an established basis for a repair loop.

The notes also explain limitations: finite examples can remain consistent with candidates even when no solution satisfies the full requirement. Termination and assurance depend on the candidate space and checking method. An empirical search that finds no failure has not automatically established a universal property.

**Implication for Zou:** retain reproducible counterexamples across revisions and distinguish exhaustive verification, bounded checks, sampled testing, and exhausted search budgets.

## Product overlap

These sources describe product capabilities, not independently reproduced research results.

| Project and source | Documented overlap | Boundary relevant to Zou |
| --- | --- | --- |
| [Antithesis: how it works](https://antithesis.com/docs/introduction/how_antithesis_works/) | Fault injection, guided exploration, property checks, deterministic reproduction, and a coding-agent skill for an initial property catalog. | Exploration can find violations of properties; this documentation does not establish discovery of every required property. |
| [Kiro: correctness](https://kiro.dev/docs/specs/correctness/) | Requirements become linked properties and generated tests, with shrinking and correction workflows. | The documentation acknowledges weak-property risks and distinguishes testing evidence from formal proof. |
| [Tessl: framework launch](https://tessl.io/blog/tessl-launches-spec-driven-framework-and-registry) | Persistent specifications connect capabilities, public APIs, linked tests, and generated code. | This is a September 2025 launch description, not verification of the complete current product or of autonomous acceptance reliability. |

## Assessment of the proposal

The source-specific implications above are research interpretations. The following is a proposed direction for Zou, not a result established by these publications.

The reviewed work gives substantial prior art for architecture-based prediction, empirical model updates, specification-guided generation, verification feedback, and structured evidence. Novelty should not be claimed merely for combining these labels. Whether a particular integration is novel requires a broader comparison and evaluation.

A focused question remains useful: **Can an operation-level acceptance system reduce incorrect acceptance of AI-generated changes while keeping verification cost and human intervention practical?**

For a first `POST /orders` study, represent separate obligations for intended behavior, authorization, concurrency and failure recovery, and resource consumption under specified conditions. Associate each obligation with its source, assumptions, verifier, evidence, and unresolved questions.

Preserve the original constraint tuple as a compact record if useful. Add relationships for dependencies, context, supporting evidence, and counterevidence. An observation should identify the code and contract versions, deployment, workload, tool configuration, measurement period, and statistical limitations needed to interpret it.

Keep specification modification distinct from implementation repair. A failed run should permit investigation of the checker, predictive model, environment, and requirements as well as code. A timed-out or inapplicable verifier should leave an explicit evidence gap.

## A defensible first experiment

Compare three workflows under matched budgets and independent evaluation:

1. Code generation with conventional generated tests.
2. Contract-guided generation and verification.
3. The same contracts plus resource predictions, empirical validation, and explicit handling of insufficient evidence.

Use a narrow backend stack and known reference requirements. Include incorrect implementations, deliberately incomplete or restrictive specifications, changed workloads, and faulty predictive assumptions. Keep evaluation cases outside the repair loop. Include correct candidates to measure unnecessary rejection as well as missed defects.

The primary measure should be the fraction of accepted candidates that fail independent acceptance criteria. Also report the fraction of incorrect candidates accepted, correct candidates rejected, unresolved decisions, intervention count, time, and verification cost. Define denominators explicitly. Repeat stochastic runs and report uncertainty.

An ablation should identify whether predictions and evidence-gap handling improve decisions beyond contracts alone. A useful outcome is a measurable reduction in incorrect acceptance at an acceptable cost. Passing every available check does not, by itself, demonstrate that outcome.
