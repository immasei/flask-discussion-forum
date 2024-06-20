'''
db.py - database file, containing all the logic to interface with the sql database
'''

from sqlalchemy import create_engine, or_, and_
from sqlalchemy.orm import Session
from models import *

from pathlib import Path
from login import gen_hash
from datetime import datetime

# creates the database directory
Path("database") \
    .mkdir(exist_ok=True)

# "database/main.db" specifies the database file
# turn echo = True to display the sql output
engine = create_engine("sqlite:///database/main.db", echo=False)
Base.metadata.create_all(engine)

def insert_user(username: str, password: str):
    # [*] create new user
    with Session(engine) as session:  
        user = User(username=username, password=gen_hash(password))
        session.add(user)
        session.commit()

def now():
    return datetime.now().strftime("%m/%d/%Y, %H:%M:%S").replace(',', '.')

def get_user(username: str):
    # [*] get existing user
    with Session(engine) as session:
        return session.get(User, username)
    

# ref: [ query result to dict ] https://stackoverflow.com/questions/17717877/convert-sqlalchemy-query-result-to-a-list-of-dicts
#      [ remove instance key  ] https://stackoverflow.com/questions/17665809/remove-key-from-dictionary-in-python-returning-new-dictionary
def to_dict(query):
    # [*] HELPER FUNC
    # remove instance key so that <home.jinja: let friendlist = {{friendlist | tojson}};> works
    if query is None: return {}
    return {k:v for k,v in query.__dict__.items() if k != '_sa_instance_state'}
    

def get_friendship(user, friend):
    # get friendship
    with Session(engine) as session:
        friendship = session.get(Friendship, (user, friend))

        if friendship is None:
             friendship = session.get(Friendship, (friend, user))
        return to_dict(friendship)


# ref: [ session get composite key ] https://docs.sqlalchemy.org/en/20/orm/session_api.html#sqlalchemy.orm.Session.get
def send_friend_request(user: str, friend: str):
    # [*] requester::user send a friend request
    with Session(engine) as session:
        if user == friend:
            return False     # same user
        if get_user(user) is None or get_user(friend) is None:
            return False     # user not found
        if get_friendship(user, friend):
            return False     # relationship exists
        
        # [create] status::pending
        friendship = Friendship(requester=user, receiver=friend)
        session.add(friendship)
        session.commit()
        return True          # valid friend request

# ref: [ update method ] https://www.tutorialspoint.com/sqlalchemy/sqlalchemy_orm_updating_objects.htm
#      [ where and/or ] https://www.tutorialspoint.com/sqlalchemy/sqlalchemy_orm_using_query.htm
def approve_friend_request(user: str, friend: str, log_key: str):
    # [*] receiver::user approve friend request
    # [update] status::approved
    # [update] receiver_pkey::log_key
    with Session(engine) as session:
        session.query(Friendship).filter(and_(Friendship.requester == friend, 
                                              Friendship.receiver == user)
                                ).update({'status': 'approved', 
                                          "receiver_pkey": log_key})
        session.commit()

# ref: [ delete method ] https://docs.sqlalchemy.org/en/20/orm/session_basics.html#deleting
def remove_friend(user: str, friend: str):
    # [*] reject pending friend request
    # [*] revoke friend request
    # [*] unfriend
    with Session(engine) as session:
        friendship = session.get(Friendship, (friend, user))
        if friendship is None:
            friendship = session.get(Friendship, (user, friend))

        session.delete(friendship)
        session.commit()


# ref: [ where and/or ] https://www.tutorialspoint.com/sqlalchemy/sqlalchemy_orm_using_query.htm
def get_friendlist(user: str):
    # [*] get friendlists of 1 user
    # [get] status::approved
    # [get] status::pending
    with Session(engine) as session:
        friendships = session.query(Friendship,
                            ).filter(or_(Friendship.requester == user, 
                                         Friendship.receiver == user))
        friendlist = [to_dict(friendship) for friendship in friendships]
        for friendship in friendlist:
            if friendship['requester'] == user:
                friendship['role'] = get_user(friendship['receiver']).role
            else:
                friendship['role'] = get_user(friendship['requester']).role

        return friendlist
    
def get_userlist():
    with Session(engine) as session:
        users = session.query(User).all()
        userlist = [to_dict(u) for u in users]

        return userlist
    
def create_groupchat(user, groupname, member):
     # [*] requester::user send a friend request
    with Session(engine) as session:
        if get_groupchat(groupname) is not None:
            return False
        if get_user(groupname) is not None:
            return False

        # [create] status::pending
        group = GroupChat(name=groupname)
        session.add(group)
        session.commit()

        group = session.get(GroupChat, groupname)
        for i in member:
            group.member[i] = 'member'
        group.member[user] = 'admin'
        session.commit()

        return True          # valid friend request

