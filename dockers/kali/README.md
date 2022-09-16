# Kali Linux WSL Docker Image for Vulnerability analysis


### Notes

- Enlightenment 17 is great but xfce4 is definitely a lighter option
- XRDP works fine on the first boot, however when you restart the image it doesn't work anymore (Switched to kex for the moment)
- I haven't found a way to start kex on the docker image boot since it requires a initial configuration for a password, and there seems to be no way of supplying it programatically