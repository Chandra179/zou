# Ideas

> **Current scope:** the implementation in this repository (the [`business-rules` skill](../.claude/skills/business-rules/SKILL.md) and [how-to](business-rules-howto.md)) covers behavioral business rules only. The constraint tuple `C = (P, M, W, T, E, U)` and the resource-prediction ideas below (storage, memory, latency, capacity) are deferred, not dropped.

## Measurement-driven development

I think the idea should be designed as a closed-loop, measurement-driven development system.

It combines two complementary capabilities:

* **Predictive verification (before implementation):** Calculate what the application should consume, how it should behave, and which constraints its design must satisfy.
* **Empirical verification (during and after implementation):** Measure what the application actually does, compare the results against predictions, and use discrepancies to guide AI-generated changes.

The interesting part is the feedback loop between them.

### 1. Proposed architecture

1. Application specification: requirements, operations, data models, infrastructure
2. Predictive engine: storage formulas, memory estimates, capacity models, expected behavior
3. Constraint registry: thresholds, invariants, risk levels, assumptions
4. AI implementation agent: designs, generates, and modifies code
5. Measurement and verification engine: benchmarking, profiling, assertions, property tests, security checks
6. Evidence evaluator: compare expected vs. actual; assess confidence and coverage
7. Pass: release if policy permits
8. Fail / Unknown: repair, remeasure, or escalate

Failures feed back into AI implementation; observations can also refine predictive models after validation.

### 2. A single measurement model

Start by making every constraint follow a common structure:

`C = (P, M, W, T, E, U)`

| Symbol | Meaning                            |
| ------ | ---------------------------------- |
| P      | Property being evaluated           |
| M      | Measurement or verification method |
| W      | Workload or conditions             |
| T      | Threshold or expected invariant    |
| E      | Evidence obtained                  |
| U      | Uncertainty and limitations        |

This is useful because the same model can represent both static and dynamic properties.

For example, suppose you're designing an application that stores user events. Each serialized event is approximately 500 bytes, and you expect 1 million events daily.

The initial estimate is:

```
500 bytes × 1,000,000 = 500 MB/day
```

That is the estimated daily application payload volume, not necessarily the actual disk consumption.

When AI implements the application, the verification engine can measure the real storage growth, including indexes and database overhead.

Illustrative prediction versus observation: a 180 MB difference can trigger an investigation into indexing, metadata, serialization, or replication assumptions.

Over time, you build a repository of validated measurements and their conditions. Those observations can improve estimates for subsequent applications.

That could become one of the more valuable parts of the system: an empirical knowledge base of how software designs translate into resource consumption and behavior.

### 3. Don't make everything a threshold

Separate three types of constraints.

**Exact constraints**
Deterministic properties such as a serialized field length, numerical formula, or schema requirement. Verified by calculation, executable assertions, or formal proof under specified assumptions.

**Statistical constraints**
Latency, throughput, error rates, and utilization. These require representative workloads, measurements, and sufficient statistical confidence.

**Behavioral constraints**
Authorization, transactional consistency, idempotency, and business rules. These require explicit specifications and verification approaches; a numerical score alone is generally insufficient.

All three can fit into the same constraint registry, but their verification engines should differ.

### 4. Scoping the first prototype

Initial scope: infrastructure constraints and operation constraints.

Start with a single backend operation, such as `POST /orders`, and trace its dependencies:

HTTP request → validation and business logic → database operations → response

For each operation, define its resource demands, behavioral invariants, environmental assumptions, and evidence requirements.

Then let an AI agent implement it and run the verifiers.

The first prototype doesn't need to understand an entire application. It only needs to demonstrate that a measurable specification can guide implementation, detect violations, and support automated correction.

### 5. The most important design principle

Make measurement coverage a first-class concept.

For example, an operation might have:

* 8 properties verified successfully.
* 2 properties failing.
* 3 properties without sufficient evidence.
* 1 security requirement that has not been specified.

It should not be reported as simply "80% correct."

A verifier that reports uncertainty explicitly is much more useful than one that generates a misleading correctness percentage.

