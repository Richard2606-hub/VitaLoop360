# Acceptance checklist

Use this checklist against the running application. An unchecked item is not a claim that it has passed. The proposal's broader production and submission commitments are recorded separately from this prototype's acceptance criteria.

## Local product acceptance

- [ ] Start from the documented command without an API key. The console loads and clearly identifies synthetic demo mode.
- [ ] Open every navigation destination, including all five capability packs, the lot thread, approvals, and audit view. Each page has usable content and no unhandled error.
- [ ] Inspect the incident and reserve lots. The console makes clear that factory telemetry belongs to incident lot `2610-07`; reserve lot `2610-05` is illustrative replacement stock, not a separately analyzed shift.
- [ ] Calculate a factory result. Energy per good unit uses energy divided by good units; scrap rate uses scrap divided by total units. Any baseline and tariff assumptions are visible.
- [ ] Check a displayed savings estimate against the documented calculation. Its currency, tariff assumption, and estimated status are visible.
- [ ] Generate the factory explanation with no provider configured. The result is labelled as deterministic authored demonstration text, with no invented AMD call, tokens, model latency, or provider cost.
- [ ] Open a citation from a factory explanation. Its document, version, and passage resolve to the source text actually supplied.
- [ ] Run the fabricated-number challenge. The false figure is blocked with a named finding; the rejected text is not presented as a verified recommendation.
- [ ] Submit a draft with a missing or unknown citation. Verification fails with an intelligible finding.
- [ ] Request a lot hold. It requires a named approver and shows evidence for the decision. A pending request alone does not hold the lot.
- [ ] Approve the request once. The lot status and thread update, and the ledger records the approval and event. Repeating the action does not silently duplicate the approved change.
- [ ] Attempt to release the incident lot before holding it or before recording corrective approval after the latest hold. The server refuses the invalid transition.
- [ ] Compare the four downstream pack pages and their timeline events. Every simulation is visibly marked as a walkthrough or specified pack.
- [ ] Use the care walkthrough. It contains only fictional content, indicates human review, and makes no claim that an actual nurse has been contacted.
- [ ] Verify the audit chain after several actions. The result is accurate, and refreshing/restarting the server retains the saved records.
- [ ] Export or inspect audit records. Decisions carry a lot, time, action, and evidence where applicable; configured secret values are absent.
- [ ] Narrow the browser to a phone-sized viewport. Navigation, tables, dialogs, and action buttons remain usable without clipping essential controls.

## Configured model acceptance (requires a real endpoint)

- [ ] Configure the exact provider base URL, model identifier, and key from the deployment. Do not infer AMD hosting from a name in a configuration field.
- [ ] Complete a real factory explanation request. The console shows the configured endpoint and returned model, measured request latency, and provider-reported token usage when available.
- [ ] Confirm a failed provider request produces an explicit error, with no success label or fabricated telemetry.
- [ ] Confirm the model receives only the locked calculation facts and relevant fictional source passages.
- [ ] Confirm the returned explanation passes the same numeric and citation checks as the offline demonstration.
- [ ] When usage or pricing is absent, show it as unavailable rather than implying a measured cost of zero.
- [ ] Verify only an operator-configured AMD deployment may be described as an AMD run; save independent deployment evidence before any hardware or prize-eligibility claim.

## Proposal release gates still requiring separate work

These are not implied by a passing local demonstration:

- [ ] Source and license the proposed public datasets, implement their adapters, and validate the telemetry mapping.
- [ ] Implement and validate every claimed anomaly method, forecast, survival model, privacy guard, and document retrieval guarantee.
- [ ] Record a real Gemma completion on verified AMD infrastructure with auditable telemetry.
- [ ] Implement replay from a recorded run separately from synthetic demo mode; implement the proposal's batch-input execution mode.
- [ ] Validate installable pack manifests, schemas, capability permissions, quarantine behavior, and event subscriptions.
- [ ] Deploy and verify the required Evolus workspace, building blocks, main agent, and AMD vLLM deployment before claiming that integration.
- [ ] Conduct clinical, security, access-control, and operational review before any patient-facing or plant-connected use.
- [ ] Build and test a container from a clean clone on another machine; publish and verify the application URL externally.
- [ ] Prepare the proposal's cover image, slide deck, video, public repository, and submission materials; independently verify current event rules and eligibility.

## Audit assurance boundary

A passing SHA-256 chain check means that the records read by this process form a consistent chain. Without an independently stored checkpoint or signature, a person who can rewrite the whole ledger can recompute its hashes, and deleting a valid suffix may not be detectable. It is not proof of identity, completeness, regulatory compliance, or immutable storage.
