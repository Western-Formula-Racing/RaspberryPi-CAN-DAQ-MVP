FROM node:latest

WORKDIR /home/telemetry_webapp

RUN npm i --global http-server

COPY . . 

EXPOSE 8080

ENTRYPOINT ["http-server", "--cors", "-a", "0.0.0.0", "--proxy", "http://localhost:8080"]