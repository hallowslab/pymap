FROM centos:8
RUN set -xe && yum update -y && yum install -y \
  dnf-plugins-core git procps wget make cpanminus lsof epel-release\
  && yum config-manager --set-enabled powertools && yum update -y

RUN set -xe && yum install -y perl-CGI perl-NTLM perl-Crypt-OpenSSL-RSA\
  perl-Digest-HMAC perl-IO-Socket-INET6 perl-JSON \
  openssl-devel perl-Module-Runtime perl-Sys-MemInfo  \
  perl-CGI perl-Crypt-OpenSSL-RSA perl-IO-Socket-IP \
  perl-JSON perl-HTML-Parser perl-LWP-Protocol-https perl-Package-Generator\
  perl-Package-Stash-XS perl-Unicode-String

RUN set -xe && cpanm Data::Uniqid Dist::CheckConflicts Encode::IMAPUTF7 \
  File::Copy::Recursive File::Tail IO::Tee JSON::WebToken \
  HTML::Entities::Numbered LWP::UserAgent::Determined Mail::IMAPClient \
  Module::Implementation Module::ScanDeps Package::Stash \
  Readonly Regexp::Common Test::MockObject Test::Pod PAR::Packer
WORKDIR /home
RUN git clone https://github.com/imapsync/imapsync.git
WORKDIR /home/imapsync

#RUN set -xe && mkdir W && make testp
 

# yum Failed
# Data::Uniqid Dist::CheckConflicts Encode::IMAPUTF7 File::Copy::Recursive Unicode::String
# File::Tail IO::Tee JSON::WebToken HTML::Entities::Numbered LWP::UserAgent::Determined
# Mail::IMAPClient Module::Implementation Module::ScanDeps Package::Stash Package::Stash::XS
#

# cpanm Failed
# Package::Stash::XS Unicode::String

# Still missing
# Package::Stash::XS PAR::Packer Unicode::String