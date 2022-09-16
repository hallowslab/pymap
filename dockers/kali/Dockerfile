FROM kalilinux/kali-rolling
RUN set -xe && apt update && DEBIAN_FRONTEND=noninteractive apt install -yq \
  wget kali-linux-headless kali-win-kex kali-desktop-e17 terminology
  #dbus-x11 xorg xrdp kali-desktop-e17 terminology \
  #kali-tools-information-gathering \
  #kali-tools-vulnerability kali-tools-web \
  #kali-tools-forensics kali-tools-reporting 
EXPOSE 3309
EXPOSE 5901
EXPOSE 5902
RUN useradd -rm -d /home/kali -s /bin/bash -g root -G sudo -u 1001 kali
RUN echo 'kali:kali' | chpasswd
RUN echo '%sudo ALL=(ALL) NOPASSWD:ALL' >> /etc/sudoers
USER kali
WORKDIR /home/kali
#RUN echo "Enabling xrdp on port 3390" && sudo sed -i 's/port=3389/port=3390/g' /etc/xrdp/xrdp.ini
#RUN sudo rm -rf /var/run/xrdp/xrdp-sesman.pid && sudo /etc/init.d/xrdp start
#RUN echo 'alias start-xrdp="sudo service xrdp restart' >> ~/.bashrc
RUN echo "Bootstraped"
ENTRYPOINT ["/bin/bash"]