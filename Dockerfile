FROM python:3.9

RUN apt-get update && apt-get install -y wget postgresql postgresql-contrib

ENV DOCKERIZE_VERSION v0.6.1
RUN wget https://github.com/jwilder/dockerize/releases/download/$DOCKERIZE_VERSION/dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz \
    && tar -C /usr/local/bin -xzvf dockerize-linux-amd64-$DOCKERIZE_VERSION.tar.gz


# Download and import the Nodesource GPG key
RUN apt-get update
RUN apt-get install -y ca-certificates curl gnupg
RUN mkdir -p /etc/apt/keyrings
RUN curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg

# Create deb repository
RUN NODE_MAJOR=18 \
    && echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_$NODE_MAJOR.x nodistro main" | tee /etc/apt/sources.list.d/nodesource.list

# Run Update and Install
RUN apt-get update
RUN apt-get install nodejs -y


# install chrome
#RUN curl --silent --show-error --location --fail --retry 3 --output /tmp/google-chrome-stable_current_amd64.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb \
#    && (dpkg -i /tmp/google-chrome-stable_current_amd64.deb || apt-get -fy install)  \
#    && rm -rf /tmp/google-chrome-stable_current_amd64.deb \
#    && sed -i 's|HERE/chrome"|HERE/chrome" --disable-setuid-sandbox --no-sandbox|g' \
#        "/opt/google/chrome/google-chrome" \
#    && google-chrome --version
#
#RUN CHROME_VERSION="$(google-chrome --version)" \
#    && export CHROMEDRIVER_RELEASE="$(echo $CHROME_VERSION | sed 's/^Google Chrome //')" && export CHROMEDRIVER_RELEASE=${CHROMEDRIVER_RELEASE%%.*} \
#    && CHROMEDRIVER_VERSION=$(curl --location --fail --retry 3 http://chromedriver.storage.googleapis.com/LATEST_RELEASE_${CHROMEDRIVER_RELEASE}) \
#    && curl --silent --show-error --location --fail --retry 3 --output /tmp/chromedriver_linux64.zip "http://chromedriver.storage.googleapis.com/$CHROMEDRIVER_VERSION/chromedriver_linux64.zip" \
#    && cd /tmp \
#    && unzip chromedriver_linux64.zip \
#    && rm -rf chromedriver_linux64.zip \
#    && mv chromedriver /usr/local/bin/chromedriver \
#    && chmod +x /usr/local/bin/chromedriver \
#    && chromedriver --version


EXPOSE 5000

RUN mkdir -p /app/
WORKDIR /app

RUN pip install --upgrade pip

ADD requirements.txt requirements.txt
#ADD requirements-test.txt requirements-test.txt
RUN pip install --no-cache-dir -r requirements.txt

#RUN pip install pre-commit
#RUN pre-commit install --install-hooks

RUN npm install -g gulp

#ADD package.json /app/
#ADD package-lock.json /app/
#ADD gulpfile.js /app/
ADD . /app/

RUN npm ci
RUN npm link gulp
RUN npm rebuild node-sass
RUN gulp make

CMD /app/docker/run.sh
