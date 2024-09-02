FROM ubuntu:20.04

RUN apt-get update && \
    apt-get install -y postfix dovecot-core dovecot-imapd dovecot-pop3d

COPY postfix/main.cf /etc/postfix/
COPY dovecot/dovecot.conf /etc/dovecot/

EXPOSE 25 143

CMD ["sh", "-c", "service postfix start && service dovecot start && touch /var/log/mail.log && tail -f /var/log/mail.log"]
