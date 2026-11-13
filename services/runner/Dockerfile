FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app
RUN apt-get update && apt-get install -y --no-install-recommends openjdk-21-jdk-headless nodejs gcc g++ && rm -rf /var/lib/apt/lists/* \
  && groupadd --gid 10001 runner && useradd --uid 10001 --gid runner --create-home --shell /usr/sbin/nologin runner \
  && mkdir -p /runner && chown runner:runner /runner
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY runner.py .
COPY tests ./tests
USER runner
CMD ["sh", "-c", "rm -f /runner/java-runner.sock && exec uvicorn runner:app --uds /runner/java-runner.sock --log-level warning"]
