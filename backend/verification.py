"""Deterministic numeric locks, citation coverage, scoped lexical retrieval, PII redaction, and guards."""
import math
import re
from collections import Counter


def retrieve(documents, query, pack, version=None, limit=3):
    """BM25 over authorized pack passages, filtered before scoring."""
    docs = [d for d in documents if d["pack"] == pack and (version is None or d["version"] == version)]
    terms = re.findall(r"\w+", query.lower())
    tokens = [re.findall(r"\w+", (d["title"] + " " + d["text"]).lower()) for d in docs]
    average = sum(map(len, tokens)) / max(1, len(tokens))
    ranked = []
    for doc, words in zip(docs, tokens):
        counts = Counter(words)
        score = 0.0
        for term in terms:
            frequency = sum(term in row for row in tokens)
            idf = math.log(1 + (len(docs) - frequency + 0.5) / (frequency + 0.5))
            tf = counts[term]
            score += idf * tf * 2.5 / (tf + 1.5 * (0.25 + 0.75 * len(words) / max(1, average)))
        ranked.append({**doc, "score": round(score, 4)})
    return sorted(ranked, key=lambda row: row["score"], reverse=True)[:limit]


def verify(text, facts, passages, known_identifiers=None):
    """Checks numeric membership, identifier locks, and sentence citation coverage.

    This is a deterministic structural check, not proof that free text semantically
    follows its citation. Hypotheses remain labelled and require human review.
    """
    findings = []
    ids = {p["id"] for p in passages}
    fact_ids = {f"FACT:{name}" for name in facts}
    citations = re.findall(r"\[([^\]]+)\]", text)
    unknown = sorted(set(citations) - ids - fact_ids)
    if unknown:
        findings.append({"rule": "unresolved_citation", "message": "Unknown citation: " + ", ".join(unknown)})
    bare = re.sub(r"\[[^\]]+\]", "", text)
    if known_identifiers is not None:
        allowed_ids = set(known_identifiers) | ids
        for ident in re.findall(r"\b(?:SOP-\d+(?:-v\d+\.\d+(?:-\d+(?:\.\d+)?)?)?|IFU-v\d+\.\d+(?:-\d+)?|PO-\d{4}-\d{4}|INV-\d{4}-\d{4}|GRN-\d{4}-\d{4}|ORD-\d{4}|2610-\d{2}|(?<=[Ll]ot\s)\d{4}-\d{2})\b", bare):
            if ident not in allowed_ids and not any(a.startswith(ident) for a in allowed_ids):
                findings.append({"rule": "unlocked_identifier", "message": f"Identifier {ident} is not present in the locked inputs.", "value": ident})
            # Remove identifier so its embedded digits don't duplicate as unlocked_number
            bare = bare.replace(ident, "")
    allowed = [float(value) for value in facts.values() if isinstance(value, (int, float)) and not isinstance(value, bool)]
    for token in re.findall(r"(?<![A-Za-z\d])[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?", bare):
        value = float(token)
        if not any(abs(value - locked) <= max(0.0005, abs(locked) * 0.00001) for locked in allowed):
            findings.append({"rule": "unlocked_number", "message": f"{token} is not in the computed fact set; no supported savings claim may use it.", "value": token})
    # Split on sentence punctuation, not decimal points or citation-version dots.
    # Support both 'claim [citation].' and 'claim. [citation]' without treating
    # the post-punctuation citation as an independent sentence.
    citation_attached = re.sub(r"([.!?])[ \t]*((?:\[[^\]]+\](?:[ \t]+(?=\[))?)+)", r" \2\1", text)
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", citation_attached) if s.strip()]
    supported = sum(any(marker in ids | fact_ids for marker in re.findall(r"\[([^\]]+)\]", sentence)) for sentence in sentences)
    coverage = round(100 * supported / max(1, len(sentences)), 1)
    if coverage < 100:
        findings.append({"rule": "citation_coverage", "message": "Every sentence requires a resolvable source or locked-fact reference."})
    return {
        "status": "rejected" if findings else "passed",
        "coverage": coverage,
        "facts": [{"id": name, "value": value} for name, value in facts.items()],
        "citations": sorted(set(citations)),
        "findings": findings,
        "scope": "Numeric lock and citation coverage; not semantic entailment or clinical validation.",
    }