This also defines where humans remain necessary: not necessarily reviewing thousands of generated lines, but deciding which properties matter, examining uncovered risks, and approving high-impact changes.

### 6. Where this leads

Three modes:

| Mode             | Responsibility                                                                                            |
| ---------------- | --------------------------------------------------------------------------------------------------------- |
| Design-time      | Predict resource requirements and evaluate design feasibility                                             |
| Development-time | Verify and repair AI-generated implementations                                                            |
| Runtime          | Detect deviations from defined operational constraints and feed validated observations into future models |

The long-term goal is a system where application specifications become executable verification contracts, not merely documentation written for developers.

One further issue worth investigating is how constraints are discovered. Explicit constraints are relatively straightforward to verify. Missing constraints are harder, and they're precisely where AI-generated applications can pass every test while still behaving incorrectly.

Organize the research around two connected problems:

* **Problem A:** How can we systematically identify and quantify the measurable properties of an application?
* **Problem B:** How can we establish sufficient verification coverage to allow AI-generated changes to be accepted with minimal human intervention?

Problem A gives the measurement framework. Problem B gives the autonomous development system.

Together, they form a coherent technical direction. Each piece has prior art (see the [research review](research-review.md)), so novelty rests on whether the integration reduces incorrect acceptance at practical cost, which is still to be shown.

---

## The Oracle Problem, Intent Formalization, and Google's Contract-Based Testing Research

These three research areas directly address the central question behind the measurement-driven development idea:

How can we trust AI-generated software without humans having to understand and review every line of its implementation?

The research points toward a common architectural approach: instead of relying solely on AI's ability to produce correct code, develop independent ways to establish what correct behavior means and verify that the implementation satisfies it.

There is, however, a deeper problem: who verifies that the definition of correctness is itself correct?

That's the question that matters most for this project.

### 1. The Oracle Problem: How do we know the output is correct?

The test oracle problem is a longstanding problem in software engineering, well before generative AI.

A test oracle is a mechanism for deciding whether the observed behavior of a program is correct.

