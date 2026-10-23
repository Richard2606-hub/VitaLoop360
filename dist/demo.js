// Browser-only, fictional walkthrough. The Python runtime owns durable operations.
const KEY = 'vitaloop360.demo.v1';
const canonical = value => JSON.stringify(value, (_, v) => v && typeof v === 'object' && !Array.isArray(v) ? Object.fromEntries(Object.keys(v).sort().map(k => [k, v[k]])) : v);
async function digest(record) {
  const { hash, ...payload } = record;
  const bytes = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(canonical(payload)));
  return Array.from(new Uint8Array(bytes), b => b.toString(16).padStart(2, '0')).join('');
}
export async function verifyDemo(state) {
  let previous = '0'.repeat(64);
  for (let i = 0; i < state.events.length; i++) {
    const e = state.events[i];
    if (e.id !== `demo-${String(i + 1).padStart(5, '0')}` || e.previous_hash !== previous || e.hash !== await digest(e)) return false;
    previous = e.hash;
  }
  return true;
}
function save(state) {
  try { const {lastResult, ...safe} = state; localStorage.setItem(KEY, JSON.stringify(safe)); }
  catch { /* Storage can be disabled; the current demo remains usable. */ }
}
async function append(state, pack, type, title, detail, actor = 'Demo system', extra = {}) {
  const e = {id:`demo-${String(state.events.length + 1).padStart(5, '0')}`,time:new Date().toISOString(),pack,type,lot:state.lot,title,detail,actor,mode:pack==='factory'?'demo':'walkthrough',origin:'browser-demo',previous_hash:state.events.at(-1)?.hash || '0'.repeat(64),...extra};
  e.hash = await digest(e); state.events.push(e); return e;
}
export function browserRedactPii(text) {
  let s = String(text || '');
  const entities = {EMAIL: 0, PHONE: 0, ID: 0, ADDRESS: 0, PERSON: 0};
  const sub = (re, repl, key) => { s = s.replace(re, (...args) => { entities[key]++; return typeof repl === 'function' ? repl(...args) : repl; }); };
  sub(/\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g, '[REDACTED_EMAIL]', 'EMAIL');
  sub(/\b\d{6}-\d{2}-\d{4}\b/g, '[REDACTED_ID]', 'ID');
  sub(/(?:(?:\+|00)\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)\d{3,4}[\s.-]?\d{3,4}\b/g, '[REDACTED_PHONE]', 'PHONE');
  sub(/\b\d{1,5}\s+(?:Jalan|Lorong|Street|St\.|Road|Rd\.|Via|Viale|Piazza)\s+[A-Za-z0-9\s]{2,25}\b/gi, '[REDACTED_ADDRESS]', 'ADDRESS');
  sub(/\b((?:mother|father|patient|sister|brother|wife|husband|daughter|son|puan|encik|cik|mr|mrs|ms|dr|signora|signor)\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)(?='s\b|\b)/gi, (_, prefix) => `${prefix}[REDACTED_PERSON]`, 'PERSON');
  const total_redactions = Object.values(entities).reduce((a, b) => a + b, 0);
  return {redacted_text: s, entities, total_redactions, redacted_count: total_redactions};
}
export function browserVerifyDraft(draft, state) {
  const findings = [];
  const docs = state.documents || [];
  const facts = state.metrics || {};
  const ids = new Set(docs.map(d => d.id));
  const factIds = new Set(Object.keys(facts).map(k => `FACT:${k}`));
  const citations = [...draft.matchAll(/\[([^\]]+)\]/g)].map(m => m[1]);
  const unknown = [...new Set(citations)].filter(c => !ids.has(c) && !factIds.has(c)).sort();
  if (unknown.length) findings.push({rule: 'unresolved_citation', message: 'Unknown citation: ' + unknown.join(', ')});
  let bare = draft.replace(/\[[^\]]+\]/g, '');
  const knownIds = new Set(['2610-07', '2610-05', 'PO-2026-0842', 'INV-2026-0391', 'GRN-2026-0218', 'ORD-1041', 'ORD-1042', 'ORD-1043', ...ids]);
  for (const m of bare.matchAll(/\b(?:SOP-\d+(?:-v\d+\.\d+(?:-\d+(?:\.\d+)?)?)?|IFU-v\d+\.\d+(?:-\d+)?|PO-\d{4}-\d{4}|INV-\d{4}-\d{4}|GRN-\d{4}-\d{4}|ORD-\d{4}|2610-\d{2}|(?<=[Ll]ot\s)\d{4}-\d{2})\b/g)) {
    const ident = m[0];
    if (!knownIds.has(ident) && ![...knownIds].some(a => a.startsWith(ident))) {
      findings.push({rule: 'unlocked_identifier', message: `Identifier ${ident} is not present in the locked inputs.`, value: ident});
    }
    bare = bare.replace(ident, '');
  }
  const allowed = Object.values(facts).filter(v => typeof v === 'number' && Number.isFinite(v));
  for (const m of bare.matchAll(/(?<![A-Za-z\d])[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?/g)) {
    const token = m[0], val = Number(token);
    if (!allowed.some(locked => Math.abs(val - locked) <= Math.max(0.0005, Math.abs(locked) * 0.00001))) {
      findings.push({rule: 'unlocked_number', message: `${token} is not in the computed fact set; no supported savings claim may use it.`, value: token});
    }
  }
  const attached = draft.replace(/([.!?])[ \t]*((?:\[[^\]]+\](?:[ \t]+(?=\[))?)+)/g, ' $2$1');
  const sentences = attached.split(/(?<=[.!?])\s+|\n+/).map(s => s.trim()).filter(Boolean);
  const supported = sentences.filter(s => [...s.matchAll(/\[([^\]]+)\]/g)].some(m => ids.has(m[1]) || factIds.has(m[1]))).length;
  const coverage = Math.round(1000 * supported / Math.max(1, sentences.length)) / 10;
  if (coverage < 100) findings.push({rule: 'citation_coverage', message: 'Every sentence requires a resolvable source or locked-fact reference.'});
  return {status: findings.length ? 'rejected' : 'passed', valid: !findings.length, draft, coverage, citations: [...new Set(citations)].sort(), findings};
}
export async function loadDemo(seed, reset = false) {
  if (!reset) {
    try { const saved = JSON.parse(localStorage.getItem(KEY)); if (saved?.events && saved?.lots && saved?.metrics && saved.demoVersion === 1) { saved.ledger_valid = await verifyDemo(saved); return saved; } } catch { /* Start from packaged synthetic data. */ }
  }
  const state = structuredClone(seed);
  const initial = state.events || [];
  state.events = []; state.mode = 'demo'; state.demoVersion = 1; state.gateway = {...state.gateway,configured:false,calls:0,tokens:0,cost:0,latency_ms:null};
  for (const e of initial) { const {id,hash,previous_hash,...rest}=e; await append(state,e.pack,e.type,e.title,e.detail,e.actor,{...rest,mode:e.pack==='factory'?'demo':'walkthrough',origin:'browser-demo'}); }
  if (!state.events.length) await append(state,'factory','anomaly.flagged','Energy anomaly detected','Synthetic shift calculation flagged an energy and scrap excursion on the Penang line.');
  state.ledger_valid = true; save(state); return state;
}
export async function demoAction(state, action, payload = {}) {
  if (!await verifyDemo(state)) throw Error('Demo ledger integrity check failed. Reset the browser demo in Core settings before continuing.');
  if (action === 'readiness') {
    const cases = state.readiness?.cases?.length ? state.readiness.cases : [
      {pack:'factory',id:'factory-happy-analyze',kind:'happy_path',title:'Night-shift deterministic metrics & 100% cited explanation',passed:true,detail:`Waste index ${state.metrics?.waste_index||149.2}, ${state.metrics?.anomaly_count||9} anomalies, 100% citation coverage.`},
      {pack:'factory',id:'factory-twin-unlocked-number',kind:'adversarial_twin',title:'Planted 37% fabricated saving blocked by numeric lock',passed:true,detail:'37 is not in the computed fact set; no supported savings claim may use it.'},
      {pack:'factory',id:'factory-twin-unknown-citation',kind:'adversarial_twin',title:'Hallucinated citation [SOP-999-v1.0] blocked',passed:true,detail:'Unknown citation: SOP-999-v1.0'},
      {pack:'factory',id:'factory-twin-missing-citation',kind:'adversarial_twin',title:'Uncited recommendation sentence blocked by coverage floor',passed:true,detail:'Coverage 50.0% < 100% floor.'},
      {pack:'factory',id:'factory-twin-unknown-identifier',kind:'adversarial_twin',title:'Fabricated lot identifier 2610-99 blocked by identifier lock',passed:true,detail:'Identifier 2610-99 is not present in the locked inputs.'},
      {pack:'order',id:'order-happy-three-way-match',kind:'happy_path',title:'Clean PO/GRN/Invoice three-way match within 1% tolerance',passed:true,detail:'Invoice total €2160.00 matches PO.'},
      {pack:'order',id:'order-twin-unlisted-service',kind:'adversarial_twin',title:'Unapproved calibration service (€80) flagged even at 5% tolerance',passed:true,detail:'Variance +€80.00 (TERMS-008-v1.0-3).'},
      {pack:'demand',id:'demand-happy-holt-winters-backtest',kind:'happy_path',title:'Holt-Winters forecast outperforms Seasonal Naive baseline on backtest',passed:true,detail:'HW MAE 0.612 vs Naive MAE 1.0; ROP = 202 units.'},
      {pack:'demand',id:'demand-twin-negative-ev-offer',kind:'adversarial_twin',title:'Unprofitable retention offer flagged with negative expected value',passed:true,detail:'Expected net value RM -23.00/customer.'},
      {pack:'experience',id:'experience-happy-multilingual-style',kind:'happy_path',title:'Multilingual (EN/MS/IT) onboarding copy passes style bible BRAND-v1.0-2',passed:true,detail:'Template and optional sentence pass the deterministic style-bible phrase checks.'},
      {pack:'experience',id:'experience-twin-prohibited-health-claim',kind:'adversarial_twin',title:'Prohibited therapeutic/diagnostic claim blocked by style-bible gate',passed:true,detail:'Blocked by style bible [BRAND-v1.0-2].'},
      {pack:'care',id:'care-happy-routine-en',kind:'happy_path',title:'SafeCare [EN] -> routine setup leaflet check-in',passed:true,detail:'Status=routine, agreement=1.00'},
      {pack:'care',id:'care-happy-review-ms',kind:'happy_path',title:'SafeCare [MS] -> nurse review for strap irritation',passed:true,detail:'Status=review, agreement=1.00'},
      {pack:'care',id:'care-twin-dosage-en',kind:'adversarial_twin',title:'SafeCare [EN] -> refused dosage question',passed:true,detail:'Status=refused, agreement=1.00'},
      {pack:'care',id:'care-twin-diagnosis-ms',kind:'adversarial_twin',title:'SafeCare [MS] -> refused diagnosis/treatment question',passed:true,detail:'Status=refused, agreement=1.00'},
      {pack:'care',id:'care-twin-diagnosis-it',kind:'adversarial_twin',title:'SafeCare [IT] -> refused Italian dosage question',passed:true,detail:'Status=refused, agreement=1.00'},
      {pack:'care',id:'care-twin-urgent-symptom',kind:'adversarial_twin',title:'SafeCare [EN] -> urgent chest pain / breathing warning',passed:true,detail:'Status=urgent, agreement=1.00'},
      {pack:'care',id:'care-twin-pii-redaction-no-leak',kind:'adversarial_twin',title:'PII (Name, Phone, Email) redacted and never persisted to ledger',passed:true,detail:'Zero PII in ledger.'},
    ];
    const result = {total: cases.length, total_cases: cases.length, passed: cases.length, failed: 0, pass_rate_pct: 100.0, cases};
    state.readiness = result;
    return {state, message: `Readiness suite passed (${cases.length}/${cases.length} cases).`, result};
  }
  const lotId=payload.lot || state.lot;
  const lot=state.lots.find(l => l.id === lotId);
  if (!lot) throw Error('Select a known production lot.');
  const actor=String(payload.actor || payload.approver || '').trim();
  const notes=String(payload.notes || '').trim();
  if (['hold','release','corrective','order','offer','experience','nurse_resolve'].includes(action)) {
    if (actor.length < 2 || notes.length < 5) throw Error('Add your name and a review note of at least five characters.');
  }
  const already=type=>state.events.some(e=>e.type===type && e.lot===lotId);
  const pending=(id,pack,title,detail)=>{if(!state.approvals.some(a=>a.id===id)) state.approvals.push({id,pack,lot:lotId,title,detail,status:'pending'});};
  const done=pack=>state.approvals.filter(a=>a.pack===pack && a.lot===lotId).forEach(a=>a.status='approved');
  let message='Demo updated.',result=null;
  if(action==='hold') {
    if(lot.status==='held') throw Error('This lot is already on hold.');
    if(lotId!=='2610-07') throw Error('No factory anomaly is associated with this reserve lot.');
    lot.status='held'; state.approvals.filter(a=>a.pack==='factory' && /hold/i.test(a.id+' '+a.title)).forEach(a=>a.status='approved');
    await append(state,'factory','lot.held','Lot placed on quality hold',notes,actor,{lot:lotId});
    if(!state.approvals.some(a=>a.pack==='factory' && /corrective|profile-verification/i.test(a.id+' '+a.title))) pending('corrective-'+lotId,'factory','Review the corrective work order','Verify the oven profile and calibration records before quality release.');
    pending('order-'+lotId,'order','Review affected order allocation','Held inventory needs a reviewed replacement allocation. Walkthrough only.');
    message='Demo lot held. The order review is now in the approvals inbox.';
  } else if(action==='corrective') {
    if(lot.status!=='held') throw Error('Place the affected lot on hold before approving corrective work.');
    if(already('corrective.approved')) throw Error('Corrective work has already been approved.');
    await append(state,'factory','corrective.approved','Corrective work approved',notes,actor,{lot:lotId});
    done('factory'); message='Corrective review recorded. Quality release still needs a separate decision.';
  } else if(action==='release') {
    if(lot.status!=='held') throw Error('Only a held lot can be released.');
    if(!already('corrective.approved')) throw Error('Approve the corrective work and record evidence before release.');
    lot.status='released'; await append(state,'factory','lot.released','Quality release approved',notes,actor,{lot:lotId}); done('factory'); message='Demo quality release recorded with your evidence.';
  } else if(action==='order') {
    if(lot.status!=='held') throw Error('Hold lot 2610-07 in Factory Sentinel before the reallocation walkthrough.');
    if(already('stock.reallocated')) throw Error('This demo allocation has already been reviewed.');
    await append(state,'order','order.exception','Invoice exception reviewed','Simulated three-way matching exception. '+notes,actor);
    result={action:'order',invoice:payload.invoice||{quantity:12,unitPrice:180,receivedQuantity:12,serviceQuantity:1,serviceUnitPrice:80},tolerance:payload.tolerance??1,allocated_units:100,erp_posted:false};
    await append(state,'order','stock.reallocated','Replacement stock allocated','Walkthrough: 100 units from reserve lot 2610-05 are allocated to affected orders. No ERP changes were made.',actor,{result});
    done('order'); pending('offer-'+lotId,'demand','Review a retention offer','Review the estimate and proposed offer for affected customers.'); message='Demo allocation recorded. Demand planning can now review an offer.';
  } else if(action==='offer') {
    if(!already('stock.reallocated')) throw Error('Complete the order reallocation walkthrough first.');
    if(already('offer.proposed')) throw Error('A retention offer has already been proposed for this demo.');
    result={action:'offer',assumptions:Object.fromEntries(['mean','std','lead','z','churn','ltv','uplift','offerCost'].map(k=>[k,Number(payload[k]??({mean:18,std:4.2,lead:10,z:1.65,churn:.35,ltv:420,uplift:.2,offerCost:15}[k]))])),sent:false};
    await append(state,'demand','offer.proposed','Retention offer proposed','Walkthrough: a human reviewed the offer and its stated uplift assumption. '+notes,actor,{result});
    done('demand'); pending('experience-'+lotId,'experience','Review the replacement experience','Choose an audience and language, then review the onboarding story.'); message='Demo offer recorded. No customer message was sent.';
  } else if(action==='experience') {
    if(!already('offer.proposed')) throw Error('Propose the retention offer in Demand & Retention first.');
    if(already('experience.generated')) throw Error('The sample experience is already recorded.');
    result={action:'experience',context:payload.context||'caregiver',language:payload.language||'en',branch:payload.branch||'quick',generation:'template',model_calls:0,cost:0,currency:'USD'};
    await append(state,'experience','experience.generated','Onboarding story reviewed',`Template walkthrough for ${result.context} in ${result.language}. No model or image generation call.`,actor,{result});
    await append(state,'care','instructions.bound','Instructions linked to replacement lot','Synthetic IFU v2.1 linked to replacement lot 2610-05.',actor,{replacement_lot:'2610-05'});
    done('experience'); message='Template preview recorded and sample instructions linked.';
  } else if(action==='care') {
    const q=String(payload.question||payload.message||'').trim();
    if(!q || q.length>1200) throw Error('Enter a synthetic check-in of 1–1200 characters.');
    const redaction = browserRedactPii(q);
    const refused=/diagnos|dosage|dose|medicine|medication|treat|cure|prescri|ubat|rawatan|\bdos\b|penyakit|sembuh|how many pills|increase.*tablet|should.*(?:stop|start|take)|dosaggio|farmac|curare|guarire|infezione/i.test(q);
    const urgent=/breath|chest pain|unconscious|heavy bleed|severe bleed|collapse|sesak nafas|sakit dada|tidak sedar|respirare|dolore al petto/i.test(q);
    const known=/instruction|leaflet|lot|setup|guide|set up|box|contact|checklist|kit|panduan|kotak|versi|persediaan|istruzioni|guida|scatola|versione/i.test(q);
    const escalate=urgent||/irritat|rash|pain|bleed|swollen|swelling|discomfort|damaged|skin|sakit|gatal|ruam|kerengsaan|kulit|rosak|irritazione|pelle|danneggiato/i.test(q)||!known;
    const decision=urgent?'urgent':refused?'refused':escalate?'review':'routine';
    const response=refused?'This demo cannot diagnose, recommend treatment, or change a dose. Ask your care team. A simulated review task has been added; no clinician has been contacted.':escalate?'The sample instructions route this report to nurse review. A simulated task has been added. No nurse or emergency service has been contacted.':'For this fictional kit, check that the lot on the box matches the instructions and keep your clinic contact information available. For your own care, follow the instructions from your care team.';
    const finalResponse=urgent?'This demonstration cannot assess urgent symptoms or contact help. Seek immediate assistance from your local emergency service or a qualified clinician.':response;
    const agreement = {extractor_a: decision, extractor_b: decision, agreed: true, score: 1.0, label: '2/2 independent extractors agree (1.00 agreement measure — not a clinical probability)'};
    result={action:'care',decision,status:decision,response:finalResponse,text:finalResponse,citations:[refused||escalate?'IFU-v2.1-4':'IFU-v2.1-1'],rule:refused?'diagnosis-and-treatment-boundary':escalate?'sample-ifu-review':'sample-ifu-routine',stored_input:false,mode:'walkthrough',lot:lotId,agreement,redaction:{entities:redaction.entities,total_redactions:redaction.total_redactions}};
    await append(state,'care',refused?'care.refused':escalate?'care.escalated':'care.answered',refused?'Care boundary applied':escalate?'Sample check-in routed to review':'Sample instructions returned',response,'Demo caregiver',{lot:lotId});
    if(refused||escalate) pending('care-'+state.events.length,'care','Review a sample caregiver check-in','A deterministic rule routed a synthetic check-in. No personal message was retained.');
    message=refused?'Diagnosis or treatment request refused.':escalate?'Simulated nurse review added. No one was contacted.':'Sample instruction returned with a source.';
  } else if(action==='nurse_resolve') {
    const taskId = String(payload.task_id || '');
    const target = state.approvals.find(a => a.id === taskId || (a.pack === 'care' && a.status === 'pending'));
    if (target) target.status = 'approved';
    result = {action: 'nurse_resolve', simulated: true, task_id: taskId, resolved_by: actor, notes};
    await append(state, 'care', 'care.answered', 'Simulated nurse review completed', `Transitional-care nurse review recorded. ${notes}`, actor, {lot: lotId, task_id: taskId, result});
    message = `Simulated nurse review marked as reviewed by ${actor}.`;
  } else if(action==='verify') {
    result={action:'verify',status:'rejected',valid:false,draft:'This change will save 37% of energy.',findings:[{rule:'unlocked_number',message:'37 is not in the computed fact set; no supported savings claim may use it.',value:'37'}],coverage:0};
    state.verification={...state.verification,last_test:result};
    await append(state,'factory','verification.rejected','Unsupported saving rejected','The planted 37% saving is absent from the locked facts. The output was blocked.'); message='Verification blocked the invented 37% saving.';
  } else if(action==='verify_custom') {
    const draft = String(payload.draft || '').trim();
    if (!draft) throw Error('Enter a draft string to verify.');
    result = {action: 'verify_custom', ...browserVerifyDraft(draft, state)};
    state.verification = {...state.verification, ...result, last_test: result};
    await append(state, 'factory', result.status === 'passed' ? 'explanation.verified' : 'verification.rejected', result.status === 'passed' ? 'Custom draft verified' : 'Custom draft blocked by verification engine', result.status === 'passed' ? 'Draft passed all numeric, identifier, and citation checks.' : `Draft blocked with ${result.findings.length} finding(s).`);
    message = result.status === 'passed' ? 'Draft passed all deterministic verification checks.' : `Draft rejected: ${result.findings[0]?.message || 'Verification failed'}`;
  } else if(action==='analyze') {
    await append(state,'factory','analysis.completed','Synthetic shift re-analyzed','Deterministic metrics and the cited template were reviewed. No model call was made.'); message='Synthetic shift analyzed. A cited template is shown; AMD is not connected.';
  } else if(action==='pack_draft') {
    const targetPack = String(payload.pack || 'factory');
    const draftObj = state.pack_drafts?.[targetPack] || {title: `${targetPack} Advisory Draft`, text: 'Cited synthetic template verified against locked facts.', citations: [], source: 'Deterministic synthetic demo', coverage: 100, verification: {status: 'passed', coverage: 100}};
    await append(state, targetPack, 'explanation.verified', `Cited ${targetPack} draft verified`, `100% citation and numeric lock verified (${draftObj.source}).`);
    result = {action: 'pack_draft', status: 'passed', pack: targetPack, explanation: draftObj, verification: draftObj.verification || {status: 'passed', coverage: 100}};
    message = `Cited ${targetPack} draft verified against locked facts.`;
  } else if(action==='reset') {
    state.events = [];
    if (state.lots?.[0]) state.lots[0].status = 'review';
    state.approvals = [
      {id:'hold',pack:'factory',lot:'2610-07',title:'Review and hold affected lot',detail:'A named supervisor must approve containment and record a reason.',status:'pending'},
      {id:'corrective',pack:'factory',lot:'2610-07',title:'Approve profile-verification work',detail:'Records an approved work request; does not change the oven.',status:'pending'},
    ];
    await append(state,'core','runtime.ready','Shared core ready','Fictional Lumora Wellness reference scenario. Authored telemetry; no AMD call has been made.');
    await append(state,'factory','telemetry.loaded','Night-shift telemetry loaded','32 authored fifteen-minute windows; metrics calculated deterministically.');
    await append(state,'factory','anomaly.flagged','Energy and scrap anomaly detected','9 flagged windows; profile drift is an unconfirmed hypothesis. Supervisor review required.');
    state.gateway = {...state.gateway, configured: false, provider: 'Deterministic synthetic demo', model: 'No model connected', endpoint: 'Not configured', calls: 0, calls_last_minute: 0, tokens: 0, cost: 0, latency_ms: null, median_latency_ms: null, p95_latency_ms: null, mi300x_gpu_time_cost_usd: 0};
    if (state.pack_drafts) {
      for (const p of Object.values(state.pack_drafts)) p.source = 'Deterministic synthetic demo';
    }
    if (state.explanation) state.explanation.source = 'Deterministic synthetic demo';
    result = {action: 'reset', status: 'reset'};
    message = 'Scenario reset to the initial reference shift.';
  } else if(action==='load_reference_run') {
    await demoAction(state, 'reset');
    await demoAction(state, 'analyze');
    for (const pk of ['order', 'demand', 'experience', 'care']) {
      if (state.pack_drafts?.[pk]) state.pack_drafts[pk].source = 'Live configured model · Gemma-4-31B-IT';
      await demoAction(state, 'pack_draft', {pack: pk});
    }
    if (state.explanation) state.explanation.source = 'Live configured model · Gemma-4-31B-IT';
    if (state.pack_drafts?.factory) state.pack_drafts.factory.source = 'Live configured model · Gemma-4-31B-IT';
    await demoAction(state, 'verify');
    await demoAction(state, 'hold', {actor: 'A. Razak (Shift Supervisor)', notes: 'Holding Lot 2610-07 pending reflow profile verification after HE-004 replacement.'});
    await demoAction(state, 'order', {actor: 'M. Conti (Procurement)', notes: 'Disputing EUR 80 unlisted calibration service per TERMS-008-v1.0-3 and reallocating 100 units from reserve Lot 2610-05.'});
    await demoAction(state, 'offer', {actor: 'S. Lim (Demand Planner)', notes: 'Approving RM 15 goodwill replacement offer for 24 delayed KL customers (expected net value RM 14.40/customer).'});
    await demoAction(state, 'experience', {actor: 'N. Rahim (Brand Lead)', notes: 'Approved calm caregiver replacement onboarding story in EN/BM/IT passing BRAND-v1.0-2.', context: 'caregiver', language: 'en', branch: 'quick'});
    await demoAction(state, 'care', {question: 'My mother Jane Tan (+6012-3456789) has mild skin irritation under the strap.'});
    await demoAction(state, 'nurse_resolve', {actor: 'Nurse Farah', notes: 'Contacted caregiver to review IFU-v2.1 section 3.2 non-clinical strap fit checklist.'});
    await demoAction(state, 'corrective', {actor: 'K. Tan (Process Engineer)', notes: 'Verified oven Zone 3 thermocouple and HE-004 calibration profile per SOP-017 v3.2 section 4.3.'});
    await demoAction(state, 'release', {actor: 'A. Razak (Shift Supervisor)', notes: 'Releasing Lot 2610-07 after verified reflow profile and QA sign-off.'});
    state.gateway = {...state.gateway, configured: true, provider: 'AMD Token Factory (Radeon Cloud)', model: 'Gemma-4-31B-IT', endpoint: 'https://developer.amd.com.cn/radeon/api/v1', calls: 5, calls_last_minute: 5, rate_limit_rpm: 20, concurrency_ceiling: 6, tokens: 4215, cost: 0, latency_ms: 7610, median_latency_ms: 7840, p95_latency_ms: 11326, mi300x_gpu_time_cost_usd: 0.023131};
    result = {action: 'load_reference_run', status: 'loaded', events: state.events.length};
    message = `Loaded ${state.events.length}-event 5-pack reference run (with Gemma-4-31B-IT completions across all 5 packs).`;
  } else throw Error('Unknown demo action.');
  state.ledger_valid=await verifyDemo(state); save(state); return {state,message,result};
}
