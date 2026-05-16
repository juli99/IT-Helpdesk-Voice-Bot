from rapidfuzz import fuzz
import re

STOP_WORDS = {
    'the', 'and', 'a', 'an', 'in', 'on', 'at', 'to', 'of', 'it',
    'my', 'we', 'for', 'are', 'was', 'but', 'so', 'do', 'by', 'or',
    'if', 'as', 'be', 'he', 'she', 'its', 'our', 'get', 'got', 'had',
    'have', 'also', 'just', 'that', 'this', 'with', 'from', 'been',
    'completely', 'everyone', 'after', 'has', 'is', 'not', 'i', 'am',
    'me', 'up', 'out', 'when', 'can', 'keep', 'kept', 'will', 'would', 'isn', 'isnt', 'dont', 'cant', 'wont', 'didnt', 'doesnt'
}

GENERIC_WORDS = {
    'update', 'install', 'server', 'driver', 'boot',
    'screen', 'mode', 'error', 'scan', 'reset',
    'connect', 'access', 'share', 'lock', 'block',
    'check', 'clean', 'repair', 'restore', 'run', 'drive'
}

def normalize(text):
    return re.sub(r'[^\w\s]', ' ', text.lower()).strip()

def get_ngrams(words, n):
    return [' '.join(words[i:i+n]) for i in range(len(words) - n + 1)]

def fuzzy_check(transcript: str, vocab_terms: list) -> list:
    clean = normalize(transcript)
    words = [w for w in clean.split() if w not in STOP_WORDS and w not in GENERIC_WORDS and len(w) >= 2]

    single_terms = [t for t in vocab_terms if len(t.split()) == 1]
    multi_terms  = [t for t in vocab_terms if len(t.split()) > 1]

    flagged = {}

    # --- single word matching ---
    for word in words:
        if word.lower() in [t.lower() for t in single_terms]:
            continue  # exact match, correctly spoken
        best_score = 0
        best_term = None
        for term in single_terms:
            # skip substring matches ("install" vs "uninstall", "update" vs "gpupdate")
            if word.lower() in term.lower() or term.lower() in word.lower():
                continue
            score = fuzz.ratio(word, term.lower())
            if score > best_score:
                best_score = score
                best_term = term
        if best_score >= 80 and best_term:
            flagged[word] = {
                'original': word,
                'matched_term': best_term,
                'score': round(best_score, 1)
            }

    # --- multi-word phrase matching (ngrams up to 4 words) ---
    all_words = clean.split()
    for n in range(2, 5):
        for ngram in get_ngrams(all_words, n):
            if ngram.lower() in [t.lower() for t in multi_terms]:
                continue  # exact match, correctly spoken
            best_score = 0
            best_term = None
            for term in multi_terms:
                if abs(len(term.split()) - n) > 1:
                    continue
                # skip if all ngram words already exist in the term (e.g. "system is" vs "POS system")
                if all(w in term.lower().split() for w in ngram.split()):
                    continue
                score = fuzz.ratio(ngram, term.lower())  # order-sensitive, replaces token_sort_ratio
                if score > best_score:
                    best_score = score
                    best_term = term
            if best_score >= 82 and best_term:
                if ngram not in flagged or best_score > flagged[ngram]['score']:
                    flagged[ngram] = {
                        'original': ngram,
                        'matched_term': best_term,
                        'score': round(best_score, 1)
                    }

    return list(flagged.values())