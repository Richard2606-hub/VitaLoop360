import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {webcrypto} from 'node:crypto';
globalThis.crypto ??= webcrypto;
const cache = new Map();
globalThis.localStorage = {getItem:key=>cache.get(key)||null,setItem:(key,value)=>cache.set(key,value)};
const {loadDemo, demoAction, verifyDemo, browserRedactPii, browserVerifyDraft} = await import('../dist/demo.js');
const seed=JSON.parse(await readFile(new URL('../dist/demo-data.json',import.meta.url),'utf8'));
const state=await loadDemo(seed,true);
const reviewer={actor:'Test Reviewer',notes:'Synthetic evidence reviewed.'};
assert.equal(await verifyDemo(state),true);
await assert.rejects(demoAction(state,'hold',{}),/name/);
await assert.rejects(demoAction(state,'release',reviewer),/held/);
await demoAction(state,'hold',reviewer);
assert.equal(state.lots[0].status,'held');
await assert.rejects(demoAction(state,'release',reviewer),/corrective/);
assert.equal(state.approvals.filter(a=>a.pack==='factory'&&a.status==='pending').length,1);
await assert.rejects(demoAction(state,'offer',reviewer),/reallocation/);
await demoAction(state,'order',reviewer);
await demoAction(state,'offer',reviewer);
await demoAction(state,'experience',{...reviewer,context:'caregiver',language:'it',branch:'detailed'});
assert.ok(state.events.some(e=>e.type==='instructions.bound'));
for(const [question,expected] of [
  ['What dose of medicine?','refused'],
  ['Berapa dos ubat?','refused'],
  ['Quale dose di farmaco?','refused'],
  ['The strap irritates the skin.','review'],
  ['Kerengsaan kulit.','review'],
  ['Irritazione cutanea.','review'],
  ['An unexplained question','review'],
  ['Where is the setup guide?','routine'],
  ['Dove trovo la guida rapida?','routine'],
  ['Cannot breathe','urgent'],
  ['Dolore al petto','urgent']
]) {
  const r=await demoAction(state,'care',{question,lot:'2610-05'});
  assert.equal(r.result.status,expected);
  assert.equal(JSON.stringify(state.events).includes(question),false,'Never store raw check-in text');
}
const piiSample=browserRedactPii('Patient Jane Doe email jane@example.com phone +60 12-345 6789 at 14 Jalan Ampang');
assert.equal(piiSample.redacted_text.includes('Jane'),false);
assert.equal(piiSample.redacted_text.includes('jane@example.com'),false);
assert.ok(piiSample.redacted_count>=3);
const nurseTask=state.approvals.find(a=>a.pack==='care'&&a.status==='pending');
assert.ok(nurseTask);
await demoAction(state,'nurse_resolve',{...reviewer,task_id:nurseTask.id});
assert.equal(state.approvals.find(a=>a.id===nurseTask.id).status,'approved');
const rejection=await demoAction(state,'verify');
assert.equal(rejection.result.status,'rejected');
const customRejection=await demoAction(state,'verify_custom',{draft:'Lot 9999-88 scrap was 37% per [SOP-999-v1.0].'});
assert.equal(customRejection.result.status,'rejected');
assert.ok(browserVerifyDraft('Lot 9999-88 scrap was 4.09% per [SOP-017-v3.2-4.2].',state).findings.some(r=>r.rule==='unlocked_identifier'));
const readiness=await demoAction(state,'readiness');
assert.equal(readiness.result.failed,0);
assert.ok(readiness.result.total>=18);
await demoAction(state,'corrective',reviewer);
await demoAction(state,'release',reviewer);
assert.equal(state.lots[0].status,'released');
assert.equal(await verifyDemo(state),true);
const restored=await loadDemo(seed);
assert.equal(restored.lots[0].status,'released');
restored.events[0].detail='tampered';
assert.equal(await verifyDemo(restored),false);
await assert.rejects(demoAction(restored,'analyze'),/integrity/);
console.log('Browser domain checks passed: approvals, dependency chain, care boundaries, PII redaction, readiness suite, persistence, hash integrity.');
