FROM --platform=arm64 arm64v8/nginx:1.27.0-alpine-slim

ENV TZ=Asia/Tokyo

COPY ./default.conf /etc/nginx/conf.d/default.conf
COPY ./html /usr/share/nginx/html
