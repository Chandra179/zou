# Initial chat design review and evidence gaps

Record: `EVIDENCE-DESIGN-001`. Date: 3 November 2026.

Specification: [`chat-mvp` version 0.1](../specification.yaml). Design: [`chat-design-v0.1`](../system-design.md). Guidance: [evaluation-pattern.yaml](../../../evaluation-pattern.yaml).

## Decision and conditions

Decision under evaluation: is there enough confirmed intent and a sufficiently bounded design to begin the authentication/encryption and gateway investigations?

Reviewed material: the user's answers in this chat, the implementation plan subsequently supplied by the user, the current repository documents, and official technical documentation linked below. The latest request is to create documentation; this record does not authorize or claim application implementation or cloud provisioning.

Repository baseline before documentation changes: `9d28f66fad02a744862e5d567ed3d2a152ab3fec`. The working tree already contained a modified README and untracked research documents and evaluation guidance. Those existing changes are not application implementation. New design/specification files are uncommitted, so their identity is the versioned document set in the delivered working tree rather than a nonexistent application revision. Future execution records must identify a committed revision or content hashes of all evaluated inputs.

No application runtime, SDK version, browser compatibility matrix, deployment, or workload execution was available. No measured application results are inferred from the design.

## Observations and limitations

| Observation | Evidence | Limitation |
| --- | --- | --- |
| The starting repository contains research and guidance, with no application source or package manifest | File inventory, README, and Git status inspection | An inventory establishes the starting state, not app feasibility |
| Product choices are concrete enough for a bounded design | Source ledger U-01 through U-04 and P-01, with checkable claims in the registry | User choices establish intended behavior, not specification completeness or satisfaction |
| WebAuthn defines a single-device credential through backup eligibility | [WebAuthn Level 3](https://www.w3.org/TR/webauthn-3/) | No authenticator or verification library was executed; no hardware-attestation guarantee follows |
| SimpleWebAuthn documents server-side registration/authentication support and credential metadata | [Server documentation](https://simplewebauthn.dev/docs/packages/server) | No version is installed or compatibility-tested |
| Matrix provides a browser SDK with Rust/WASM crypto and persistent storage; concurrent store access is a documented concern | [Matrix SDK documentation](https://matrix-org.github.io/matrix-js-sdk/) | Does not demonstrate the proposed no-recovery, fixed-device workflow |
| The SDK exposes client transport configuration | [SDK client options](https://matrix-org.github.io/matrix-js-sdk/interfaces/matrix.IMatrixClientCreateOpts.html) | Does not establish that the proposed gateway allowlist is sufficient or secure |
| Synapse documents JWT login and explicit device IDs | [JWT login documentation](https://element-hq.github.io/synapse/latest/jwt.html) | Disabled-public-signup provisioning, repeated login, token invalidation, and device preservation need execution |
| Matrix documents transaction identifiers for idempotent request retransmission | [Matrix transaction identifiers](https://spec.matrix.org/latest/client-server-api/#transaction-identifiers) | No proof that the proposed outbox preserves scope through its actual SDK lifecycle |
| Managed private-service hosting is available in the proposed provider's documentation | [Render private services](https://render.com/docs/private-services) | No configuration is deployed; isolation, persistence, cost, and capacity remain unknown |

Sources were consulted on the record date. These are documentation observations, not security certification, experimental reproduction, or measured evidence of the chat application's behavior.

## Claim status

All 15 application claims in the registry are **UNVERIFIED**. No implementation check has been run.

| Claims | Required next evidence |
| --- | --- |
| AUTH-001, AUTH-002, DEVICE-001 | I-01 authentication and persistent-device scenarios, session revocation, and credential/store failure cases |
| CONTACT-001, ACCESS-001, DEPLOYMENT-001 | I-02 gateway tests and I-03 room reconciliation; I-05 external deployment isolation |
| MESSAGE-001, MESSAGE-002 | I-01 real encrypted exchange and I-03 lost-response/retry/reconnect scenarios |
| PRIVACY-001, TRUST-001 | I-04 verification plus payload/storage/log inspection under the declared threat boundary |
| BLOCK-001 | I-03 send/block ordering and I-02 room/to-device bypass tests |
| REPORT-001, OPERATIONS-001, UX-001 | I-05 UI, report-disclosure, operator authorization, suspension, and observability checks |
| PERFORMANCE-001 | I-05 real 20-client ten-minute workload with recorded environment and delivery failures |

## Design issues identified and targeted revisions

1. **UI-only policy would be insufficient.** The design now requires private Synapse and gateway checks across room, key, and to-device paths. Exact supported SDK routes remain an I-02 deliverable, not an assumed fact.
2. **Device-bound sign-in does not bind message keys to hardware.** The design distinguishes authenticator credentials, local crypto storage, and supported browser-profile behavior. Lost-store handling must not initialize replacement keys.
3. **Blocking cannot retract previously accepted messages.** The design defines its effective point at gateway authorization and requires explicit classification of already authorized or indeterminate sends. I-03 must measure actual race behavior.
4. **Room creation spans two systems.** The design requires durable provisioning and reconciliation before returning a canonical room; no cross-system atomicity is claimed. I-03 must establish the recovery method.
5. **No recovery may conflict with SDK setup conventions.** I-01/I-04 must verify encryption and optional contact verification without enabling secret backups or replacement devices.
6. **Reporting deliberately reveals selected plaintext.** The privacy boundary and report check now distinguish explicit disclosures from ordinary-message leakage. Submitted text is not treated as independently verified authorship evidence.

These revisions clarify proposed design and scope. They do not weaken the agreed E2EE, device-bound sign-in, or authorization requirements, and they do not count as successful implementation checks.

## Documentation checks

Checks on this document set are limited to parsing, reference consistency, repository-relative link resolution, and whitespace. They do not verify any application claim.

Environment: Python 3.12.3, PyYAML 6.0.1, Git 2.43.0; local working tree, no application runtime. A one-off Python check parsed the registry with duplicate-key rejection, compared references against registry keys, resolved local paths, and inspected the four changed/new documentation files. It did not execute the named application checks.

| Documentation check | Actual result | Scope |
| --- | --- | --- |
| YAML syntax, unique keys, claim identity, and classification | VERIFIED: 15 uniquely identified outcome/invariant/constraint entries | Registry structure only |
| Claim source/check/dependency/condition references | VERIFIED: all referenced IDs exist; all claims remain unverified with empty evidence lists | Reference integrity, not completeness or correctness of acceptance criteria |
| Local links | VERIFIED: 14 local Markdown links and three YAML document references resolve | README and new document set; external URLs were read, not continuously monitored |
| Whitespace and Markdown structure | VERIFIED: final newlines, no trailing whitespace, balanced code fences, heading spacing; `git diff --check` passed | Four files; untracked files were inspected directly because Git diff omits them |

Evaluated input SHA-256 hashes:

```text
3c63315b9b67148bdaf3134c46af883af3da3e350ddd19971578d45ebca2a9d3  docs/chat/system-design.md
7d224ad171dd87a5a391fafbd8913ff6c1fcda2a6003793c54381540f83eaed7  docs/chat/specification.yaml
bf7b0a8bf815c7b9febca718cfec95928f2545439721399ec226f64fdd48e1e1  evaluation-pattern.yaml
```

These checks establish a consistent documentation set, not a verified design or executable app. The recorded hashes identify specification/design inputs; this evolving evidence record has no self-referential hash.

## Decision

**Proceed to bounded investigation**, starting with I-01 and I-02. Do not accept the application or declare the full architecture verified.

Stopping rule for this review: scoped outcomes have checkable criteria and material unknowns have named investigations or launch decisions. Exhaustive scenario discovery is not claimed. If a prototype contradicts a dependency assumption, revise the implicated integration and re-evaluate affected claims; do not silently relax acceptance criteria.

Remaining launch decisions: stable domain and identity configuration, hosting region and budget, resource sizing, data retention/deletion and notices, operational response, and backup policy. Local feasibility investigation can proceed without those decisions; public pilot readiness cannot.

Revisit this record's conclusions when a requirement changes, a selected dependency fails the integration checks, a new privacy/authorization path is found, or the workload or deployment assumptions change. Future evidence records must preserve the check procedure, tool and environment versions, code/configuration identity, raw results or artifact references, uncertainty, and a scoped decision.
