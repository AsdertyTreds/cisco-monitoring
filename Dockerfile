FROM python:3.8
RUN  mkdir - /usr/src/cisco-monitoring
WORKDIR /usr/src/cisco-monitoring
COPY . /usr/src/cisco-monitoring
EXPOSE 8080
ENV TZ Europe/Moscow
RUN pip install --no-cache-dir -r reqirement.txt
CMD ["python","main.py"]
