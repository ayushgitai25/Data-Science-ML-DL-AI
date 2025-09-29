# Hybrid Search

Hybrid search combines **semantic (dense vector)** search and **syntactic (sparse vector)** search to balance meaning and exact keyword matching.

---

## Concepts

- **Dense / Semantic Search**  
  - Embedding-based (e.g. BERT, Sentence Transformers)  
  - Captures semantic similarity  
  - Uses ANN / cosine similarity  

- **Sparse / Keyword Search**  
  - One-Hot Encoding (OHE), Bag-of-Words (BoW), TF-IDF, binary 0/1  
  - Captures exact tokens and term frequency  
  - Stored in inverted index / sparse matrix  

- **Hybrid Fusion**  
  - Combine both with weighted scoring or rank fusion  
  - `score = α * dense + (1 - α) * sparse`  

---

## Workflow

1. Preprocess documents  
2. Build **dense index** (embeddings) + **sparse index** (keywords)  
3. Query → generate both dense & sparse vectors  
4. Retrieve top-k from both  
5. Fuse results → return ranked list  

---

## Example (Python)

```python
def hybrid_search(query, top_k=10, alpha=0.5):
    dense_results = dense_index.search(embed(query), top_k)
    sparse_results = sparse_index.search(vectorize(query), top_k)
    return fuse(dense_results, sparse_results, alpha)


## How It Works

### Indexing
- Documents stored in **two forms**:
  1. **Sparse matrix** → OHE, BoW, TF-IDF, binary 0/1  
  2. **Dense vectors** → semantic embeddings  

### Query Processing
1. User query sent to both databases.  
2. Sparse index → returns exact keyword matches (`top_k1`).  
3. Dense index → returns semantic matches (`top_k2`).  
4. Results are merged using **Reciprocal Rank Fusion (RRF)**.

---

## Reciprocal Rank Fusion (RRF)

Each document’s score is calculated as:

\[
\text{Score(doc)} = \sum \frac{1}{c + R_d}
\]

- \(R_d\) = rank of the document in that search result  
- \(c\) = constant (usually between 1–60, e.g. 60)  
- If a document is present in **both lists**, add up its scores.  
- Higher sum = higher rank.  
- If scores are equal, tie-breaking (e.g. favor sparse match) decides.

---

### Example

Let \(c = 60\).

**Sparse search results (top_k1):**
1. docA (rank=1)  
2. docB (rank=2)  
3. docC (rank=3)  

**Dense search results (top_k2):**
1. docB (rank=1)  
2. docD (rank=2)  
3. docA (rank=3)  

**RRF Scoring:**
- docA: \(1/(60+1) + 1/(60+3) = 1/61 + 1/63 ≈ 0.0326\)  
- docB: \(1/(60+2) + 1/(60+1) = 1/62 + 1/61 ≈ 0.0328\)  
- docC: \(1/(60+3) = 1/63 ≈ 0.0159\)  
- docD: \(1/(60+2) = 1/62 ≈ 0.0161\)  

**Final Ranking (highest score first):**
1. docB  
2. docA  
3. docD  
4. docC


## Weighted Hybrid Fusion

Sometimes we want to favor one method more (e.g. exact keyword matches > semantic matches).  
We introduce **weights** for sparse vs dense scores.

### Formula

\[
\text{FinalScore(doc)} = w_s \cdot \text{Score}_s(doc) \;+\; w_d \cdot \text{Score}_d(doc)
\]

- \(w_s\) = weight for **sparse score**  
- \(w_d\) = weight for **dense score**  
- \(w_s + w_d = 1\) (usually normalized)

### Applied in RRF

Each score component becomes:

\[
\text{Score}_s(doc) = \frac{w_s}{c + R_{sparse}}
\]

\[
\text{Score}_d(doc) = \frac{w_d}{c + R_{dense}}
\]

Then **sum them up** across both rankings.

---

### Example (c = 60, w_s = 0.7, w_d = 0.3)

**Sparse results:**  
1. docA (rank=1)  
2. docB (rank=2)  

**Dense results:**  
1. docB (rank=1)  
2. docA (rank=2)  

**Scores:**  
- docA = \(0.7/(60+1) + 0.3/(60+2)\) = 0.01148 + 0.00484 = **0.0163**  
- docB = \(0.7/(60+2) + 0.3/(60+1)\) = 0.01129 + 0.00492 = **0.0162**

**Final ranking:** docA > docB (since docA had more sparse weight)

---

👉 By tuning \(w_s\) and \(w_d\), you control whether the system prioritizes **exact keyword matches** (sparse) or **semantic similarity** (dense).


## Hybrid + Graph Database Search

In addition to **sparse (keyword)** and **dense (semantic)** search, a **Graph Database** introduces a third search mode: **Knowledge Graph Search**.

---

### Supported Searches

1. **Keyword Search (Sparse)**
   - Uses inverted index / sparse matrix (OHE, BoW, TF-IDF, binary 0/1).
   - Best for exact term matching, IDs, rare tokens.

2. **Semantic Search (Dense)**
   - Embedding vectors stored in vector DB or graph nodes.
   - Finds semantically similar entities/documents even if words differ.

3. **Graph / Knowledge Search**
   - Queries relationships between entities (nodes + edges).  
   - E.g. “Find all drugs that treat diseases related to gene X.”  
   - Uses **graph traversal / path queries** rather than text similarity.  
   - Can leverage graph algorithms (PageRank, shortest path, community detection).

---

### Workflow

1. **Documents + Entities** stored in **graph DB** with:
   - Text index (sparse)  
   - Embedding index (dense)  
   - Knowledge graph edges (relations)  

2. **User Query** runs in **three parallel modes**:
   - Sparse → keyword results (`top_k1`)  
   - Dense → semantic results (`top_k2`)  
   - Graph query → entity/relationship results (`top_k3`)  

3. **Fusion Layer** combines them:
   - Weighted sum (α·sparse + β·dense + γ·graph)  
   - Or Reciprocal Rank Fusion extended to 3 inputs:  
     \[
     \text{Score(doc)} = \frac{w_s}{c+R_s} + \frac{w_d}{c+R_d} + \frac{w_g}{c+R_g}
     \]

4. **Final Ranking** returned to user.

---

### Example

Query: *“Find treatments for lung cancer”*

- **Sparse Search** → docs with exact phrase “lung cancer”  
- **Semantic Search** → docs mentioning “pulmonary carcinoma treatment”  
- **Graph Search** → nodes: (Drug) –[treats]→ (Disease: Lung Cancer)  

**Final ranking** merges all three results with weightage.
