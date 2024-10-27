FROM python

WORKDIR /usr/src/app

COPY . . 
RUN python setup.py install
