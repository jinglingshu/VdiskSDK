#!/usr/bin/env python
# -*- coding: utf-8 -*-

__version__ = '1.0'
__author__ = 'memoryboxes@gmail.com'

'''
Python client SDK for sina vdisk API.
support:
http://openapi.vdisk.me/?a=keep
http://openapi.vdisk.me/?m=auth&a=get_token
http://openapi.vdisk.me/?m=user&a=keep_token
http://openapi.vdisk.me/?m=file&a=upload_file
http://openapi.vdisk.me/?m=file&a=upload_share_file
http://openapi.vdisk.me/?m=dir&a=create_dir
http://openapi.vdisk.me/?m=dir&a=getlist
http://openapi.vdisk.me/?m=file&a=get_quota
http://openapi.vdisk.me/?m=file&a=upload_with_sha1
http://openapi.vdisk.me/?m=file&a=get_file_info
http://openapi.vdisk.me/?m=dir&a=delete_dir
http://openapi.vdisk.me/?m=file&a=delete_file
http://openapi.vdisk.me/?m=file&a=copy_file
http://openapi.vdisk.me/?m=file&a=move_file
http://openapi.vdisk.me/?m=file&a=rename_file
http://openapi.vdisk.me/?m=dir&a=rename_dir
http://openapi.vdisk.me/?m=dir&a=move_dir
http://openapi.vdisk.me/?m=file&a=share_file
http://openapi.vdisk.me/?m=file&a=cancel_share_file
http://openapi.vdisk.me/?m=recycle&a=get_list
http://openapi.vdisk.me/?m=recycle&a=truncate_recycle
http://openapi.vdisk.me/?m=recycle&a=delete_file
http://openapi.vdisk.me/?m=recycle&a=delete_dir
http://openapi.vdisk.me/?m=recycle&a=restore_file
http://openapi.vdisk.me/?m=recycle&a=restore_dir
http://openapi.vdisk.me/?m=dir&a=get_dirid_with_path

how to use:
    please notice  __main__ function
'''

try:
    import json
except ImportError:
    import simplejson as json
import time
import hmac, hashlib
import urllib, urllib2

_HTTP_GET = 1
_HTTP_POST = 2

def _get_json_request(req):
    resp = urllib2.urlopen(req)
    body = resp.read()
    r = json.loads(body)
    if r['err_code'] <> 0:
        raise APIError(r.error_code, getattr(r, 'err_msg', ''), http_url)
    return r

def _http_call(client, url, method, authorization, **kw):
    '''
    send an http request and expect to return a json object if no error.
    '''
    url_ext = '?token=' + client.access_token
    params = {}
    params['token'] = client.access_token
    for k, v in kw.iteritems():
        params[k] = v
        url_ext += ('&%s=%s' % (k, v))


    http_url = (method == _HTTP_GET) and ('%s%s' %(url ,url_ext)) or ('%s' % (url))
    params = (method == _HTTP_GET) and None or params
    req = (method == _HTTP_GET) and urllib2.Request(http_url) or urllib2.Request(http_url, urllib.urlencode(params))

    return _get_json_request(req)


class APIError(StandardError):
    '''
    raise APIError if got failed json message.
    '''
    def __init__(self, error_code, error, request):
        self.error_code = error_code
        self.error = error
        self.request = request
        StandardError.__init__(self, error)

    def __str__(self):
        return 'APIError: %s: %s, request: %s' % (self.error_code, self.error, self.request)


class HttpObject(object):
    '''
    http request wrapper
    '''
    def __init__(self, client, method):
        self.client = client
        self.method = method

    def __getattr__(self, attr):
        def wrap(**kw):
            return _http_call(client,
                    '%s?m=%s&a=%s' % (self.client.api_url, attr.split('__')[0], attr.split('__')[1]),
                    self.method, self.client.access_token, **kw)
        return wrap


class VDiskAPIClient(object):
    '''
    vdisk api wrapper
    '''
    def __init__(self, account, password, appkey, app_secret):
        self._user = account
        self._password = password
        self._appkey = appkey
        self._app_secret = app_secret
        self._expires = 15 * 60

        self.access_token = None
        self.api_url = 'http://openapi.vdisk.me/'
        self.get = HttpObject(self, _HTTP_GET)
        self.post = HttpObject(self, _HTTP_POST)

        #just hack code for get_token methord ...
        self.post.auth__get_token = self.__auth__get_token
        self.post.keep = self.__keep

    def __auth__get_token(self, app_type='local'):
        '''
        get access token
        '''
        def _get_signature(account, appkey, password, app_secret, str_time):
            str = 'account=' + account + '&appkey=' + appkey + '&password=' + password + '&time=' + str_time
            h = hmac.new(app_secret, str, hashlib.sha256)
            s = h.hexdigest()
            return s

        str_time = str(int(time.time()))
        values = {'account' : self._user,
            'password' : self._password,
            'time' : str_time,
            'appkey' : self._appkey,
            'app_type' : app_type,
            'signature' : _get_signature(self._user, self._appkey, self._password, self._app_secret, str_time)}

        req = urllib2.Request(self.api_url + '?m=auth&a=get_token', urllib.urlencode(values))
        json_token_res = _get_json_request(req)
        self.access_token = json_token_res['data']['token']
        return json_token_res


    def __keep(self):
        '''
        reflesh dologid
        '''
        values = {'token' : self.access_token}

        req = urllib2.Request(self.api_url + '?a=keep', urllib.urlencode(values))
        return _get_json_request(req)


if __name__ == '__main__':
    client = VDiskAPIClient('memoryboxes@163.com', 'XXXXX', 'XXXXX', 'bde9b687cf20ad580888fb3be5e87ec6')
    client.post.auth__get_token()

    print client.post.dir__get_dirid_with_path(path = '/')
    print client.post.dir__getlist(dir_id = 0)

