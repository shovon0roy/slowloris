detect the protocol that the website uses (http/https)
then accordingly select the port number (80 for http and 443 for https)
then run the python code to execute attack. if there is no protection in the site then
it might fall. 
example:
       python3 httpAttack.py --host www.hackme.com --port 20000 