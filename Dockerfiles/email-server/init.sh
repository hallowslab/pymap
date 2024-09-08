service dovecot start
service postfix start

tail -f /var/log/dovecot.log /var/log/postfix.log /var/log/mail.log