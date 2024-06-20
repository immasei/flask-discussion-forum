import bcrypt
import base64
import hashlib

# Encode string to bytestring
# ref: https://stackoverflow.com/questions/27519306/hashlib-md5-typeerror-unicode-objects-must-be-encoded-before-hashing
def to_byte(string: str):
    return string.encode('utf-8')

# Decode bytestring to string
def to_string(bstring: str):
    return bstring.decode('utf-8')

# Hash plain password using sha256
# ref: https://stackoverflow.com/questions/65067575/python-bcrypt-how-to-check-a-long-encrypted-by-sha256-password
def gen_hash(password: str): 
    password = hashlib.sha256(to_byte(password)).digest() # hash password with sha256

    return bcrypt.hashpw(
                base64.b64encode(password),               # base64 encode to prevent null byte
                bcrypt.gensalt())                         # hash result with salt

def check_password(actual: str, expected: str):
    actual = hashlib.sha256(to_byte(actual)).digest()     # hash raw password with sha256

    return bcrypt.checkpw(                                # compare hash
                base64.b64encode(actual),                 
                expected)