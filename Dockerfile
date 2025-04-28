FROM python:3.12
WORKDIR /usr/local/yapper

# Install the application dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire src directory, preserving folder structure
COPY /src/ ./  # This ensures /templates, /static and everything stays in the correct places

EXPOSE 5050

CMD ["python", "src/app.py"]  # Adjust this based on your folder structure
