# llm-zoomcamp-2026-code



Command to successful install / attach the env
```bash
source .venv/bin/activate
uv sync
python -m ipykernel install --user --name llm-zoomcamp-2026-code --display-name "Python (.venv)"
```

## Retrieval plus generation

RAG stands for Retrieval-Augmented Generation. Generation is the LLM
producing text, and retrieval is search. We retrieve relevant documents
from our knowledge base and use them to augment what the LLM generates.
That search step is what gives the LLM the context it needs to answer
correctly.


## Knowledge Base
if for persistent search, run the files starts with persistent.