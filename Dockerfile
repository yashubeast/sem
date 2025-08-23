FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y git && \
    apt-get clean

# set working directory
WORKDIR /app

# copy the files
# COPY . .
RUN git clone https://github.com/yashubeast/sem.git .

# install
RUN pip install --no-cache-dir -r req.txt

# executable run.sh
RUN chmod +x run.sh

ENV PYTHONUNBUFFERED=1

# run the bot
CMD ["python", "main.py"]