# -*- coding: utf-8 -*-

import time
import hashlib


str_tail = 'FangZi'


# Hi i am the NOTE
def check_time(request_time, user_name):
    now = time.time()
    if now - request_time < len(user_name):
        return True
    else:
        return False


def check_name(user_name):
    """
        THIS IS SOME NOTE
    """
    str_key = 'Hello ' + str_tail
    return str_key in user_name


hash_key = 'Are you OK'  # Of Course U R


def check_hash(request_token):
    if hashlib.md5(hash_key).hexdigest() == request_token:
        return True

    else:
        return False
