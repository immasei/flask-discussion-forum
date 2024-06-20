
'''
socket_routes
file containing all the routes related to socket.io
'''

from flask_socketio import join_room, emit, leave_room
from flask import request, abort, url_for
try:
    from __main__ import socketio
except ImportError:
    from app import socketio

from models import Room
from app import validate_token
import db

room = Room()
online_users = {} # list of online users with its connection id (sid) and rsa public key
 
# ref: [ socket example ] https://www.squash.io/implementing-real-time-features-with-flask-socketio-and-websockets/#:~:text=Flask%2DSocketIO%20is%20a%20Flask,the%20overhead%20of%20HTTP%20polling
#      [ socket general ] https://flask-socketio.readthedocs.io/en/latest/getting_started.html
#      [ include_self   ] https://stackoverflow.com/questions/29266594/broadcast-to-all-connected-clients-except-sender-with-python-flask-socketio
#      [ broadcast      ]

# ref: [request.sid] https://stackoverflow.com/questions/66610562/socketio-to-emit-to-a-particular-user-without-using-separate-room-for-every-cli
def authenticate_request(username):
    if username is None or validate_token() != username:
        return True
    return False

@socketio.on('connect')
def connect():
    # [*] when the client connects to a socket
    user = request.cookies.get("username")
    # [401][unauthorized request]
    # if authenticate_request(user): return url_for('login')
    # [upd online users][everyone]
    online_users[user] = {'id': request.sid, 'pub_key': None}
    emit('notification', {'online_users': online_users}, broadcast=True)


@socketio.on('disconnect')
def disconnect():
    # [*] event when client disconnects
    user = request.cookies.get("username")
    room_id = room.curr.get(user)
    room.curr.pop(user, None)

    # [401][unauthorized request]
    # if authenticate_request(user): return url_for('login')
    # [upd online users][everyone]
    online_users.pop(user, None)
    emit('notification', {'online_users': online_users}, broadcast=True)
    # [disconnected][room_id]
    if room_id is not None:
        to_save = f"{user} has disconnected"
        emit("incoming", {'username': None, 
                          'message': to_save, 
                          'color': 'red', 
                          'timestamp':db.now()}, 
                          to=int(room_id))
        # [find the other friend]
        participants = room.get_participants(int(room_id))
        friend = [i for i in participants if i != user][0]
        # [save message]
        db.save_message(user, friend, to_save, from_server=True)
        db._save_message(user, friend, to_save, from_server=True)


@socketio.on("send")
def send(user, to_send, hmac, room_id, to_save):
    # [*] send message::send button
    # [401][unauthorized request]
    # if authenticate_request(user): return url_for('login')

    # [transfer message][room_id]
    if to_send is not None:
        emit("incoming", {'username': user, 'message': to_send, 
                          'hmac': hmac, 'color': 'black', 'timestamp':db.now()}, 
                          to=int(room_id))
    # [find the other friend]
    participants = room.get_participants(int(room_id))
    friend = [i for i in participants if i != user][0]
    # [save message]
    db.save_message(user, friend, to_save)


@socketio.on("join")
def join(user, friend):
    # [*] join room::chat button
    # if authenticate_request(user): return url_for('login')  # [401][unauthorized request]
    sender = db.get_user(user)
    receiver = db.get_user(friend)

    if sender is None or receiver is None: abort(404)       # [404][not found]
    # [join room]
    room_id = room.get_room_id([user, friend])   
    to_other = f"{user} has joined the room."
    to_self =  f"{user} has joined the room. Now talking to {friend}."       
    
    if room_id is not None:                                 # [room exist]
        join_room(room_id)
        # [join noti][except sender]
        emit("incoming", {'username': None, 'message': to_other, 'color': 'green', 'timestamp':db.now()}, 
                          to=room_id, include_self=False)
        # [join noti][sender only]
        emit("incoming", {'username': None, 'message': to_self, 'color': 'green', 'timestamp':db.now()})
    else:                                                   # [new room]
        room_id = room.create_room([user, friend])
        join_room(room_id)
        # [join noti][sender only]
        emit("incoming", {'username': None, 'message': to_self, 'color': 'green', 'timestamp':db.now()}, 
                          to=room_id)

    db.save_message(user, friend, to_other, from_server=True)
    room.curr[user] = room_id
    # [exchange public key]
    emit('rsa', online_users.get(user, {}).get('pub_key'), 
                to=room_id, include_self=False)
    return {'room_id': room_id, 
            'pub_key': online_users.get(friend, {}).get('pub_key'), 
            'chat_log': db.get_friendship(user, friend).get('chat_history'),
            'friendlist': db.get_friendlist(user)}

