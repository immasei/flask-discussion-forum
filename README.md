## Discussion Forum and Private Chat

### Setup your virtual environment and install the library

```bash
pip install -r requirements.txt
```

### Running the App

```bash
make
```

### If the web stuck, you need to flush the socket pools

```
chrome://net-internals/#sockets
```

Press flush socket pools


### HTTPS - Goto Trust CA

Steps
```
mkdir  certs  
```

```
cd certs
```

```
openssl genrsa -out CA.key 2048
```

```
openssl req -x509 -new -nodes -key CA.key -sha256 -days 825 -out CA.pem
```

```
openssl genrsa -out localhost.key 2048 
```

```
openssl req -new -key localhost.key -out localhost.csr 
```

```
touch localhost.ext
````

Insert into localhost.ext
```
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
subjectAltName = @alt_names

[alt_names]
DNS.1 = localhost
IP.1 = 127.0.0.1
```

```
openssl x509 -req -in localhost.csr -CA CA.pem -CAkey CA.key \
-CAcreateserial -out localhost.crt -days 825 -sha256 -extfile localhost.ext
```

Trust CA step
```
sudo security add-trusted-cert -d -r trustRoot -k "/Library/Keychains/System.keychain" CA.pem
```
