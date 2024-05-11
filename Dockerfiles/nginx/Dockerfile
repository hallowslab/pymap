# Use an official Nginx image
FROM nginx:latest

ARG STATIC_ROOT \
    GROUPNAME \
    GID

# nginx parses variables as lower case??
# https://stackoverflow.com/questions/57676371/nginx-variables-ignore-case
ENV static_root=${STATIC_ROOT} \
    STATIC_ROOT=${STATIC_ROOT}

# Install envsubst
RUN apt-get update && \
    apt-get install -y gettext-base && \
    rm -rf /var/lib/apt/lists/*

RUN addgroup --gid $GID $GROUPNAME

# Create $STATIC_ROOT
RUN mkdir -p $STATIC_ROOT
# Add permissions for group keep user on root for nginx container
RUN chown -R root:$GROUPNAME $STATIC_ROOT && chmod -R g+rw $STATIC_ROOT

# Remove default Nginx configuration file
#RUN rm /etc/nginx/conf.d/default.conf

# Copy Nginx configuration file
COPY templates/nginx/nginx.conf /etc/nginx/conf.d/nginx.template

RUN envsubst '$STATIC_ROOT' < /etc/nginx/conf.d/nginx.template > /etc/nginx/nginx.conf

CMD ["nginx", "-g", "daemon off;"]

#CMD ["tail", "-f", "/dev/null"]
