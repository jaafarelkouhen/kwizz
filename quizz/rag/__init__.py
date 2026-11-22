"""Assistant RAG de MyKwizz, sur le modèle de market-risk-rag-chatbot (mohamedzayd-elfahime).

Même chaîne que ce dépôt : question → routeur d'intention → récupération dans des fiches Markdown
→ construction du prompt → LLM → garde-fous → réponse avec ses sources.
Différences : la récupération est lexicale (comme son « fast_markdown_retriever ») au lieu de Chroma,
et le LLM est Claude via quizz/ia/client.py au lieu d'Ollama. Sans clé API, l'assistant répond
quand même avec les passages des fiches.
"""
