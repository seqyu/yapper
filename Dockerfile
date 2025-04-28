FROM python:3.12
WORKDIR /usr/local/yapper

# Install the application dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire src directory, preserving folder structure
COPY /src/ ./

EXPOSE 5050

CMD ["python", "app.py"]
