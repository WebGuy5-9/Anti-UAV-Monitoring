# Use the official NGINX image
FROM nginx:1.21-alpine

# Copy your static files to the default NGINX public directory
COPY ./static/ /usr/share/nginx/html/

# Copy your custom NGINX configuration
# This will overwrite the default config
COPY ./nginx.conf /etc/nginx/conf.d/default.conf