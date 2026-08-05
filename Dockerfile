FROM python:3.14

WORKDIR /app

COPY requirements.txt .

# Filter out pywin32 and explicitly install required framework & PDF packages
RUN grep -iv "pywin32" requirements.txt > requirements.container.txt && \
    pip install --no-cache-dir -r requirements.container.txt fastapi uvicorn[standard] python-docx langgraph pypdf pdfplumber

COPY . .

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]