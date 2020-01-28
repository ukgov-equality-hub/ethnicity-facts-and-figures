FROM python:3.7

RUN apt-get update && apt-get install -y wget postgresql postgresql-contrib

ENV DOCKERIZE_VERSION v0.6.1
RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz
RUN curl -sL https://deb.nodesource.com/setup_10.x | bash && apt-get install -y nodejs && npm install

EXPOSE 5000

RUN mkdir -p /app/
WORKDIR /app

ADD requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

ADD . /app/

RUN pip install pre-commit
RUN pre-commit install --install-hooks

RUN npm install -g gulp
RUN npm install
RUN npm link gulp
RUN npm rebuild node-sass
RUN gulp make

CMD /app/docker/run.sh
