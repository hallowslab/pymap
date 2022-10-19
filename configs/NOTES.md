
# General notes:

## **Special characters**
- https://lists.bestpractical.com/pipermail/rt-users/2011-November/073861.html
    * Knowledge that I'd like to document for the list. By trial and error, on Centos 5 I've found that you should use single quotes if your password contains special characters such as '$'. Double-quotes didn't work.

## **Davmail as proxy for Outlook/Exchange/Office365 services**
- [Davmail](http://davmail.sourceforge.net/)
- [A nice post ;)](https://exhaust.lewiscollard.com/post/146866104/office365-to-migadu-migration/)
```
./imapsync \
  --host1 localhost \
  --port1 1143 \
  --user1 'USERNAME' \
  --debugimap1 \
  --password1 '12345' \
  --host2 HOSTNAME/IP \
  --user2 'USERNAME' \
  --password2 '12345'
```

Multiple instances of Davmail can be running with different configurations **MAKE SURE TO CHANGE ALL THE PORTS IN THE PROPERTIES FILE**:
```
davmail davmail.properties
davmail davmail2.properties
.....
```