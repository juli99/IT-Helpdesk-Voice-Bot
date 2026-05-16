import json
from fuzzy_correction import fuzzy_check
from llm_correction import llm_correct

def load_vocab(path='it_vocab.json') -> list:
    with open(path, 'r') as f:
        data = json.load(f)
        return data['terms']

def get_relevant_vocab(flagged: list, vocab_terms: list, max_terms: int = 25) -> list:
    if not flagged:
        return []
    # always include the suggested matched terms
    matched = {f['matched_term'].lower() for f in flagged}
    # also include vocab terms that share a word with any flagged original
    flagged_words = {w for f in flagged for w in f['original'].lower().split()}
    relevant = []
    for term in vocab_terms:
        term_words = set(term.lower().split())
        if term.lower() in matched or term_words & flagged_words:
            relevant.append(term)
    # cap at max_terms to control token usage
    return relevant[:max_terms]

def correction(transcript: str) -> dict:
    vocab_terms = load_vocab()
    flagged = fuzzy_check(transcript, vocab_terms)
    flagged_clean = [{'original': f['original'], 'suggested': f['matched_term']} for f in flagged]

    relevant_vocab = get_relevant_vocab(flagged, vocab_terms)
    result = llm_correct(transcript, flagged_clean, relevant_vocab)

    flagged_originals = {f['original'].lower() for f in flagged}
    verified_corrections = [
        c for c in result.get('corrections', [])
        if c['original'].lower() in flagged_originals
    ]

    verified_corrections.sort(key=lambda c: len(c['original']), reverse=True)

    corrected = transcript
    applied = []
    for c in verified_corrections:
        if c['original'] in corrected:
            corrected = corrected.replace(c['original'], c['corrected'])
            applied.append(c)

    return {
        'corrected_transcript': corrected,
        'confidence': result.get('confidence', 'low'),
        'corrections': applied
    }