# /features/keyword_extractor.py
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import re
import streamlit as st

# Track if advanced features are available
ADVANCED_KEYWORDS = True

# Lazy-loaded models - cached to prevent reinitialization
_keybert_model = None
_sentence_model = None


@st.cache_resource
def _get_keybert_model():
    """Lazy load KeyBERT model with caching to prevent Torch reinitialization"""
    global _keybert_model, _sentence_model
    
    if _keybert_model is not None:
        return _keybert_model, True
    
    try:
        # Import only when needed
        from keybert import KeyBERT
        from sentence_transformers import SentenceTransformer
        
        _sentence_model = SentenceTransformer('all-MiniLM-L6-v2')
        _keybert_model = KeyBERT(model=_sentence_model)
        return _keybert_model, True
    except ImportError:
        return None, False
    except Exception as e:
        st.warning(f"Could not load KeyBERT models: {e}. Using basic extraction.")
        return None, False


class KeywordExtractor:
    def __init__(self):
        """Initialize keyword extractor - models are lazy-loaded when needed"""
        self.use_advanced = True  # Will try advanced first
        self._model_loaded = False

    def _get_model(self):
        """Get the KeyBERT model, loading it lazily if needed"""
        if not self._model_loaded:
            model, success = _get_keybert_model()
            self.use_advanced = success
            self._model_loaded = True
            return model
        return _keybert_model

    def extract_from_url(self, url: str, num_keywords: int = 20) -> Dict[str, List[str]]:
        try:
            response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            for element in soup(['script', 'style', 'meta', 'link']):
                element.decompose()
            
            title = soup.title.string if soup.title else ''
            h1s = ' '.join([h.get_text() for h in soup.find_all('h1')])
            paragraphs = ' '.join([p.get_text() for p in soup.find_all('p')[:10]])
            full_text = ' '.join([title] * 3 + [h1s] * 2 + [paragraphs])
            full_text = re.sub(r'\s+', ' ', full_text).strip()

            if not full_text or len(full_text) < 50:
                return {'exact': [], 'phrase': [], 'broad': []}

            # Try to get model (lazy load)
            kw_model = self._get_model()
            
            if kw_model and self.use_advanced:
                keywords = kw_model.extract_keywords(
                    full_text, keyphrase_ngram_range=(1, 3), stop_words='english',
                    use_mmr=True, diversity=0.5, top_n=num_keywords
                )
                exact = [kw for kw, score in keywords if len(kw.split()) <= 2 and score > 0.5]
                phrase = [kw for kw, score in keywords if len(kw.split()) >= 2 and score > 0.4]
                broad = [kw for kw, score in keywords if kw not in exact and kw not in phrase]
                return {'exact': exact, 'phrase': phrase, 'broad': broad}
            else:
                # Basic fallback
                from collections import Counter
                words = re.findall(r'\b[a-z]{3,15}\b', full_text.lower())
                common_words = [w for w, c in Counter(words).most_common(num_keywords)]
                return {'exact': common_words[:5], 'phrase': [], 'broad': common_words[5:]}
        except Exception as e:
            st.error(f"Error extracting keywords: {e}")
            return {'exact': [], 'phrase': [], 'broad': []}

    def extract_from_text(self, text: str, num_keywords: int = 20) -> Dict[str, List[str]]:
        """Extract keywords from plain text using the same logic as URL extraction."""
        if not text or len(text) < 20:
            return {'exact': [], 'phrase': [], 'broad': []}

        # Clean and prepare text
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Try to get model (lazy load)
        kw_model = self._get_model()
        
        if kw_model and self.use_advanced:
            keywords = kw_model.extract_keywords(
                text, keyphrase_ngram_range=(1, 3), stop_words='english',
                use_mmr=True, diversity=0.5, top_n=num_keywords
            )
            exact = [kw for kw, score in keywords if len(kw.split()) <= 2 and score > 0.5]
            phrase = [kw for kw, score in keywords if len(kw.split()) >= 2 and score > 0.4]
            broad = [kw for kw, score in keywords if kw not in exact and kw not in phrase]
            return {'exact': exact, 'phrase': phrase, 'broad': broad}
        else:
            # Basic fallback
            from collections import Counter
            words = re.findall(r'\b[a-z]{3,15}\b', text.lower())
            common_words = [w for w, c in Counter(words).most_common(num_keywords)]
            return {'exact': common_words[:5], 'phrase': [], 'broad': common_words[5:]}

    def generate_variations(self, seed_keywords: str, num_variations: int = 15) -> Dict[str, List[str]]:
        """Generate keyword variations from seed keywords."""
        # Simple variation generation
        variations = []
        seed_list = [kw.strip() for kw in seed_keywords.split(',') if kw.strip()]
        
        for seed in seed_list:
            # Add basic variations
            variations.extend([
                f"buy {seed}",
                f"{seed} for sale", 
                f"best {seed}",
                f"cheap {seed}",
                f"{seed} reviews",
                f"how to {seed}",
                f"what is {seed}",
                f"{seed} guide",
                f"{seed} tips",
                f"{seed} tutorial"
            ])
        
        # Remove duplicates and limit
        variations = list(set(variations))[:num_variations]
        
        # Categorize by match type
        exact = [v for v in variations if len(v.split()) <= 2][:5]
        phrase = [v for v in variations if len(v.split()) >= 3][:5]
        broad = [v for v in variations if v not in exact and v not in phrase][:5]
        
        return {'exact': exact, 'phrase': phrase, 'broad': broad}

    def format_for_campaign(self, keywords_dict: Dict[str, List[str]]) -> str:
        lines = []
        for kw in keywords_dict.get('exact', []): lines.append(f"{kw}, exact")
        for kw in keywords_dict.get('phrase', []): lines.append(f"{kw}, phrase")
        for kw in keywords_dict.get('broad', []): lines.append(f"{kw}, broad")
        return '\n'.join(lines)
