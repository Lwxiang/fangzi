# -*- coding: utf-8 -*-

import hashlib
import time

from pymongo import MongoClient

from config import *
from fangzi.settings import *


class Request(object):
    """
        A Simple Request Example
    """

    def __init__(self, request_time, user_name, request_token):
        self.request_time = request_time
        self.user_name = user_name
        self.request_token = request_token


def connect():
    """
        Connect to MONGODB
    """
    conn = MongoClient(URL, PORT)
    db = conn[DATABASE]
    collection = db[COLLECTION]
    return collection


def traditional_check(req):
    """
        Traditional way to do check
        import and call each functions to get result
        It takes long and complex code to do this
        It is hard to change and manage those functions
    """

    import functions

    result = functions.check_time(req.request_time, req.user_name)
    print 'check_time %s' % result
    result = functions.check_name(req.user_name)
    print 'check_name %s' % result
    result = functions.check_hash(req.request_token)
    print 'check_hash %s' % result


def fang_zi_check():
    """
        The dynamic-function_check way
        Get code from database(You can set a update cache time to prevent fetching each time)
        Execute each function code and get its result
    """

    clt = connect()

    # Create a base namespace
    base = {}

    # Exec IMPORT
    import_part = clt.find_one({'_id': 'IMPORT_PART'})
    if import_part:
        exec import_part['body'] in base

    # Exec STATIC
    static_part = clt.find_one({'_id': 'STATIC_PART'})
    if static_part:
        exec static_part['body'] in base

    func_part = clt.find({'flag': 'CODE'})

    # Exec each functions code
    for c in func_part:
        # A namespace to process the function in local scope
        ns = base

        # Initialize the parameters of each function
        exec '%s, = %s' % (c['para'], [eval('request.%s' % para) for para in c['para'].split(',')]) in ns

        # Exec the code and use except to catch
        try:
            exec c['body'] in ns
            pass
            # If there is no Exception, then the code is fail
        except Exception, result:
            print '%s %s' % (c['_id'], result)

if __name__ == '__main__':

    time = time.time()
    name = 'FangZi How Are U'
    token = hashlib.md5('Are you OK').hexdigest()
    request = Request(time, name, token)

    # In your project, you can keep the functions file, and use it to test the functions' performing
    # And if everything is OK, you can change CHECK_TYPE from DEVELOP to PRODUCT to use dynamic way
    if CHECK_TYPE == 'DEVELOP':
        traditional_check(request)
    elif CHECK_TYPE == 'PRODUCT':
        fang_zi_check()
