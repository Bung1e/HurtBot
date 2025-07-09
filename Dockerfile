FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y curl gnupg libicu-dev && \
    curl -sL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs git && \
    npm install -g azure-functions-core-tools@4 --unsafe-perm true


WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -e .

EXPOSE 7071 8000

ENV PYTHONPATH=/app
ENV AzureWebJobsScriptRoot=/app
ENV AZURE_FUNCTIONS_ENVIRONMENT=Development

CMD ["uv", "run", "python", "-m", "azure.functions.worker", "--host", "0.0.0.0", "--port", "7071"]