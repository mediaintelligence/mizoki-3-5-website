FROM nginx:alpine

# Copy custom nginx config
COPY nginx.conf /etc/nginx/nginx.conf

# Copy website files
COPY *.html /usr/share/nginx/html/
COPY assets/ /usr/share/nginx/html/assets/

# Cloud Run uses PORT environment variable
ENV PORT=8080

# Expose port
EXPOSE 8080

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
