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
  const lotId=payload.lot || state.lot;
  const lot=state.lots.find(l => l.id === lotId);
  if (!lot) throw Error('Select a known production lot.');
  const actor=String(payload.actor || payload.approver || '').trim();
  const notes=String(payload.notes || '').trim();
  if (['hold','release','corrective','order','offer','experience'].includes(action)) {
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
    result={action:'experience',context:payload.context||'caregiver',language:payload.language||'en',branch:payload.branch||'quick',generation:'template',model_calls:0};
    await append(state,'experience','experience.generated','Onboarding story reviewed',`Template walkthrough for ${result.context} in ${result.language}. No model or image generation call.`,actor,{result});
    await append(state,'care','instructions.bound','Instructions linked to replacement lot','Synthetic IFU v2.1 linked to replacement lot 2610-05.',actor,{replacement_lot:'2610-05'});
    done('experience'); message='Template preview recorded and sample instructions linked.';
  } else if(action==='care') {
    const q=String(payload.question||payload.message||'').trim();
    if(!q || q.length>1200) throw Error('Enter a synthetic check-in of 1–1200 characters.');
    const refused=/diagnos|dosage|dose|medicine|medication|treat|cure|prescri|ubat|rawatan|\bdos\b|penyakit|sembuh|how many pills|increase.*tablet|should.*(?:stop|start|take)/i.test(q);
    const urgent=/breath|chest pain|unconscious|heavy bleed|severe bleed|collapse|sesak nafas|sakit dada|tidak sedar/i.test(q);
    const known=/instruction|leaflet|lot|setup|guide|set up|box|contact|checklist|kit|panduan|kotak|versi|persediaan/i.test(q);
    const escalate=urgent||/irritat|rash|pain|bleed|swollen|swelling|discomfort|damaged|skin|sakit|gatal|ruam|kerengsaan|kulit|rosak/i.test(q)||!known;
    const decision=urgent?'urgent':refused?'refused':escalate?'review':'routine';
    const response=refused?'This demo cannot diagnose, recommend treatment, or change a dose. Ask your care team. A simulated review task has been added; no clinician has been contacted.':escalate?'The sample instructions route this report to nurse review. A simulated task has been added. No nurse or emergency service has been contacted.':'For this fictional kit, check that the lot on the box matches the instructions and keep your clinic contact information available. For your own care, follow the instructions from your care team.';
    const finalResponse=urgent?'This demonstration cannot assess urgent symptoms or contact help. Seek immediate assistance from your local emergency service or a qualified clinician.':response;
    result={action:'care',decision,status:decision,response:finalResponse,text:finalResponse,citations:[refused||escalate?'IFU-v2.1-4':'IFU-v2.1-1'],rule:refused?'diagnosis-and-treatment-boundary':escalate?'sample-ifu-review':'sample-ifu-routine',stored_input:false,mode:'walkthrough',lot:lotId};
    await append(state,'care',refused?'care.refused':escalate?'care.escalated':'care.answered',refused?'Care boundary applied':escalate?'Sample check-in routed to review':'Sample instructions returned',response,'Demo caregiver',{lot:lotId});
    if(refused||escalate) pending('care-'+state.events.length,'care','Review a sample caregiver check-in','A deterministic rule routed a synthetic check-in. No personal message was retained.');
    message=refused?'Diagnosis or treatment request refused.':escalate?'Simulated nurse review added. No one was contacted.':'Sample instruction returned with a source.';
  } else if(action==='verify') {
    result={action:'verify',status:'rejected',valid:false,draft:'This change will save 37% of energy.',findings:['Unverified number: 37%. No locked calculation supports this saving.'],coverage:0};
    state.verification={...state.verification,last_test:result};
    await append(state,'factory','verification.rejected','Unsupported saving rejected','The planted 37% saving is absent from the locked facts. The output was blocked.'); message='Verification blocked the invented 37% saving.';
  } else if(action==='analyze') {
    await append(state,'factory','analysis.completed','Synthetic shift re-analyzed','Deterministic metrics and the cited template were reviewed. No model call was made.'); message='Synthetic shift analyzed. A cited template is shown; AMD is not connected.';
  } else throw Error('Unknown demo action.');
  state.ledger_valid=await verifyDemo(state); save(state); return {state,message,result};
}