@socketio.on("_join")
def _join(user, group):
    # if authenticate_request(user): return url_for('login')  # [401][unauthorized request]
    
    groupchat = db.get_groupchat(group)
    if groupchat is None: abort(404)       # [404][not found]
    # [join room]
    room_id = room.get_room_id([group])   
    noti = f"{user} has joined the room."
    
    if room_id is None:    
        room_id = room.create_room([group])      

    join_room(room_id)
    # [join noti][sender only]
    emit("incoming", {'username': None, 'message': noti, 'color': 'green', 'timestamp':db.now()}, 
                        to=room_id)

    # [save message from server][1]
    db._save_message(user, group, noti, from_server=True)
    room.curr[user] = room_id
    # [exchange public key]
    return {'room_id': room_id, 
            'chat_log': groupchat.chat_history, 
            'mem': [*groupchat.member]}

@socketio.on("_send")
def _send(user, room_id, message):
    # [*] send message::send button
    # [401][unauthorized request]
    # if authenticate_request(user): return url_for('login')

    # [transfer message][room_id]
    emit("incoming", {'username': user, 'message': message, 
                          'hmac': None, 'color': 'black2', 'timestamp':db.now()}, 
                          to=int(room_id))

    group = room.get_participants(int(room_id))[0]
    # [save message]
    db._save_message(user, group, message)


@socketio.on("leave")
def leave(username, room_id):
    # [*] leave room event handler
    # [401][unauthorized request]
    # if authenticate_request(username): return url_for('login')
    participants = room.get_participants(int(room_id))

    if participants is not None:
        to_save = f"{username} has left the room."
        # [leave noti][room_id]
        emit("incoming", {'username': None, 
                        'message': to_save, 
                        'color': 'red', 'timestamp':db.now()}, 
                        to=room_id, include_self=False)
         # [find the other friend]
        friend = [i for i in participants if i != username][0]
        # [save message]
        # db.save_message(username, friend, to_save, from_server=True)
        # db._save_message(username, friend, to_save, from_server=True)
        
    room.curr.pop(username, None)
    leave_room(room_id)
    return -1


@socketio.on('rsa')
def send_rsa(public_key):
    # [*] send rsa public key
    username = request.cookies.get("username")
    # [401][unauthorized request]
    # if authenticate_request(username): return url_for('login')

    # [update self public key]
    online_users[username]['pub_key'] = public_key
    emit('no_pkey', broadcast=True)


@socketio.on('aes')
def send_aes(secret_key, room_id):
    # [*] send aes symmetric key for communication
    username = request.cookies.get("username")
    # [401][unauthorized request]
    # if authenticate_request(username): return url_for('login')
    # [exchange secret key for communication]
    emit('aes', {'sec_key': secret_key}, to=room_id, include_self=False)


@socketio.on('ask_pkey')
def ask_pkey(user, friend):
    # [*] requester::user asking for log key
    # [401][unauthorized request]
    # if authenticate_request(user): return url_for('login')

    user_id = online_users.get(user, {}).get('id')
    friend_id = online_users.get(friend, {}).get('id')
    # [if both online]
    if user_id and friend_id:
        emit('approver', 
                {'username': user, 
                 'pub_key': online_users.get(user, {}).get('pub_key')
                }, to=friend_id)


@socketio.on('send_pkey')
def send_pkey(user, friend, log_key): 
    # [*] receiver:user send log key
    # [401][unauthorized request]
    # if authenticate_request(user): return url_for('login')
    # [if online]
    friend_id = online_users.get(friend, {}).get('id')
    if friend_id:
        emit('receive_pkey', {'username': user, 'pkey': log_key}, to=friend_id)

