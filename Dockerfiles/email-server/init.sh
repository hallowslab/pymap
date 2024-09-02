mkdir -p /var/mail/pymap/Maildir/{cur,new,tmp}
chown -R pymap:pymap /var/mail/pymap
echo 'pymap:Password123' > /etc/dovecot/users


mkdir -p /var/mail/test/Maildir/{cur,new,tmp}
chown -R test:test /var/mail/test
echo 'test:Password123' >> /etc/dovecot/users


service dovecot start
service postfix start

tail -f /var/log/postfix.log /var/log/dovecot.log