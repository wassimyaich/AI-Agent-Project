FROM python:3.12-slim

# Create and set a non-root user for execution
RUN useradd -m appuser
WORKDIR /app

COPY requirements.txt .

# Filter pywin32, install packages securely, and clean up temporary files
RUN grep -iv "pywin32" requirements.txt > requirements.container.txt && \
    pip install --no-cache-dir \
    --only-binary=:all: \
    -r requirements.container.txt \
    fastapi \
    uvicorn[standard] \
    python-docx \
    langgraph \
    pypdf \
    pdfplumber || \
    pip install --no-cache-dir \
    -r requirements.container.txt \
    fastapi \
    uvicorn[standard] \
    python-docx \
    langgraph \
    pypdf \
    pdfplumber && \
    rm requirements.container.txt

# Copy source code and set correct user permissions
COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]