def get_grouplist(user: str):
    # [*] get friendlists of 1 user
    # [get] status::approved
    # [get] status::pending
    with Session(engine) as session:
        groups = session.query(GroupChat).all()
        groups = [to_dict(g) for g in groups if g.member.get(user, None) is not None]

        return groups
    
def get_groupchat(group: str):
    # [*] get existing user
    with Session(engine) as session:
        return session.get(GroupChat, group)

 # ref: [ where and/or ] https://www.tutorialspoint.com/sqlalchemy/sqlalchemy_orm_using_query.htm   
def update_pkey(user, friend, log_key):
    # [*] requester::user save log key
    # [update] requester_pkey::log_key
    with Session(engine) as session:
        session.query(Friendship).filter(and_(Friendship.requester == user, 
                                              Friendship.receiver == friend)
                                ).update({"requester_pkey": log_key})
        session.commit()


# ref: [   current time   ] https://www.freecodecamp.org/news/python-get-current-time/
#      [ upd mutable dict ] https://dsbowen.github.io/sqlalchemy-mutable/mutable_dict/
def save_message(user, friend, message, from_server=False):
    # [*] save message
    # [update] chat_history::message 
    with Session(engine) as session:                                # either
        friendship = session.get(Friendship, (user, friend))        # requester::user
        if friendship is None:
             friendship = session.get(Friendship, (friend, user))   # requester::friend

        if friendship is None:
            return
        # [if message if from server]
        sender = user
        if from_server: sender = None
            
        friendship.chat_history[now()] = [sender, message]
        session.commit()

def _save_message(user, group, message, from_server=False):
    with Session(engine) as session:             
        groupchat = session.get(GroupChat, group) 
        if groupchat is None:
            return
        # [if message if from server]
        sender = user
        if from_server: sender = None
            
        groupchat.chat_history[now()] = [sender, message]
        session.commit()

def set_role(username: str, role: str):
    with Session(engine) as session:
        session.query(User).filter(User.username == username).update({'role': role})
        session.commit()


def get_repo(reponame: str):
    # [*] get existing user
    with Session(engine) as session:
        return session.get(Repository, reponame)
    
def add_mem_repo(user, reponame, memlist):
    with Session(engine) as session: 
        type = 'add'

        # create repo
        if get_repo(reponame) is None:
            type = 'create'
            # no right to create repo
            if get_user(user).role not in ['Admin']:
                return False
            
            repo = Repository(name=reponame)
            session.add(repo)
            session.commit()

        # no right to add member 
        if get_user(user).role not in ['Admin', 'Administrative']:
            return False

        # add member to repo
        repo = session.get(Repository, reponame)
        new = [i for i in memlist if repo.member.get(i) is None]
            
        for i in memlist:
            # so re add mem dont change their mute status
            if repo.member.get(i) is None:
                repo.member[i] = False 

        if repo.member.get(user) is None:
            repo.member[user] = False

        session.commit()

        return (type, new)

def get_role(role, up=True):
    roles = ['Student', 
              'Academics', 
              'Administrative',
              'Admin']
    
    if up:
        loc = min(roles.index(role) + 1, 3)
    else: 
        loc = max(roles.index(role) - 1, 0)
    
    return roles[loc]

def get_rank(role):
    roles = ['Student', 
              'Academics', 
              'Administrative',
              'Admin']
    return roles.index(role)

    

def change_password(user, target, new_password):
    with Session(engine) as session: 
        if get_user(user).role not in ['Admin']:
            return False
        
        get_user(target).password = gen_hash(new_password)
        session.commit()
        return True


def promote(promoter, promoted, up=True):
    with Session(engine) as session: 
        target = get_user(promoted)
        user = get_user(promoter)

        if user is None or user.role not in ['Admin']:
            return False
        
        new_role = get_role(target.role, up)
        session.query(User).filter(User.username == promoted
                                   ).update({'role': new_role})
        session.commit()

        return new_role

    
def kick_mem_repo(user, reponame, to_kick):
    with Session(engine) as session: 
        repo = session.get(Repository, reponame)

        # kicked but not logged out so still havr access
        if repo.member.get(user) is None:
            return False
        
        # no right to kick member 
        if get_user(user).role not in ['Admin', 'Administrative']:
            return False
        
        if get_rank(get_user(user).role) < get_rank(get_user(to_kick).role):
            return False
        
        repo.member.pop(to_kick, None)

        session.commit()

        return True
    
