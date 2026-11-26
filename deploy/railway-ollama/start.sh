#!/bin/sh
# Start Ollama, then pull the two models once (a no-op when they are already on the volume).
set -e
ollama serve &
server=$!
until OLLAMA_HOST=http://[::1]:11434 ollama list >/dev/null 2>&1; do sleep 1; done
for model in ${LLM_MODEL:-qwen3:4b} ${EMBEDDING_MODEL:-embeddinggemma:300m}; do
  OLLAMA_HOST=http://[::1]:11434 ollama pull "$model"
done
echo "Ollama ready with ${LLM_MODEL:-qwen3:4b} and ${EMBEDDING_MODEL:-embeddinggemma:300m}"
wait "$server"
