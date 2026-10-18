"""Deterministic numeric locks, citation coverage, scoped lexical retrieval and guards."""
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


def verify(text, facts, passages):
    """Checks numeric membership and sentence citation coverage.

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
    allowed = [float(value) for value in facts.values() if isinstance(value, (int, float)) and not isinstance(value, bool)]
    for token in re.findall(r"(?<![A-Za-z\d])[+-]?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?", bare):
        value = float(token)
        if not any(abs(value - locked) <= max(0.0005, abs(locked) * 0.00001) for locked in allowed):
            findings.append({"rule": "unlocked_number", "message": f"{token} is not in the computed fact set; no supported savings claim may use it.", "value": token})
    # Split on sentence punctuation, not decimal points or citation-version dots.
    # Support both 'claim [citation].' and 'claim. [citation]' without treating
    # the post-punctuation citation as an independent sentence.
    citation_attached = re.sub(r"([.!?])\s*((?:\[[^\]]+\][ \t]*)+)", r" \2\1", text)
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+|\n+", citation_attached) if s.strip()]
    supported = sum(any(marker in ids | fact_ids for marker in re.findall(r"\[([^\]]+)\]", sentence)) for sentence in sentences)
    coverage = round(100 * supported / max(1, len(sentences)), 1)
    if coverage < 100:
        findings.append({"rule": "citation_coverage", "message": "Every sentence requires a resolvable source or locked-fact reference."})
    return {"status": "rejected" if findings else "passed", "coverage": coverage, "facts": [{"id": name, "value": value} for name, value in facts.items()], "citations": sorted(set(citations)), "findings": findings, "scope": "Numeric lock and citation coverage; not semantic entailment or clinical validation."}


def care_guard(question):
    text = question.lower()
    medical = r"diagnos|dosage|\bdose\b|medicat|treatment|\btreat\b|prescri|painkiller|antibiotic|\bmg\b|\bpill\b|how much.*take|how many.*take|double.*tablet|\bcure\b|what.*(?:wrong|disease|condition)|do i have|is (?:it|this).*(?:infect|allerg)|should.*(?:stop|start|take|increase|decrease)|can i.*(?:take|stop|increase|decrease)"
    medical += r"|\bdos\b|ubat|rawatan|merawat|sembuh|penyakit"
    urgent = r"breath|chest pain|unconscious|heavy bleed|severe bleed|collapse|sesak nafas|sakit dada|tidak sedar"
    review = r"irritat|discomfort|rash|damaged|broken|swollen|swelling|hurt|pain|kerengsaan|kulit|gatal|ruam|rosak"
    if re.search(urgent, text):
        return "urgent", "This demonstration cannot assess urgent symptoms or contact help. Seek immediate assistance from your local emergency service or a qualified clinician."
    if re.search(medical, text):
        return "refused", "I cannot diagnose a condition or recommend a medicine, dosage, or treatment. Ask your qualified care team. This fictional demo does not contact a nurse."
    if re.search(review, text):
        return "review", "This sample check-in requires nurse review under the fictional instructions. A simulated task has been opened; no clinic has been contacted. [IFU-v2.1-4]"
    if re.search(r"instruction|leaflet|lot|setup|set up|box|contact|checklist|kit|hello|panduan|kotak|versi|persediaan", text):
        return "routine", "Check that the lot on the box matches the supplied instructions and keep the leaflet and your clinic's contact information accessible. [IFU-v2.1-1]"
    return "out_of_scope", "The sample instructions do not support an answer to that question. Please ask your care team; no clinical answer is generated."