@socketio.on('save_pkey')
def save_pkey(user, friend, log_key):
    # [*] requester::user save log key
    # [401][unauthorized request]
    if authenticate_request(user): return url_for('login')
    # [requester save log key]
    db.update_pkey(user, friend, log_key)


@socketio.on('request')
def send_request(user, friend):
    # [*] requester::user send friend request
    # # [401][unauthorized request]
    # if authenticate_request(user): return url_for('login')

    # [create pending friend request]
    if db.send_friend_request(user, friend):
        user_id = online_users.get(user, {}).get('id')
        friend_id = online_users.get(friend, {}).get('id')
        # [if requester online][request sent]
        if user_id:
            emit('sent', {'username': friend}, to=user_id)
        # [if receiver online][request received]
        if friend_id:
            emit('received', {'username': user}, to=friend_id)


@socketio.on('approve')
def approve_request(user, friend, log_key):
    # [*] receiver::user approve friend request
    # [approve friend request]
    db.approve_friend_request(user, friend, log_key)
    user_id = online_users.get(user, {}).get('id')
    friend_id = online_users.get(friend, {}).get('id')

    # [if requester online][request approved]
    if friend_id:
        emit('approved', {'username': user, 'status': 'online', 'role': db.get_user(user).role}, to=friend_id)
        # [if both online][exchange log key]
        if user_id:
            emit('approver', 
                 {'username': friend, 
                  'pub_key': online_users.get(friend, {}).get('pub_key')
                 }, to=user_id)
        return {'status': 'online', 'role': db.get_user(friend).role}    
    return {'status': 'offline', 'role': db.get_user(friend).role} 


@socketio.on('remove')
def remove_friend(user, friend, table):
    # [*] receiver::user reject friend request
    # [401][unauthorized request]
    # [reject friend request]
    db.remove_friend(user, friend)
    friend_id = online_users.get(friend, {}).get('id')
    # [if requester online][request rejected]
    if friend_id:
        emit('removed', {'username': user, 'table': table}, to=friend_id)

    
@socketio.on('create-group')
def create_groupchat(user, groupname, member):
    # [*] requester::user send friend request
    if groupname == '':
        return {'message': 'Group Name Unavailable', 'category': 'danger'}

    # [create pending friend request]
    if db.create_groupchat(user, groupname, member):
        user_id = online_users.get(user, {}).get('id')
        if user_id:
            emit('group-created', {'groupname': groupname}, to=user_id)

        for friend in member:
            friend_id = online_users.get(friend, {}).get('id')

            if friend_id:
                emit('group-created', {'groupname': groupname}, to=friend_id)

        return {'message': 'Group Successfully Created', 'category': 'success'}
    else:
        return {'message': 'Group Name Unavailable', 'category': 'danger'}
    

@socketio.on('create-post')
def create_post(user, repo, title, content, room_id):
    if title == '' or content == '':
        return {'message': 'Post Empty', 'category': 'danger'}

    new_post = db.create_post(user, repo, title, content)
    emit("post-create", new_post, to=room_id)
    
    return {'message': 'Post Created', 'category': 'success'}

@socketio.on('create-comment')
def create_comment(user, comment, postid, room_id):
    if comment == '':
        return {'message': 'Comment Empty', 'category': 'danger'}

    new_comment = db.save_comment(user, comment, postid)
    emit("comment-create", new_comment, to=room_id)

    return {'message': 'Post Created', 'category': 'success'}

@socketio.on('delete-post')
def delete_post(user, postid, room_id):

    if db.delete_post(user, postid):
        emit("post-delete", {'postid': postid}, to=room_id)
        return {'message': f'Post #{postid} deleted', 'category': 'success'}
    else:
        return {'message': 'No permission', 'category': 'danger'}


@socketio.on('delete-comment')
def delete_comment(user, postid, author, time, room_id):

    if db.delete_comment(user, postid, author, time):
        emit("comment-delete", {'postid': postid,
                                'author': author,
                                'datetime': time}, to=room_id)
        return {'message': f'Comment deleted', 'category': 'success'}
    return {'message': 'No permission', 'category': 'danger'}

