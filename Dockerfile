FROM coady/pylucene:10.0.0

WORKDIR /app

COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-c", "import lucene; print('lucene works')"]
