FROM python:3.9

RUN apt install wget
RUN pip install pandas sqlalchemy psycopg2 pyarrow
RUN pip install --upgrade google-cloud-bigquery

ENV CLIENT_ID=
ENV CLIENT_SECRET=
ENV REDIRECT_URI=
ENV GOOGLE_APPLICATION_CREDENTIALS=

WORKDIR /app
COPY . .

ENTRYPOINT [ "python", "spotify_etl.py"]