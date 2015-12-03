# -*- coding: utf-8 -*-

import hashlib
import time

import pymongo

from config import *
from fangzi.settings import *


class Request(object):

    def __init__(self, request_time, user_name, request_token):
        self.request_time = request_time
        self.user_name = user_name
        self.request_token = request_token


def connect():
        conn = pymongo.Connection(URL, PORT)
        db = conn[DATABASE]
        collection = db[COLLECTION]
        return collection


def traditional_check(req):

    import functions

    result = functions.check_time(req.request_time, req.user_name)
    print 'check_time %s' % result
    result = functions.check_name(req.user_name)
    print 'check_name %s' % result
    result = functions.check_hash(req.request_token)
    print 'check_hash %s' % result


def fang_zi_check():

    clt = connect()

    import_part = clt.find_one({'_id': 'IMPORT_PART'})
    if import_part:
        exec import_part['body']

    static_part = clt.find_one({'_id': 'STATIC_PART'})
    if static_part:
        exec static_part['body']

    func_part = clt.find({'flag': 'CODE'})
    for c in func_part:

        exec '%s, = %s' % (c['para'], [eval('request.%s' % para) for para in c['para'].split(',')])

        try:
            exec c['body']
            pass
        except Exception, result:
            print '%s %s' % (c['_id'], result)

if __name__ == '__main__':

    time = time.time()
    name = 'FangZi How Are U'
    token = hashlib.md5('Are you OK').hexdigest()
    request = Request(time, name, token)

    if CHECK_TYPE == 'DEVELOP':
        traditional_check(request)
    elif CHECK_TYPE == 'PRODUCT':
        fang_zi_check()
