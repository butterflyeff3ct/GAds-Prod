# /core/matching.py
from typing import List, Set, Dict, Tuple, Optional
import re

class MatchEngine:
    """
    Enhanced keyword matching engine with query expansion and intent detection.
    Models how Google Ads matches search queries to keywords.
    """
    
    def __init__(self):
        # Match type effectiveness (how much search volume each match type captures)
        self.match_capture = {
            "exact": 0.95,
            "phrase": 0.70,
            "broad": 0.40
        }
        
        # Common query variations and synonyms for expansion
        self.synonyms = {
            'buy': ['purchase', 'order', 'get', 'shop'],
            'cheap': ['affordable', 'discount', 'budget', 'inexpensive'],
            'best': ['top', 'great', 'excellent', 'finest'],
            'phone': ['smartphone', 'mobile', 'cell phone', 'device'],
            'shoes': ['footwear', 'sneakers', 'boots'],
            'laptop': ['notebook', 'computer', 'pc'],
            'car': ['vehicle', 'auto', 'automobile'],
        }
        
        # Common query modifiers
        self.modifiers = {
            'question': ['how', 'what', 'where', 'when', 'why', 'who'],
            'intent': ['buy', 'purchase', 'order', 'find', 'compare'],
            'qualifier': ['best', 'cheap', 'affordable', 'top', 'good'],
            'location': ['near me', 'nearby', 'local', 'in'],
            'time': ['today', 'now', 'tonight', 'this week']
        }

    def _normalize(self, text: str) -> str:
        """Normalize text for matching."""
        text = text.lower()
        text = re.sub(r'[^\w\s]', ' ', text)
        return ' '.join(text.split())

    def _expand_query(self, query: str) -> Set[str]:
        """
        Expand query with synonyms and variations.
        This simulates how Google Ads understands query intent.
        """
        normalized = self._normalize(query)
        words = normalized.split()
        
        expansions = {normalized}  # Start with original
        
        # Add synonym variations
        for word in words:
            if word in self.synonyms:
                for synonym in self.synonyms[word]:
                    # Replace word with synonym
                    new_query = normalized.replace(word, synonym)
                    expansions.add(new_query)
        
        # Add variations with/without modifiers
        for modifier_type, modifier_words in self.modifiers.items():
            for modifier in modifier_words:
                if modifier in words:
                    # Try removing modifier
                    query_without = ' '.join([w for w in words if w != modifier])
                    if query_without:
                        expansions.add(query_without)
        
        return expansions

    def match_type_score(self, keyword: str, query: str, match_type: str) -> float:
        """
        Calculate match score between keyword and query for given match type.
        Returns 0.0 (no match) to 1.0 (perfect match).
        """
        keyword_clean = self._normalize(keyword)
        query_clean = self._normalize(query)
        
        # Get query expansions for broad matching
        if match_type == "broad":
            query_variants = self._expand_query(query_clean)
        else:
            query_variants = {query_clean}

        if match_type == "exact":
            # Exact match: keyword must exactly match query
            if keyword_clean == query_clean:
                return self.match_capture["exact"]
            return 0.0
            
        elif match_type == "phrase":
            # Phrase match: keyword must appear as a phrase in query
            for query_variant in query_variants:
                if keyword_clean in query_variant:
                    # Calculate strength based on how much of query is the keyword
                    keyword_words = len(keyword_clean.split())
                    query_words = len(query_variant.split())
                    coverage = keyword_words / query_words
                    return self.match_capture["phrase"] * coverage
            return 0.0
            
        elif match_type == "broad":
            # Broad match: all keyword words must appear in query (any order)
            kw_words = set(keyword_clean.split())
            
            best_score = 0.0
            for query_variant in query_variants:
                q_words = set(query_variant.split())
                
                # Check if all keyword words are present
                if kw_words.issubset(q_words):
                    # Calculate match strength
                    word_overlap = len(kw_words.intersection(q_words))
                    total_words = len(kw_words)
                    
                    # Perfect match if all words present
                    if word_overlap == total_words:
                        match_strength = self.match_capture["broad"]
                        
                        # Bonus for word order preservation
                        if self._check_word_order(keyword_clean, query_variant):
                            match_strength *= 1.2
                        
                        best_score = max(best_score, match_strength)
                    else:
                        # Partial match
                        partial_strength = self.match_capture["broad"] * (word_overlap / total_words)
                        best_score = max(best_score, partial_strength)
            
            return min(1.0, best_score)  # Cap at 1.0
        
        return 0.0

    def _check_word_order(self, keyword: str, query: str) -> bool:
        """Check if keyword words appear in same order in query."""
        kw_words = keyword.split()
        query_words = query.split()
        
        kw_idx = 0
        for q_word in query_words:
            if kw_idx < len(kw_words) and q_word == kw_words[kw_idx]:
                kw_idx += 1
        
        return kw_idx == len(kw_words)

    def is_negative_hit(self, query: str, negative_keywords: List[str]) -> bool:
        """
        Check if query matches any negative keywords.
        Negative keywords prevent ads from showing.
        """
        query_clean = self._normalize(query)
        q_words = set(query_clean.split())

        for neg_kw in negative_keywords:
            neg_kw = neg_kw.strip()
            if not neg_kw:
                continue
            
            # Phrase Match Negative: "keyword"
            if neg_kw.startswith('"') and neg_kw.endswith('"'):
                neg_phrase = self._normalize(neg_kw.strip('"'))
                if neg_phrase in query_clean:
                    return True
                    
            # Exact Match Negative: [keyword]
            elif neg_kw.startswith('[') and neg_kw.endswith(']'):
                neg_exact = self._normalize(neg_kw.strip('[]'))
                if neg_exact == query_clean:
                    return True
                    
            # Broad Match Negative: keyword (default)
            else:
                neg_words = set(self._normalize(neg_kw).split())
                if neg_words.issubset(q_words):
                    return True
        
        return False

    def find_best_match(self, query: str, keywords: List[Dict]) -> Tuple[Optional[Dict], float]:
        """
        Find the best matching keyword for a query.
        Returns (keyword_dict, match_score) or (None, 0.0).
        """
        best_keyword = None
        best_score = 0.0
        
        for kw_dict in keywords:
            keyword_text = kw_dict.get('text', '')
            match_type = kw_dict.get('match_type', 'broad')
            
            score = self.match_type_score(keyword_text, query, match_type)
            
            # Prefer exact match types when scores are close
            if score > best_score:
                best_score = score
                best_keyword = kw_dict
            elif score == best_score and best_keyword:
                # Tie-breaker: prefer more specific match types
                match_type_priority = {'exact': 3, 'phrase': 2, 'broad': 1}
                current_priority = match_type_priority.get(match_type, 0)
                best_priority = match_type_priority.get(best_keyword.get('match_type', 'broad'), 0)
                
                if current_priority > best_priority:
                    best_keyword = kw_dict
        
        return best_keyword, best_score

    def generate_search_queries(self, keyword: str, match_type: str, num_queries: int = 10) -> List[str]:
        """
        Generate realistic search queries that would match this keyword.
        Educational function showing what queries trigger your keywords.
        """
        keyword_clean = self._normalize(keyword)
        words = keyword_clean.split()
        
        queries = [keyword_clean]  # Start with exact keyword
        
        if match_type in ["phrase", "broad"]:
            # Add queries with modifiers before
            for qualifier in self.modifiers['qualifier'][:3]:
                queries.append(f"{qualifier} {keyword_clean}")
            
            # Add queries with modifiers after
            for intent in self.modifiers['intent'][:2]:
                queries.append(f"{intent} {keyword_clean}")
            
            # Add location queries
            queries.append(f"{keyword_clean} near me")
            queries.append(f"{keyword_clean} online")
        
        if match_type == "broad":
            # Add reordered variations
            if len(words) > 1:
                queries.append(f"{words[-1]} {' '.join(words[:-1])}")
            
            # Add queries with additional words
            queries.append(f"how to {keyword_clean}")
            queries.append(f"where to {keyword_clean}")
            
            # Add synonym variations
            for word in words:
                if word in self.synonyms and self.synonyms[word]:
                    synonym = self.synonyms[word][0]
                    new_query = keyword_clean.replace(word, synonym)
                    queries.append(new_query)
        
        # Remove duplicates and limit
        unique_queries = list(dict.fromkeys(queries))
        return unique_queries[:num_queries]

    def explain_match(self, keyword: str, query: str, match_type: str) -> Dict:
        """
        Explain why/how a keyword matches (or doesn't match) a query.
        Educational function for understanding match types.
        """
        keyword_clean = self._normalize(keyword)
        query_clean = self._normalize(query)
        score = self.match_type_score(keyword, query, match_type)
        
        kw_words = set(keyword_clean.split())
        q_words = set(query_clean.split())
        
        explanation = {
            'keyword': keyword,
            'query': query,
            'match_type': match_type,
            'score': round(score, 3),
            'matches': score > 0,
            'keyword_words': list(kw_words),
            'query_words': list(q_words),
            'matching_words': list(kw_words.intersection(q_words)),
            'missing_words': list(kw_words - q_words),
            'extra_words': list(q_words - kw_words)
        }
        
        # Add match-type specific explanation
        if match_type == "exact":
            explanation['reason'] = "Exact match requires query to exactly match keyword"
            explanation['requirement_met'] = keyword_clean == query_clean
        elif match_type == "phrase":
            explanation['reason'] = "Phrase match requires keyword to appear as phrase in query"
            explanation['requirement_met'] = keyword_clean in query_clean
        else:  # broad
            explanation['reason'] = "Broad match requires all keyword words to appear in query (any order)"
            explanation['requirement_met'] = kw_words.issubset(q_words)
        
        return explanation
