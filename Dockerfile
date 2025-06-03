FROM python:3.11-slim

# install git and other dependencies
RUN apt-get update && \
	apt-get install -y git && \
	apt-get clean

# set working directory
WORKDIR /sem

# clone the repository
RUN git clone https://github.com/yashubeast/sem.git .

# install
RUN pip install --no-cache-dir -r req.txt

# executable run.sh
RUN chmod +x run.sh

# run the bot
CMD ["python", "run.sh"]