def mute_mem_repo(user, reponame, to_mute):
    with Session(engine) as session: 
        repo = session.get(Repository, reponame)

        # kicked but not logged out so still havr access
        if repo.member.get(user) is None:
            return False
        
        # no right to mute member 
        if get_user(user).role not in ['Admin', 'Administrative', 'Academics']:
            return False
        
        if get_rank(get_user(user).role) < get_rank(get_user(to_mute).role):
            return False

        repo.member[to_mute] = not repo.member[to_mute]
        session.commit()
        return (True, repo.member[to_mute])

    
def create_post(user, repo, title, content):
    with Session(engine) as session:
        post = Post(repo=repo, 
                    title=title, 
                    author=user, 
                    content=content,
                    datetime=now())
        
        session.add(post)
        session.commit()

        return {'author': post.author, 
                'repo': repo, 
                'title': title, 
                'content': content, 
                'postid': post.id,
                'datetime': post.datetime,
                'role': get_user(user).role}

def save_comment(user, comment, postid):
    with Session(engine) as session:
        post = session.get(Post, int(postid))
        if post is None:
            return
            
        time = now()
        post.comment[f'{time}{user}'] = [time, user, comment]
        session.commit()

        return {'author': user,
                'role': get_user(user).role,
                'datetime': time,
                'content': comment,
                'postid': postid}

def get_repolist(user: str):
    with Session(engine) as session:
        repos = session.query(Repository).all()
        repos = [to_dict(r) for r in repos if r.member.get(user, None) is not None]

        for repo in repos:
            repo['muted'] = dict(repo['member'])
            for member in repo['member']:
                repo['member'][member] = get_user(member).role

        return repos
    
def get_postlist(repos):
    with Session(engine) as session:
        # repos = session.query(Repository).all()
        postlist = []
        for repo in repos:
            posts = session.query(Post).filter(Post.repo == repo['name'])
            postlist.extend([to_dict(p) for p in posts])

        # author and role
        for post in postlist:
            post['role'] = get_user(post['author']).role

            # commenter and role
            for k, v in post['comment'].items():
                user = v[1]
                post['comment'][k].append(get_user(user).role)

            post['comment'] = dict(reversed(list(post['comment'].items())))

        return postlist
    
def delete_post(user, postid):
    with Session(engine) as session:
        post = session.get(Post, postid)
        if get_user(user).role in ['Student'] and user != post.author:
            return False

        session.delete(post)
        session.commit()
        return True

def delete_comment(user, postid, author, time):
     with Session(engine) as session:
        post = session.get(Post, int(postid))

        if get_user(user).role in ['Student'] and user != author:
            return False

        post.comment.pop(f'{time}{author}', None)

        session.commit()
        return True

def modify_post(user, postid, title, content):
    print(postid,  title, content)
    with Session(engine) as session:
        post = session.get(Post, int(postid))
        if get_user(user).role in ['Student'] and post.author != user:
            return False

        session.query(Post).filter(Post.id == int(postid)).update({'title': title, 
                                                                   'content': content})
        session.commit()
        return True

def save_repo_mess(reponame, sender, message, from_server=False):
    with Session(engine) as session:             
        repo = session.get(Repository, reponame)
        if repo is None:
            return

        if from_server: sender = None
        time = now()
        if repo.chat_history.get(time) is None:
            repo.chat_history[time] = [(sender, message)]
        else:
            repo.chat_history[time] = repo.chat_history[time] + [(sender, message)]

        session.commit()

        return {'repo': reponame, 'sender': sender, 'message': message, 'datetime': time}
    

admin = 'X'
if get_user(admin) is None:
    insert_user(admin, 'pwd')
    set_role(admin, 'Admin')



# insert_user('z', 'x')
# set_role('a', 'Admin')
# insert_user('s', 'x')
# insert_user('s3', 'x')
# insert_user('s2', 'x')
# insert_user('b', 'd')
# insert_user('a', 'v')
# insert_user('c', 'd')
# promote('X', 'z')
# mute_mem_repo('X', 'COMP2123', 'c')

# add_mem_repo('X', 'INFO1113', ['a'])
# add_mem_repo('X', 'INFO1112', ['c'])
# print(add_mem_repo('X', 'COMP2123', ['X']))

# create_post('X', 'COMP2123', 'hey', 'stay fcking still :)')
# create_post('a', 'COMP2123', 'hwllo', 'asfjhaf')
# print(get_postlist(get_repolist('X')))
# save_comment('a', 'yesnt', 2)
# delete_comment('1', 'a', '05/09/2024, 02:42:58')
# delete_post(1)
# modify_post(1, 'New', 'stay fcking still neh :)')
# _save_repo_mess('COMP2123', 'X', 'yy')
# _save_repo_mess('COMP2123', 'a', 'halo')
# send_friend_request('a', 'X')

# print(get_userlist())
