'''
models.py - defines sql alchemy data models and class Room for socket.io rooms

Just a sidenote, using SQLAlchemy is a pain. If you want to go above and beyond, 
do this whole project in Node.js + Express and use Prisma instead, 
Prisma docs also looks so much better in comparison
or use SQLite, if you're not into fancy ORMs (but be mindful of Injection attacks :) )
'''

from sqlalchemy import String, Text, ForeignKey, Integer
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from typing import Dict, Optional, Any
import json
from sqlalchemy.ext import mutable
from sqlalchemy.types import TypeDecorator
from sqlalchemy import Boolean


class Base(DeclarativeBase):
    # [*] base model
    pass


# ref: [ this ] https://stackoverflow.com/questions/52900981/how-to-make-sqlalchemy-store-an-object-as-json-instead-of-a-relationship
class JsonEncodedDict(TypeDecorator):
    # [*] create column type of json from sqlalchemy mutable dict
    impl = Text

    def process_bind_param(self, value, dialect):
        if value is None:
            return '{}'
        else:
            return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return {}
        else:
            return json.loads(value)
mutable.MutableDict.associate_with(JsonEncodedDict)


#ref: [ composite pk ] https://stackoverflow.com/questions/65271004/primary-key-that-is-unique-over-2-columns-in-sqlalchemy
#     [ default val  ] https://stackoverflow.com/questions/9706059/setting-a-default-value-in-sqlalchemy   
class Friendship(Base):       
    # [*] table: Friendship
    __tablename__ = "friendship"

    requester: Mapped[str] = mapped_column(String, ForeignKey("user.username"), primary_key=True)
    receiver: Mapped[str] = mapped_column(String, ForeignKey("user.username"), primary_key=True)
    status: Mapped[str] = mapped_column(String, default='pending')
    
    requester_pkey: Mapped[Optional[str]] = mapped_column(String, default=None)
    receiver_pkey: Mapped[Optional[str]] = mapped_column(String, default=None)
    chat_history: Mapped[dict[str, Any]] = mapped_column(JsonEncodedDict)

    mapped_column(ForeignKey("parent_table.id"))


class GroupChat(Base):
    __tablename__ = "groupchat"
    name: Mapped[str] = mapped_column(String, primary_key=True)
    member: Mapped[dict[str, Any]] = mapped_column(JsonEncodedDict)
    chat_history: Mapped[dict[str, Any]] = mapped_column(JsonEncodedDict)


class User(Base):
    # [*] table: User
    __tablename__ = "user"
    
    username: Mapped[str] = mapped_column(String, primary_key=True)
    password: Mapped[str] = mapped_column(String)
    role: Mapped[str] = mapped_column(String, default='Student')

class Repository(Base): 
    __tablename__ = "repo"
    
    name: Mapped[str] = mapped_column(String, primary_key=True)
    member: Mapped[dict[str, Any]] = mapped_column(JsonEncodedDict)
    chat_history: Mapped[dict[str, Any]] = mapped_column(JsonEncodedDict)

class Post(Base):
     # https://soumendrak.medium.com/autoincrement-id-support-in-sqlalchemy-6a1383520ce3#:~:text=Autoincrement%20IDs%20are%20a%20convenient,the%20primary_key%20and%20autoincrement%20arguments.
     __tablename__ = "post"

     id = mapped_column(Integer, autoincrement=True, primary_key=True)
     repo: Mapped[str] = mapped_column(String, ForeignKey("repo.name"))
     title: Mapped[str] = mapped_column(String)
     author: Mapped[str] = mapped_column(String, ForeignKey("user.username"))
     content: Mapped[str] =  mapped_column(String)                    # so it can be extended to img/ file
     datetime: Mapped[str] =  mapped_column(String)      
     comment: Mapped[dict[str, Any]] = mapped_column(JsonEncodedDict) # time = user, content


class Counter():
    # [*] stateful counter used to generate the room id
    def __init__(self):
        self.counter = 0
    
    def get(self):
        self.counter += 1
        return self.counter

class Room():
    # [*] Room class 
    # self.curr::{ 'user1'       : room_id }
    # self.rooms::{ (user1, user2): room_id }
    def __init__(self):
        self.counter = Counter()
        self.curr: Dict[str, int] = {}
        self.rooms: Dict[tuple, int] = {}

    def create_room(self, members) -> int:
        room_id = self.counter.get()
        conn = tuple(sorted(members))  
        self.rooms[conn] = room_id
        return room_id
    
    def join_room(self, user: str, room_id: int) -> int:
        self.curr[user] = room_id

    def leave_room(self, party: tuple):
        self.rooms.pop(party)

    # gets the room id from a user
    def get_room_id(self, members):
        conn = tuple(sorted(members))  
        return self.rooms.get(conn)
    
    def get_participants(self, room_id: int):
        for party, room in self.rooms.items():
            if room == room_id:
                return party

