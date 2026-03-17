FROM nginx:alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY *.html /usr/share/nginx/html/
COPY *.css /usr/share/nginx/html/
COPY assets/ /usr/share/nginx/html/assets/
COPY app.js /usr/share/nginx/html/ || true
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