def redact_pii(text):
    """Deterministic PII redaction for emails, phone numbers, IDs, addresses, and named persons."""
    if not isinstance(text, str):
        return {"redacted_text": "", "entities": {"EMAIL": 0, "PHONE": 0, "ID": 0, "ADDRESS": 0, "PERSON": 0}, "total_redactions": 0}
    counts = {"EMAIL": 0, "PHONE": 0, "ID": 0, "ADDRESS": 0, "PERSON": 0}
    redacted = text

    def _sub(pattern, placeholder, key, flags=0):
        nonlocal redacted
        redacted, n = re.subn(pattern, placeholder, redacted, flags=flags)
        counts[key] += n

    _sub(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b", "[REDACTED_EMAIL]", "EMAIL")
    _sub(r"\b\d{6}-\d{2}-\d{4}\b", "[REDACTED_ID]", "ID")
    _sub(r"(?:(?:\+|00)\d{1,3}[\s.-]?)?(?:\(?\d{2,4}\)?[\s.-]?)\d{3,4}[\s.-]?\d{3,4}\b", "[REDACTED_PHONE]", "PHONE")
    _sub(r"\b\d{1,5}\s+(?:Jalan|Lorong|Street|St\.|Road|Rd\.|Via|Viale|Piazza)\s+[A-Za-z0-9\s]{2,25}\b", "[REDACTED_ADDRESS]", "ADDRESS", flags=re.IGNORECASE)
    _sub(
        r"\b((?:mother|father|patient|sister|brother|wife|husband|daughter|son|puan|encik|cik|mr|mrs|ms|dr|signora|signor)\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)(?='s\b|\b)",
        r"\1[REDACTED_PERSON]",
        "PERSON",
        flags=re.IGNORECASE,
    )
    _sub(
        r"\b((?:my\s+name\s+is|i\s+am|nama\s+saya|mi\s+chiamo)\s+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\b",
        r"\1[REDACTED_PERSON]",
        "PERSON",
        flags=re.IGNORECASE,
    )
    return {
        "redacted_text": redacted,
        "entities": counts,
        "total_redactions": sum(counts.values()),
    }


def care_guard(question):
    """Deterministic multilingual care guard (English, Bahasa Melayu, Italiano)."""
    text = question.lower()
    medical = (
        r"diagnos|dosage|\bdose\b|medicat|treatment|\btreat\b|prescri|painkiller|antibiotic|\bmg\b|\bpill\b|pills\b"
        r"|how much.*take|how many.*take|double.*tablet|\bcure\b|what.*(?:wrong|disease|condition)|do i have"
        r"|is (?:it|this).*(?:infect|allerg)|should.*(?:stop|start|take|increase|decrease)|can i.*(?:take|stop|increase|decrease)"
        r"|\bdos\b|ubat|rawatan|merawat|sembuh|penyakit"
        r"|dosaggio|farmac|medicin|curare|guarire|infezione|malattia|prescrivere|compresse"
    )
    urgent = (
        r"breath|chest pain|unconscious|heavy bleed|severe bleed|collapse"
        r"|sesak nafas|sakit dada|tidak sedar|pendarahan"
        r"|respirare|dolore al petto|incosciente|emorragia"
    )
    review = (
        r"irritat|discomfort|rash|damaged|broken|swollen|swelling|hurt|pain"
        r"|kerengsaan|kulit|gatal|ruam|rosak|bengkak|sakit"
        r"|irritazione|eruzione|pelle|gonfiore|danneggiat|rotto|dolore"
    )
    routine = (
        r"instruction|leaflet|lot|setup|set up|box|contact|checklist|kit|hello|guide"
        r"|panduan|kotak|versi|persediaan|risalah"
        r"|istruzioni|guida|scatola|versione|configurazione|contatto|ricarica"
    )
    if re.search(urgent, text):
        return "urgent", "This demonstration cannot assess urgent symptoms or contact help. Seek immediate assistance from your local emergency service or a qualified clinician."
    if re.search(medical, text):
        return "refused", "I cannot diagnose a condition or recommend a medicine, dosage, or treatment. Ask your qualified care team. This fictional demo does not contact a nurse."
    if re.search(review, text):
        return "review", "This sample check-in requires nurse review under the fictional instructions. A simulated task has been opened; no clinic has been contacted. [IFU-v2.1-4]"
    if re.search(routine, text):
        return "routine", "Check that the lot on the box matches the supplied instructions and keep the leaflet and your clinic's contact information accessible. [IFU-v2.1-1]"
    return "out_of_scope", "The sample instructions do not support an answer to that question. Please ask your care team; no clinical answer is generated."


def care_agreement(question):
    """Independent dual-extractor agreement indicator (Proposal Pack 5 requirement).

    Compares Extractor A (deterministic boundary pattern matcher) with Extractor B
    (IFU section lexical overlap matcher). Explicitly labelled as an agreement measure,
    never a clinical probability.
    """
    status_a, _ = care_guard(question)
    q = question.lower()
    ifu_sec1_terms = {"lot", "box", "instruction", "instructions", "leaflet", "contact", "setup", "guide", "kit", "checklist", "panduan", "kotak", "versi", "persediaan", "risalah", "istruzioni", "guida", "scatola", "versione", "ricarica"}
    ifu_sec4_terms = {"irritation", "irritating", "irritates", "discomfort", "rash", "damaged", "broken", "strap", "skin", "swollen", "pain", "kerengsaan", "kulit", "gatal", "ruam", "rosak", "irritazione", "pelle", "danneggiato"}
    medical_terms = {"dose", "dosage", "diagnose", "diagnosis", "medication", "medicine", "treatment", "treat", "cure", "pill", "mg", "antibiotic", "painkiller", "dos", "ubat", "rawatan", "penyakit", "dosaggio", "farmaco", "curare", "infezione"}
    urgent_terms = {"breath", "breathing", "chest", "unconscious", "bleed", "bleeding", "collapse", "nafas", "dada", "respirare", "petto"}
    words = set(re.findall(r"\w+", q))
    if words & urgent_terms or "chest pain" in q or "sesak nafas" in q:
        status_b = "urgent"
    elif words & medical_terms or any(k in q for k in ("diagnos", "dosage", "medicat", "prescri", "double", "how much")):
        status_b = "refused"
    elif words & ifu_sec4_terms or any(k in q for k in ("irritat", "swoll", "kerengsaan", "irritazione")):
        status_b = "review"
    elif words & ifu_sec1_terms:
        status_b = "routine"
    else:
        status_b = "out_of_scope"
    agreed = status_a == status_b
    score = 1.0 if agreed else 0.5
    return {
        "extractor_a": status_a,
        "extractor_b": status_b,
        "agreed": agreed,
        "score": score,
        "agreement_Count": "2/2" if agreed else "1/2",
        "label": "2/2 independent extractors agree (1.00 agreement measure — not a clinical probability)" if agreed else "1/2 extractors agree (0.50 agreement measure — routed conservatively to human review)",
    }


def experience_quality_gate(sentence=""):
    """Deterministic style-bible quality gate blocking prohibited clinical/health claims in EN/MS/IT."""
    text = str(sentence or "").strip()
    forbidden_pattern = (
        r"diagnos|treat(?:s|ment)?|cur(?:e|es)|prevent(?:s|ion)?|medical[ -]grade|clinically[ -]proven"
        r"|reduce[s]? pain|heal(?:s|ing)?|merawat|menyembuh|mencegah|mengesan penyakit|mengurangkan kesakitan"
        r"|guarire|guarigione|terapeutic|curare|diagnosticare|clinicamente provato|riduce il dolore"
    )
    match = re.search(forbidden_pattern, text, flags=re.IGNORECASE)
    passed = match is None
    return {
        "passed": passed,
        "blocked_term": match.group(0) if match else None,
        "style_bible": "BRAND-v1.0-2",
        "message": "Template and optional sentence pass the deterministic style-bible phrase checks." if passed else f"Blocked by style bible [BRAND-v1.0-2]: prohibited health/clinical claim '{match.group(0)}' detected.",
    }
