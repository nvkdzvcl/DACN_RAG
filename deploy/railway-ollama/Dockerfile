# Ollama for the Railway "ollama" service (Root Directory: deploy/railway-ollama).
# Mount a volume at /root/.ollama so models survive redeploys. Reachable only on the private
# network: the API calls http://ollama.railway.internal:11434. Do not add a public domain.
FROM ollama/ollama:latest
# Listen on all IPv4/IPv6 interfaces, as Railway private networking requires.
ENV OLLAMA_HOST=[::]:11434
COPY start.sh /start.sh
ENTRYPOINT ["/bin/sh", "/start.sh"]
