# syntax=docker/dockerfile:1

from mcr.microsoft.com/playwright:v1.46.0

WORKDIR /mbstandalone

# docker build --tag mbplugin:1.00.03 mbplugin/docker --build-arg UID=$(id -u) --build-arg GID=$(id -g) --build-arg UNAME=$(whoami) 
ARG UNAME=testuser
ARG UID=1000
ARG GID=1000
ENV UNAME=$UNAME
ENV UID=$UID
ENV GID=$GID
#RUN usermod -u $UID node && groupmod -g $GID node
#RUN groupadd --gid 2000 node && useradd --uid 2000 --gid node --shell /bin/bash --create-home node
RUN groupadd -f --gid $GID $UNAME && (id -u $UNAME &>/dev/null || useradd --uid $UID --gid $UNAME --shell /bin/bash --create-home $UNAME)

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

#RUN python -m pip install playwright
#CMD [ "python", "mbplugin/plugin/util.py", "standalone-get-balance"]

