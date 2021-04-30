FROM nginx:1.19.10-alpine

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/
COPY 502.html /etc/nginx/
COPY certs/crt.pem /etc/nginx/crt.pem
COPY certs/key.pem /etc/nginx/key.pem