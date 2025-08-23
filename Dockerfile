FROM python:3.11-slim

# set working directory
WORKDIR /app

# copy the files
COPY . .

# install
RUN pip install --no-cache-dir -r req.txt

# executable run.sh
RUN chmod +x run.sh

# run the bot
CMD ["./run.sh"]