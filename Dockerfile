FROM python:latest
ARG MAINTAINER="zfxmnb <fanx1949@gmail.com>"
LABEL maintainer=${MAINTAINER}
COPY /.data.example /.data
COPY main.py /main.py
COPY /templates /templates
COPY /static /static
COPY requirements.txt /requirements.txt
# volume
VOLUME /.data
ARG PORT=80
EXPOSE ${PORT}
ENV PORT=80
ENV DATA_DIR=/.data
RUN python -m pip install -r /requirements.txt --break-system-packages
# entry point
ENTRYPOINT ["python", "/main.py"]