FROM python:3.12
WORKDIR /usr/local/yapper

# Install the application dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r --break-system-packages requirements.txt

# Copy in the source code
COPY src/* ./
EXPOSE 0471
# 471 spells 'atl' on a calculator, referencing to All Things Linux, check em out at discord.gg/linux they are very cool :p

CMD ["python", "app.py"]
