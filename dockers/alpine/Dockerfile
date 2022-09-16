FROM alpine:3.14
RUN set -xe && apk update && apk add \
  git perl curl wget lsof bash bash-completion make procps \
  perl-unicode-string perl-test-mockobject perl-par-packer perl-sys-meminfo \
  perl-package-stash-xs perl-html-parser perl-cgi perl-crypt-ssleay \
  perl-crypt-openssl-rsa perl-io perl-io-socket-ssl perl-io-socket-inet6 \
  perl-json perl-json-webtoken perl-test-mock-guard perl-lwp-useragent-determined \
  perl-term-readkey perl-app-cpanminus
RUN cpanm Authen::NTLM Data::Uniqid Digest::HMAC Digest::HMAC_MD5 Encode::IMAPUTF7 \
  File::Copy::Recursive File::Tail IO::Tee Mail::IMAPClient Parse::RecDescent Readonly \
  Regexp::Common Test::Fatal Test::Requires Test::Deep
WORKDIR /home
RUN git clone https://github.com/imapsync/imapsync.git
WORKDIR /home/imapsync
RUN set -xe && make testp
RUN set -xe && mkdir W && make install