@socketio.on('modify-post')
def modify_post(user, postid, title, content, room_id):

    if db.modify_post(user, postid, title, content):
        emit("post-modified", {'postid': postid,
                            'title': title,
                            'content': content}, to=room_id)
        return {'message': f'Post #{postid} modified', 'category': 'success'}
    return {'message': 'No permission', 'category': 'danger'}


@socketio.on("join-repo")
def join_repo(user, reponame):
    repo = db.get_repo(reponame)
    if repo is None: abort(404)       # [404][not found]

    # [join room]
    room_id = room.get_room_id([reponame])   
    noti = f"{user} has joined the room."
    
    if room_id is None:    
        room_id = room.create_room([reponame])      

    join_room(room_id)
    # [join noti][sender only]
    emit("incoming", {'username': None, 'message': noti, 'timestamp':db.now()}, 
                        to=room_id)

    # [save message from server][1]
    # db._save_message(user, group, noti, from_server=True)
    room.curr[user] = room_id
    return {'room_id': room_id, 
            'chat_log': repo.chat_history, 
            'muted': repo.member[user]}

@socketio.on("send-repo")
def repo_send_message(user, reponame, room_id, message):
    # [save message]
    new_message = db.save_repo_mess(reponame, user, message)
    emit("recv-mess", new_message, to=int(room_id), include_self=False)
    emit("recv-mess", new_message)

@socketio.on('add-mem-repo')
def add_mem_repo(user, reponame, memlist, room_id, type='add'):

    if isinstance(memlist, str):
        if db.get_user(memlist) is None:
            return {'message': 'Username not exist', 'category': 'danger'}
        memlist = [memlist]

    res = db.add_mem_repo(user, reponame, memlist)

    mems = [{'name': mem, 'role': db.get_user(mem).role} for mem in list(set(memlist))]
    if not res:
        return {'message': 'No permission', 'category': 'danger'}
    elif type == 'creaadd':
        dtype = res[0]
        memlist = res[1]
        if dtype == 'create':
            for i in list(set(memlist)):
                iid = online_users.get(i, {}).get('id')
                if iid:
                    emit("repo-create", {'message': f'You have been added to repo {reponame}. Refresh the page to see it.', 
                                         'category': 'success'}, to=iid)
            return {'message': 'Repo created. Refresh the page.', 'category': 'success'}
        else:
            emit("repo-add-mem", 
                {'mems': mems,
                    'repo': reponame}, broadcast=True)
            return {'message': 'Member added.', 'category': 'success'}
    else:
        emit("repo-add-mem", 
                 {'mems': mems, 'repo': reponame}, to=int(room_id))
        print([{'name': mem, 'role': db.get_user(mem).role} for mem in list(set(memlist))])
        return {'message': 'Member added.', 'category': 'success'}

@socketio.on('kick-mem-repo')
def kick_mem_repo(user, reponame, to_kick, room_id):
    if not db.kick_mem_repo(user, reponame, to_kick):
        return {'message': 'No permission', 'category': 'danger'}
   
    emit("repo-kick-mem", {'mem': to_kick, 'repo': reponame}, to=int(room_id))
    return {'message': 'Kicked.', 'category': 'success'}

@socketio.on('mute-mem-repo')
def mute_mem_repo(user, reponame, to_mute, room_id):
    res = db.mute_mem_repo(user, reponame, to_mute)
    if not res:
        return {'message': 'No permission', 'category': 'danger'}
   
    emit("repo-mute-mem", {'mem': to_mute, 'repo': reponame, 'prev': res[1]}, to=int(room_id))

    if res[1]:
        return {'message': 'Muted.', 'category': 'success'}
    return {'message': 'Unmuted.', 'category': 'warning'}

@socketio.on('promote-user')
def role(user, target, room_id, up=True):

    new_role = db.promote(user, target, up)
    print(new_role)
    if new_role:
        emit("user-promote", {'mem': target, 'role': new_role}, to=int(room_id))
        if up:
            return {'message': 'Promoted.', 'category': 'success'}
        else:
            return {'message': 'Demoted.', 'category': 'warning'}
    else:
        return {'message': 'No permission', 'category': 'danger'}