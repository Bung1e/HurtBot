FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y curl gnupg libicu-dev && \
    curl -sL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs git && \
    npm install -g azure-functions-core-tools@4 --unsafe-perm true && \
    apt-get clean && rm -rf /var/lib/apt/lists/*


WORKDIR /app

COPY pyproject.toml ./

RUN pip install --no-cache-dir -e .

COPY . .

EXPOSE 7071 8000

ENV PYTHONPATH=/app
ENV AzureWebJobsScriptRoot=/app
ENV AZURE_FUNCTIONS_ENVIRONMENT=Development
ENV AzureFunctionsJobHost__Logging__Console__IsEnabled=true
ENV FUNCTIONS_WORKER_RUNTIME=python

CMD ["func", "host", "start"]