"""Three distinct methods over the same Day06 B corpus; exact metadata filters."""
from starter.baseline import TfidfIndex


class LexicalRetriever:
    def __init__(self, chunks):
        self.index = TfidfIndex(chunks)

    def search(self, query, *, filters=None, top_k=3):
        rows = self.index.search(query, top_k=len(self.index.chunks))
        return [r for r in rows if all(r['metadata'].get(k) == v for k, v in (filters or {}).items())][:top_k]


class DenseRetriever:
    def __init__(self, store, embedder, strategy='B'):
        self.store, self.embedder, self.strategy = store, embedder, strategy

    def search(self, query, *, filters=None, top_k=3):
        rows = self.store.search(self.strategy, self.embedder.embed_query(query), top_k, filters)
        return [{'id': r['chunk_id'], 'source_id': r['document_id'], 'source': r['source'],
                 'page': r['page'], 'text': r['text'], 'metadata': r['metadata'],
                 'score': r['score'], 'strategy': 'dense'} for r in rows]


class HybridRetriever:
    def __init__(self, dense, lexical, candidates=20, rrf_k=60):
        self.dense, self.lexical = dense, lexical
        self.candidates, self.rrf_k = candidates, rrf_k

    def search(self, query, *, filters=None, top_k=3):
        scores, rows, ranks = {}, {}, {}
        for name, retriever in [('dense', self.dense), ('tfidf', self.lexical)]:
            for rank, row in enumerate(retriever.search(query, filters=filters, top_k=max(top_k, self.candidates)), 1):
                cid = row['id']
                scores[cid] = scores.get(cid, 0) + 1 / (self.rrf_k + rank)
                rows[cid] = row
                ranks.setdefault(cid, {})[name] = rank
        return [{**rows[cid], 'score': scores[cid], 'strategy': 'hybrid', 'component_ranks': ranks[cid]}
                for cid in sorted(rows, key=lambda cid: (-scores[cid], cid))[:top_k]]


def build_retriever(method, chunks, store=None, embedder=None, strategy='B', candidates=20):
    lexical = LexicalRetriever(chunks)
    if method == 'tfidf':
        return lexical
    if method not in {'dense', 'hybrid'}:
        raise ValueError(f'Unknown retrieval method: {method}')
    if store is None or embedder is None:
        raise RuntimeError('Dense/hybrid require real embeddings and pgvector; no mock fallback')
    dense = DenseRetriever(store, embedder, strategy)
    return dense if method == 'dense' else HybridRetriever(dense, lexical, candidates)
