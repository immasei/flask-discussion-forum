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

* Setup HTTPS - Trust CA: under `/certs`

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

* #### Signup/ Login:

  * New accounts has `Student` role by default.


* #### Chat

  * Chat Window (with emoji textarea) and Toolbar 
  
    | Tab    | RT   | Encrypted | Usage |                             
    | :--------  | :--- | :-------- | :-----------------------------------| 
    | `Friends`  | ✅   | ✅        | p2p chat, friendlist, online status |
    | `Group`    | ✅   | 🅾️        | group chat                          |
    | `Sent`     | ✅   | 🅾️        | all sent friend requests            |
    | `Received` | ✅   | 🅾️        | all received friend requests        |
    | `[icon]`   | ✅   | 🅾️        | tooltab for add/unfriend, create groupchat &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|
    | `Chat Window` | ✅   | ✅        | chat + emoji textarea       |

  * `Toolbar`
     <p><img align='center' src='readme-resources/addfr.gif' width='750'/></p>
 
     <p><img align='center' src='readme-resources/toolbar.png' width='750'/></p>

   * `Chat Window`
 
     * Server message: Yellow

     * User sent message: Blue

     * User received message: Orange   

     <p><img align='center' src='readme-resources/p2p.png' width='750'/></p>

  * `Emojitextarea` 
     
     <p><img align='center' src='readme-resources/emoji.gif' width='750'/></p>

  <br>

* #### Repo

  * Discussion Forum

    | Tab        | RT    | Usage |                             
    | :--------  | :--- | :-----------------------------------| 
    | `General Setting`  | ✅  | list all accounts, promote/demote, create repo/add member |
    | `Repo Article`    | ✅ | post (crud), comment (crud)                        |
    | `Repo Chat`     | ✅ | chat     |
    | `Repo Setting` | ✅  | list repo members, kick/add/unmute/mute member, seaarch filter &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;|

  * `Repo Article`

    * User roles are displayed in every comment and post.
      
    * All members of repo can make, delete and modify their own articles.
    
    * Staff (role Academics or higher) is able to delete and modify other people's
articles regardless of role.

    * All members of repo can make, delete their own comments.

    * Staff (role Academics or higher) can delete other people’s comments
regardless of role.
 
    <p><img align='center' src='readme-resources/post.gif' width='750'/></p>
 
  * `Repo Chat Room`

    <p><img align='center' src='readme-resources/repochat.gif' width='750'/></p>
 
  * `Repo Setting`
 
    * Kick/ add people to this repo (Administrative)

    * (Un)mute people in this repo (Academics)
   
    * `Admin` have all rights but this is targeting `Academics` & `Administrative` to operate
on a specific repo. All roles have all rights of lower level roles.
   
    * Search filter for easy user management in a specific repo.
   
    <p><img align='center' src='readme-resources/reposetting.png' width='750'/></p>

    * If a user is muted in a specific repo, all text areas and inputs within the repo
are blocked. They can’t comment or post or chat. But they can still see new
posts, new comments and new incoming messages.

    <p><img align='center' src='readme-resources/mute.png' width='750'/></p>
 
  * `General Setting`

    * Functions focus on Admin and Administrative

    * Promote/ demote/ create repo (Admin)
    
    * Select multiple people to add to existing repo (Admin and Administrative)
   
    * Show all accounts in the system with a search filter. New sign-up accounts will be
shown in real time in this table.

    * When creating a new repo, all added users will receive a notification to refresh the
webpage to see the new repo.

    <p><img align='center' src='readme-resources/generalsetting.png' width='750'/></p>
    
    <p><img align='center' src='readme-resources/addmem.gif' width='750'/></p>

    <p><img align='center' src='readme-resources/badge.gif' width='750'/></p>
 


      
