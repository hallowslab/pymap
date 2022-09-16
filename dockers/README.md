

### Notes

- Starting Wordpress
  * `docker-compose -f .\stack.yml up --remove-orphans`
- Stopping Wordpress (Does not erase volume data)
  * `docker-compose -f .\stack.yml down --remove-orphans`
- Stopping Wordpress (erases volume data)
  * `docker-compose -f .\stack.yml down -v --remove-orphans`

- Acessing volumes on windows
 * \\wsl$\docker-desktop-data\version-pack-data\community\docker\volumes