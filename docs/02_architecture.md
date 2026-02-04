# System Architecture

The system follows a standard retrieval-augmented generation (RAG) architecture.

1. Data Ingestion  
   Source documents and datasets are collected from semiconductor-related inputs.

2. Chunking  
   Documents are split into semantically meaningful chunks to improve retrieval quality.

3. Embeddings  
   Each chunk is converted into a vector representation using an embedding model.

4. Vector Store  
   Embeddings are stored in a vector database to enable semantic similarity search.

5. Retrieval-Augmented Generation (RAG)  
   Relevant chunks are retrieved based on the user query and provided to the LLM as context.

6. Response Generation  
   The LLM generates a grounded response, including citations to the retrieved sources.

Optional future extensions include tool calls (SQL, Python), analytics dashboards, and workflow automation.
