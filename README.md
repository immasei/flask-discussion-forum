## Academic Discussion Forum and Messaging

### Techstack

| Frontend   | Backend                 | Database  |
| :--------  | :-----------------------| :--------------------- | 
| Jinja + Bootstrap 5   | Flask (Python) | SQLite               |
| JS + JQuery + Axios   | Flask-SocketIO | SQLAlchemy      |

### Execution

* Dependencies Installation
  
  ```
    pip install -r requirements.txt
  ```

* Setup HTTPS: under `/certs`

  ```
    (MAC only) cd certs/
  ```
    
  ```
     sudo security add-trusted-cert -d -r trustRoot -k "/Library/Keychains/System.keychain" CA.pem
  ```

* Run program

  ```
    make
  ```

  * Default Admin Account:  (`X`, `pwd`)
 
* If the web stuck or crash, you need to `flush socket pools`

  ```
    chrome://net-internals/#sockets
  ```

### Features

```
  Realtime update: RT
```

* `Navbar`

* `Signup/ Login`: New accounts has `Student` role by default.

* `Chat`: Chat Window (Emojicon) and Tool Bar

  * `Tool Bar`
  
      | Tab    | RT   | Encrypted | Usage |                             
      | :--------  | :--- | :-------- | :-----------------------------------| 
      | `Friends`  | ✅   | ✅        | p2p chat, friendlist, online status |
      | `Group`    | ✅   | 🅾️        | group chat                          |
      | `Sent`     | ✅   | 🅾️        | all sent friend requests            |
      | `Received` | ✅   | 🅾️        | all received friend requests        |
      | `[icon]`   | ✅   | 🅾️        | tooltab for add/unfriend, create groupchat        |

 <p align='center'>
    <img align='center' src='readme-resources/addfr.gif' width='750'/>
 </p>
 
 <p align='center'>
    <img align='center' src='readme-resources/toolbar.png' width='750'/>
 </p>

   * `Chat Window` (with `Emoji Text Area`)

 <p align='center'>
    <img align='center' src='readme-resources/p2p.png' width='750'/>
 </p>

  <p align='center'>
    <img align='center' src='readme-resources/emoji.gif' width='750'/>
 </p>


      







Trust CA step
```
sudo security add-trusted-cert -d -r trustRoot -k "/Library/Keychains/System.keychain" CA.pem
```
