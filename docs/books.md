# Related books and reading order

Documented: 3 November 2026.

These books support the concepts in [ideas.md](ideas.md), the [research review](research-review.md), and the [evaluation pattern](../evaluation-pattern.yaml).

**Reading status:** recommendations based on publisher or author descriptions, tables of contents, and selected accessible material. These notes do not claim a full reading of any book. The connections to Zou are our interpretation; they do not establish that a book demonstrates the complete proposed system.

## Books

### 1. Software for Dependable Systems: Sufficient Evidence?

- **Authoring body:** National Research Council.
- **Editors:** Daniel Jackson, Martyn Thomas, and Lynette I. Millett.
- **Publisher:** National Academies Press, 2007.
- **Source and online reading:** [Chapter 2: Proposed Approach](https://www.nationalacademies.org/read/11923/chapter/4).

**Relevance:** the closest match to the parent evaluation loop. It connects explicit claims and environmental assumptions with evidence and structured arguments for dependability. It also emphasizes the expertise needed to construct and assess that evidence.

**Start with:** Chapter 2, especially its treatment of claims, evidence, and expertise.

**Question for Zou:** what evidence makes a scoped acceptance decision defensible, and which judgments still require domain knowledge?

### 2. An Introduction to Self-adaptive Systems: A Contemporary Software Engineering Perspective

- **Author:** Danny Weyns.
- **Publisher:** Wiley; first published online in 2020, copyright 2021.
- **Source:** [Publisher description and contents](https://onlinelibrary.wiley.com/doi/book/10.1002/9781119574910).

**Relevance:** connects feedback control, runtime models, uncertainty, requirements, and adaptation. It provides a foundation for the repeated evaluation and revision parts of our model.

**Start with:** Chapters 1–2 for the conceptual foundation, then Chapters 6–8 for runtime models, requirements-driven adaptation, and guarantees under uncertainty.

**Question for Zou:** when conditions change, how should the system determine whether to update its model, revise its implementation, or seek additional evidence?

### 3. Specification by Example: How Successful Teams Deliver the Right Software

- **Author:** Gojko Adzic.
- **Publisher:** Manning, 2011.
- **Source:** [Publisher description and resources](https://www.manning.com/books/specification-by-example).

**Relevance:** connects collaborative requirements clarification with concrete examples, executable specifications, and living documentation. This supports the specification branch and the transition from intent to checkable behavior.

**Reading focus:** how stakeholders establish expectations, select useful examples, and maintain specifications as software changes.

**Question for Zou:** which examples make an ambiguous requirement precise enough to check, and who validates their intended meaning?

### 4. Software Abstractions: Logic, Language, and Analysis — Revised Edition

- **Author:** Daniel Jackson.
- **Publisher:** MIT Press.
- **Source:** [Publisher description](https://mitpress.mit.edu/9780262528900/software-abstractions/).

**Relevance:** introduces precise software models and automated analysis using Alloy. It supports checking specifications and designs and finding counterexamples before implementation.

**Reading focus:** expressing relationships and constraints, exploring models, and interpreting counterexamples.

**Question for Zou:** which claims can be expressed precisely enough for automated model analysis, and what limits apply to its conclusions?

### 5. Performance Solutions: A Practical Guide to Creating Responsive, Scalable Software

- **Authors:** Connie U. Smith and Lloyd G. Williams.
- **Publisher:** Addison-Wesley Professional, published 2001, copyright 2002.
- **Source:** [Publisher description, contents, and sample material](https://www.informit.com/store/performance-solutions-a-practical-guide-to-creating-9780201722291).

**Relevance:** directly supports the predictive design branch. It describes defining performance objectives, building quantitative models, estimating resource demands, and validating models throughout development.

**Start with:** Chapter 2 for the process overview, then the modelling and data-collection material and Chapter 15 on integrating performance engineering into development.

**Question for Zou:** what workload, resource, and architectural information is needed to make a useful prediction before the full implementation exists?

### 6. Systems Performance: Enterprise and the Cloud — Second Edition

- **Author:** Brendan Gregg.
- **Publisher:** Addison-Wesley.
- **Source:** [Author's book page and contents](https://www.brendangregg.com/systems-performance-2nd-edition-book.html).

**Relevance:** supports empirical verification through observability, measurement, performance analysis, capacity planning, and benchmarking, with Linux as the principal implementation context.

**Start with:** Chapter 2 on methodologies, Chapter 4 on observability tools, and Chapter 12 on benchmarking.

**Question for Zou:** what measurement method and operating context make an observed result useful for evaluating a claim or revising a predictive model?

## Mapping to the evaluation model

| Model element | Most relevant books |
| --- | --- |
| Intent and specification | Specification by Example; Software Abstractions |
| Claims, assumptions, and evidence | Software for Dependable Systems |
| Predictive design checks | Performance Solutions |
| Observed behavior and measurement | Systems Performance |
| Runtime feedback and targeted revision | An Introduction to Self-adaptive Systems |

This mapping identifies reading priorities, not exclusive boundaries between the books.

## Suggested reading order

For the current conceptual stage:

1. **Software for Dependable Systems**, Chapter 2: establish the evidence and acceptance foundation.
2. **An Introduction to Self-adaptive Systems**, Chapters 1–2: understand the feedback architecture.
3. **Specification by Example**: make intent and behavior concrete.

Then choose the next emphasis:

- **Specification analysis:** Software Abstractions.
- **Prediction and measurement:** Performance Solutions, followed by Systems Performance.

Record future reading notes separately from these recommendations, identifying the chapters actually read, claims supported by the text, limitations, and proposed applications to Zou.
