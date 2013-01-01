from random import choice
from string import ascii_letters,digits

def make():
    page_id = "".join([choice(ascii_letters+digits) for x in range(5)])
    return page_id
