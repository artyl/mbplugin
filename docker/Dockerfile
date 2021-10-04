# syntax=docker/dockerfile:1

from mcr.microsoft.com/playwright:v1.15.2

WORKDIR /mbstandalone   

COPY requirements.txt requirements.txt
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

#RUN python -m pip install playwright
#CMD [ "python", "mbplugin/plugin/util.py", "standalone-get-balance"]

