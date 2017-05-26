# Reverse shell C&C and client

C&C (Command & Control server) and client providing reverse-shell with ssl encryption for *nix, written in pure python3.

Initial setup
-------------

Firstly, you need to create your own ssl certificates (you don't wanna anybody to hijack your reverse shell, do you?).
To do so, run following commands:

1. Create new private key (you'll be prompted for a password):

        openssl genrsa -des3 -out server.key 1024  

2. Create certificate request, provide all asked information (use fake if required):

        openssl req -new -key server.key -out server.csr
    
3. In order to use key without password, use dirty trick: 

        copy server.key server.key.org
        openssl rsa -in server.key.org -out server.key
    
4. Finally, create self-signed certificate:

        openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt
        
As certificate is self-signed, you need to place `server.crt` certificate file in the same directory with `client.py` in order to client to work.

Usage
-----

Change host and port in `client.py` script. 

Start server script on C&C machine:

        python3 server.py
        
Then on client start client script:

        python3 client.py
        
Order does not matter, considering the fact that client tries to reach the server each 15 seconds, so it can be started using cron job or lauched on target machine's launch. 
