from rapidfuzz import fuzz
import re
import logger

STOP_WORDS = {
    'the', 'and', 'a', 'an', 'in', 'on', 'at', 'to', 'of', 'it',
    'my', 'we', 'for', 'are', 'was', 'but', 'so', 'do', 'by', 'or',
    'if', 'as', 'be', 'he', 'she', 'its', 'our', 'get', 'got', 'had',
    'have', 'also', 'just', 'that', 'this', 'with', 'from', 'been',
    'completely', 'everyone', 'after', 'has', 'is', 'not', 'i', 'am',
    'me', 'up', 'out', 'when', 'can', 'keep', 'kept', 'will', 'would',
    'isn', 'isnt', 'dont', 'cant', 'wont', 'didnt', 'doesnt'
}

SINGLE_WORD_SKIP = {
    'update', 'install', 'mode', 'scan', 'check',
    'clean', 'repair', 'restore', 'run'
}

def normalize(text: str) -> str:
    return re.sub(r'[^\w\s]', ' ', text.lower()).strip()

def get_ngrams(words: list, n: int) -> list:
    return [' '.join(words[i:i+n]) for i in range(len(words) - n + 1)]

def _is_exact(word: str, terms: list) -> bool:
    wl = word.lower()
    return any(wl == t.lower() for t in terms)

def fuzzy_check(transcript: str, vocab_terms: list) -> list:
    clean = normalize(transcript)
    words = [
        w for w in clean.split()
        if w not in STOP_WORDS and len(w) >= 2
    ]

    single_terms = [t for t in vocab_terms if len(t.split()) == 1]
    multi_terms  = [t for t in vocab_terms if len(t.split()) > 1]

    flagged: dict = {}

    for word in words:
        if word in SINGLE_WORD_SKIP:
            continue
        if _is_exact(word, single_terms):
            continue  

        best_score, best_term = 0, None
        for term in single_terms:
            tl = term.lower()
            wl = word.lower()
            if wl == tl:
                continue
            if len(wl) >= 5 and len(tl) >= 5 and (wl in tl or tl in wl):
                continue
            score = fuzz.ratio(wl, tl)
            if score > best_score:
                best_score, best_term = score, term

        if best_score >= 80 and best_term:
            flagged[word] = {
                'original': word,
                'matched_term': best_term,
                'score': round(best_score, 1)
            }

    all_words = clean.split()
    for n in range(2, 5):
        for ngram in get_ngrams(all_words, n):
            if _is_exact(ngram, multi_terms):
                continue  # already correct

            best_score, best_term = 0, None
            for term in multi_terms:
                if abs(len(term.split()) - n) > 1:
                    continue
                # Use fuzz.ratio (length-sensitive Levenshtein) for multi-word.
                # token_set_ratio is a subset check and falsely flags
                # "not connecting" → "VPN not connecting" at 100%.
                # fuzz.ratio penalises length differences, so a 2-word ngram
                # will never score highly against a 3-word term.
                score = fuzz.ratio(ngram, term.lower())
                if score > best_score:
                    best_score, best_term = score, term

            if best_score >= 80 and best_term:
                # Guard 1: correction must not add words.
                if len(best_term.split()) > n:
                    continue

                # Guard 2: the words that DIFFER between ngram and term must be
                # phonetically similar to each other.  This blocks false positives
                # like "just not connecting" → "VPN not connecting" (shared tail
                # inflates the overall score even though "just" ≠ "vpn").
                ngram_words_set = set(ngram.split())
                term_words_set  = set(best_term.lower().split())
                # Do NOT filter stop words here — "just" is a stop word but
                # "just" vs "vpn" still needs to fail the similarity check.
                unique_ngram = list(ngram_words_set - term_words_set)
                unique_term  = list(term_words_set  - ngram_words_set)
                if unique_ngram and unique_term:
                    word_sim = max(
                        fuzz.ratio(nw, tw)
                        for nw in unique_ngram
                        for tw in unique_term
                    )
                    if word_sim < 60:
                        continue  # differing words are not phonetically alike → false positive

                if ngram not in flagged or best_score > flagged[ngram]['score']:
                    flagged[ngram] = {
                        'original': ngram,
                        'matched_term': best_term,
                        'score': round(best_score, 1)
                    }

    result = list(flagged.values())
    if result:
        logger.fuzzy_flagged(result)
    else:
        logger.fuzzy_none()
    return result
