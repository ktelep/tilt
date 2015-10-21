#!/usr/bin/env python

import requests
import json


class CloudFoundryClient:

    login_url = 'https://login.run.pivotal.io/oauth/token'
    api_url = 'https://api.run.pivotal.io'

    def __init__(self, user, password):
        self.user = user
        self.password = password
        self.token = None

    def authenticate(self):
        print self.login_url   
        retval = requests.post(url=self.login_url,
                               headers={'accept': 'application/json',
                                        'Authorization': 'Basic Y2Y6'},
                               params={'username': self.user,
                                       'password': self.password,
                                       'grant_type': 'password',
                                       'scope': ''})

        self.token = json.loads(retval.content.decode('utf-8'))['access_token']

        return

    def get_app(self, app_name):

        retval = requests.get(url=self.api_url+'/v2/apps',
                              headers={'Authorization':
                                       'bearer %s' % self.token},
                              params={'q': 'name:%s' % app_name})

        apps = json.loads(retval.content.decode('utf-8'))

        app_data = dict()

        for i in apps['resources']:
            app_name = i['entity']['name']
            app_data[app_name] = dict()
            app_data[app_name]['entity'] = i['entity']
            app_data[app_name]['metadata'] = i['metadata']

            app_url = app_data[app_name]['metadata']['url']
            app_guid = app_data[app_name]['metadata']['guid']

        return {'name': app_name, 'url': app_url,
                'guid': app_guid, 'data': app_data}

    def scale_app(self, app_url, instances):

        url = self.api_url + app_url

        retval = requests.put(url=url,
                              headers={'Authorization':
                                       'bearer %s' % self.token},
                              data=json.dumps({'instances': instances}))

        print retval