An influential research survey, [The Oracle Problem in Software Testing: A Survey](https://ieeexplore.ieee.org/document/6963470) (IEEE Transactions on Software Engineering, 2015), describes the difficulty of determining expected behavior and automating that judgment.

#### A simple example

Suppose AI builds a function to calculate a discount:

```python
def discounted_price(price, discount):
    return price - (price * discount / 100)
```

You test:

```text
Input:
price = 100
discount = 20

Actual output:
80
```

Is the result correct? Mathematically, yes, assuming the discount represents a percentage.

But suppose the actual business rule was:

* Discounts cannot exceed 15%.
* Negative discounts are invalid.
* Discounts must be applied before tax.
* Some products are excluded.
* Rounding must follow a defined currency policy.

The implementation could be mathematically sound while violating the application's requirements.

This reveals two different forms of correctness:

**Implementation correctness**
Does the code satisfy a given specification? Can often be checked by tests, assertions, or formal verification.

**Specification correctness**
Does the specification accurately represent what was intended? Requires evidence about requirements, domain rules, and stakeholder expectations.

The original approach—calculating storage, memory, network load, latency, and other constraints—is especially strong for the first problem.

The second problem is more difficult because no amount of runtime measurement can discover a business rule that was never defined or inferred from valid evidence.

#### Four approaches to the oracle problem

The IEEE survey organizes the research around specified, derived, implicit, and human-assisted oracles.

| Approach              | How correctness is determined                    | Main limitation                      |
| --------------------- | ------------------------------------------------ | ------------------------------------ |
| Specified oracle      | Explicit expected outputs, assertions, contracts | Specification might be wrong         |
| Derived oracle        | Relationships, models, alternate implementations | Only covers certain properties       |
| Implicit oracle       | General failure indicators, such as crashes      | Many logical errors remain invisible |
| Human-assisted oracle | Domain expert evaluates uncertain behavior       | Expensive and hard to scale          |

One particularly useful technique is **metamorphic testing**.

Suppose we cannot easily calculate the correct result for every complicated operation. Instead, we define a relationship that must remain true.

For example, a search function might be expected to return the same result set regardless of the order of independent filters. Or encoding and decoding a value should recover the original value for supported inputs.

Formally, instead of knowing the answer `f(x)`, we verify:

```
R(f(x), f(T(x))) = true
```

Where `T` transforms an input and `R` is a relationship between the results.

This can be automated across thousands of AI-generated test cases without manually specifying every expected output.

Important limitation: metamorphic testing does not prove the application correct. A buggy implementation may still satisfy the relationships being tested.

### 2. Microsoft Research: Intent Formalization

Research paper, March 2026: [Intent Formalization: A Grand Challenge for Reliable Coding in the Age of AI Agents](https://www.microsoft.com/en-us/research/publication/intent-formalization-a-grand-challenge-for-reliable-coding-in-the-age-of-ai-agents/) (Shuvendu Lahiri, Microsoft Research; also [arXiv 2603.17150](https://arxiv.org/abs/2603.17150)).

This research moves the problem one level above code verification.

Microsoft calls the discrepancy between informal human requirements and precise program behavior the **intent gap**.

1. Human intent: "Users should only see their own orders"
2. Intent formalization: translate natural language into explicit, checkable behavior
3. Executable specification: for every authenticated user and order, access requires ownership or a separately authorized role
4. Verification: test or prove the implementation satisfies the formalized rule

#### The key research claim

The paper argues that translating intent into checkable specifications is a foundational challenge for reliable agentic coding.

It describes a spectrum:

* Lightweight tests that clarify likely misunderstandings.
* Detailed functional specifications suitable for formal verification.
* Domain-specific languages that can support automatic synthesis of correct code.

It also identifies the central bottleneck: validating the specifications themselves. Microsoft notes that there is no independent definitive oracle for whether a specification matches the user's true intent.

This aligns closely with the direction here. We don't necessarily need to make AI better at reviewing its own code. We need to make the application's requirements sufficiently precise and independently checkable that implementation mistakes become observable.

But requirements cannot simply be assumed correct because an LLM generated them.

#### Microsoft's supporting experiments

The 2026 paper is primarily a research agenda rather than an experiment demonstrating that the oracle problem has been solved. However, it builds on several experimental studies.

**TiCoder — interactive intent clarification** (Microsoft Research, 2022, with subsequent evaluation)
Asks users targeted questions through test cases to clarify what the code should do. In the original MBPP benchmark evaluation, one configuration improved pass@1 accuracy from 48.39% to 70.49% with one user query, and to 85.48% with up to five queries. Those results were obtained in a benchmark setting with simulated user feedback, not autonomous validation of arbitrary production systems.

**nl2postcond — translating documentation into postconditions** (Microsoft Research, FSE 2024)
Instead of generating implementation code, the model generates checkable assertions about what must be true after a function executes. The researchers reported that generated postconditions detected 64 historical real-world bugs in Defects4J. This supports the feasibility of automatically producing useful partial oracles, though it does not imply every generated postcondition is correct.

#### What to take from Microsoft

An AI system should not go directly from vague requirements to implementation.

It should first create a structured specification, expose uncertainties, and resolve important ambiguities before using that specification to guide code generation.

That suggests a separate **Intent Formalization Engine**, distinct from both the coding agent and the measurement engine.

### 3. Google Research: Grounding AI Agents in Contracts

Research paper, SpecOps 2026: [Grounding AI Agents in Contracts: An Empirical Evaluation of Spec-Driven Test Generation](https://research.google/pubs/grounding-ai-agents-in-contracts-an-empirical-evaluation-of-spec-driven-test-generation/) (Michele Tufano and collaborators, Google Research).

Google investigated a related but more narrowly scoped question: can AI generate better tests when it first reasons explicitly about a program's behavioral contract?

The researchers compared conventional agent-based test generation with a specification-driven approach.

#### How Google's method works

Instead of directly asking the agent to generate tests, the process inserts an intermediate specification step.

* Conventional approach: code context → AI generates tests
* Spec-driven approach: code context → explicit contracts → AI generates tests

The intermediate contracts cover three categories:

* **Preconditions** specify what must be true before an operation. For example, an order quantity must be positive.
* **Postconditions** specify what must be true afterward. For example, successfully creating an order must return an identifier corresponding to a persisted record.
* **Undefined behaviors** identify cases whose outcomes are not guaranteed by the contract. For example, a function may not define what happens when passed malformed data outside its accepted domain.

This distinction matters because testing an invalid input does not automatically mean the software is broken. You need to know whether the input should be rejected, handled gracefully, or is explicitly outside the operation's supported domain.

#### Google's reported results

* **+9.8 pp** bug detection rate over baseline (p = 0.0352)
* **+2.5 pp** branch coverage over baseline (p = 0.0034)

An LLM-as-a-Judge also preferred the spec-driven test suites over baseline-generated suites in 77.8% of evaluated cases and over human-authored suites in 56.7%.

Reported in the publication abstract. The judge preferences are subjective evaluation results, not independently proven correctness rates. These are percentage-point improvements, not relative percentage improvements.

Importantly, Google did not demonstrate that software can be fully validated without humans. The finding is that an explicit contract-generation step improved test generation and detected more bugs in their evaluation.

#### Why this matters here

The initial proposal emphasizes numerical measurements: memory, storage, latency, network traffic, and capacity.

Google's research suggests treating behavioral boundaries as measurable verification targets too.

```yaml
operation: transfer_money

preconditions:
  - amount > 0
  - account_is_authorized: true
  - sufficient_balance: true

postconditions:
  - source_balance_decreases_by: amount
  - target_balance_increases_by: amount
  - transaction_is_atomic: true

invariants:
  - total_money_is_conserved: true
  - unauthorized_transfers: forbidden
```

This example is intentionally simplified; a production system needs explicit rules for fees, decimal precision, concurrent operations, failure recovery, and external accounts.

The key is that each declaration becomes an obligation for the verifier—not merely a sentence in documentation.

But one issue remains: if AI invents those declarations incorrectly, Google's method alone does not guarantee that the tests represent the true business requirements.

### 4. How these research directions fit together

| Research                            | Core question                                                                  | Contribution to the system                            |
| ----------------------------------- | ------------------------------------------------------------------------------ | ----------------------------------------------------- |
| Oracle problem                      | How do we determine whether behavior is correct?                               | Independent verification mechanisms                   |
| Microsoft intent formalization      | How do we translate human intent into a correct specification?                 | Specification generation and validation               |
| Google spec-driven testing          | How do we generate tests that explore meaningful behavioral boundaries?        | Contract-guided test generation                       |
| Proposed measurement framework      | How do we predict and continuously evaluate measurable application properties? | Quantitative models, runtime evidence, feedback loops |

The proposal could integrate all four.

There is an additional research problem worth emphasizing: how can we systematically discover what we have failed to specify or measure?

That is different from measuring existing constraints. It means investigating the completeness of the measurement model itself.

### 5. The architecture to investigate

1. **Intent and system context:** requirements, data models, architecture, operational environment
2. **Specification discovery:** generate constraints, preconditions, postconditions, invariants, assumptions
3. **Specification validation:** find contradictions, ambiguities, missing cases, and unsupported assumptions
4. **Predictive measurement:** estimate storage, memory, latency, capacity, resource requirements
5. **AI implementation:** generate code constrained by the specification
6. **Independent verification:** formal checks, generated tests, benchmarks, traces, security analysis
7. **Evidence and uncertainty evaluation:** Verified · Violated · Unknown · Outside scope

Failures return to the implementation or specification stage. Validated observations improve future predictions.

A crucial architectural rule: generated code must not be allowed to silently modify its own acceptance criteria. Specification changes need separate validation and authorization.

Otherwise, an AI agent could make its implementation pass by weakening the tests or thresholds rather than correcting the implementation.

### 6. A research direction: quantifying oracle quality

The system could maintain several independent indicators of how well an application is specified and verified.

| Indicator                    | What it tells you                                                 |
| ---------------------------- | ----------------------------------------------------------------- |
| Requirement traceability     | Which requirements have associated verification obligations?      |
| Mutation detection           | Can the tests detect deliberately introduced faults?              |
| Behavioral boundary coverage | Have important valid, invalid, and edge cases been explored?      |
| Invariant coverage           | Which safety and consistency properties are verified?             |
| Environment coverage         | Under which workloads and operating conditions is evidence valid? |
| Specification confidence     | How well supported is each requirement by authoritative evidence? |

None of these alone constitutes a complete measure of correctness. A high mutation score, for instance, indicates that tests detect many introduced mutations; it does not establish that the application meets every intended requirement.

Instead of combining everything into an arbitrary 0–100 correctness score, preserve these indicators as separate evidence dimensions.

#### A hypothetical research experiment

Take 50 small applications with known reference requirements and seeded defects, then compare three development methods:

* **Baseline:** AI writes code and generates conventional tests.
* **Contract-driven:** AI formalizes requirements before generating tests.
* **Measurement-driven:** AI uses contracts, predicted resource models, runtime measurements, and verification coverage checks.

Measure the number of genuine defects detected, incorrect specifications accepted, unnecessary human interventions, and verification cost.

The most important outcome is not just how many tests pass. It is how many incorrect implementations are mistakenly accepted. That measures the reliability of the approval process itself.

### 7. Three questions that remain genuinely difficult

**Can AI identify missing requirements?**
Sometimes. It can infer likely requirements from architecture, documentation, domain conventions, and known failure modes. But it cannot guarantee discovery of every unstated intention. Any inferred requirement needs a source, confidence assessment, and a way to resolve uncertainty.

**Can probabilistic verification replace formal verification?**
Not in general. Statistical tests can establish evidence about observed behavior under sampled conditions. Formal verification can establish particular properties for all behaviors within a mathematical model and its assumptions. These approaches are complementary, not interchangeable.

**Can human code review eventually disappear?**
For carefully constrained systems and changes, automated verification may justify eliminating routine human review of individual changes. For unrestricted software, the difficult part remains proving that the specifications, assumptions, verification tools, and deployment context are sufficiently complete and trustworthy. The system can make that uncertainty explicit and route only particular risks to humans, which is a more defensible objective.

### 8. Papers to read, in order

1. [The Oracle Problem in Software Testing: A Survey](https://ieeexplore.ieee.org/document/6963470) — Barr, Harman, McMinn, Shahbaz, Yoo · 2015. The fundamental taxonomy of test oracles and why automated test generation cannot by itself solve the correctness problem.
2. [Intent Formalization: A Grand Challenge for Reliable Coding in the Age of AI Agents](https://arxiv.org/abs/2603.17150) — Lahiri · 2026. The specification-correctness problem, evaluation methods, and broader research agenda.
3. [Interactive Code Generation via Test-Driven User-Intent Formalization](https://www.microsoft.com/en-us/research/publication/interactive-code-generation-via-test-driven-user-intent-formalization/) — Lahiri et al. · 2022; related follow-up in 2024. An empirical approach to progressively clarifying intent through generated tests.
4. [Grounding AI Agents in Contracts](https://research.google/pubs/grounding-ai-agents-in-contracts-an-empirical-evaluation-of-spec-driven-test-generation/) — Tufano et al. · SpecOps 2026. An experimentally evaluated workflow that uses explicit contracts to improve AI-generated testing.

### Next research problem

The area with the greatest relevance is the intersection of specification completeness, test-oracle quality, and measurable evidence.

Consider an AI-built API that passes every existing test. The system should not merely confirm that all tests passed. It should ask:

* Which classes of behavior have never been specified?
* Which constraints are derived from authoritative requirements and which were inferred by AI?
* Which operations have no reliable oracle?
* Which failures could occur outside the measured workload?
* Which new measurements would reduce the most uncertainty?

This changes the goal from automatically proving that code passes the available checks to systematically discovering what evidence is still missing before trusting the code.

This is a stronger foundation for the proposed autonomous development system than a one-size-fits-all approach, because every application is different.
