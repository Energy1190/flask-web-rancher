import uuid
import json
import requests
from requests.auth import HTTPBasicAuth

class Env():
    env = {'DB_CONNECTION': None, 'DB_HOST': None, 'DB_PORT': 0, 'DB_ADMIN_USERNAME': None, 'DB_ADMIN_PASSWORD': None, 'URL': None,
           'DB_CREATED': False}

class RancherAPI():
    def __init__(self, key=None, secret=None, base_url=None):
        self.project = None
        self.loadbalancer = None

        self.key = key
        self.secret = secret
        self.base_url = base_url

        assert base_url
        self._test()
        self.project_list = [i.get('id') for i in self.get_project_list().get('data')]

        self.name = None
        self.id = None
        self.serviceid = None
        
        self.dockercompose = None
        self.ranchercompose = None
        self.description = None
        self.environment = {'SITEURL': None}
        self.group = "io.rancher.service.create_by_app"

        self.data = {}

    def error(func):
        def wrap(self, *args, **kwargs):
            x = func(self, *args, **kwargs)
            if x.get('type') == 'error':
                assert False, 'There was an error: {} as "{}".'.format(x.get('status'), x.get('code'))
            return x
        return wrap

    def auth(func):
        def wrap(self, *args, **kwargs):
            if self.key and self.secret: x = func(self, auth=HTTPBasicAuth(self.key, self.secret), *args, **kwargs)
            else: x = func(self, *args, **kwargs)
            return x
        return wrap

    def post_processing(func):
        def wrap(self, *args, **kwargs):
            x = func(self, *args, **kwargs)
            if x.get('id'): self.id = x.get('id')
            if x.get('name'): self.name = x.get('name')
            return x
        return wrap

    @auth
    @error
    def _test(self, **kwargs):
        try:
            x = requests.get(self.base_url + '/v2-beta', **kwargs)
        except:
            return {'type': 'error', 'status': 1, 'code': 'Failed to connect', 'message': 'Failed to connect'}
        return x.json()

    @auth
    @error
    def get_stack_list(self, **kwargs):
        assert self.project
        x = requests.get(self.base_url + '/v2-beta/projects/{}/stacks'.format(self.project), **kwargs)
        return x.json()

    @auth
    @error
    def get_project_list(self, **kwargs):
        x = requests.get(self.base_url + '/v2-beta/projects', **kwargs)
        return x.json()

    @auth
    @error
    def get_load_balancer_list(self, **kwargs):
        assert self.project
        x = requests.get(self.base_url + '/v2-beta/projects/{}/loadbalancerservices'.format(self.project), **kwargs)
        return x.json()

    def set_project(self, name=None):
        if not name and len(self.get_project_list()['data']) == 1:
            self.project = self.get_project_list()['data'][0]['id']
        else:
            self.project = name

    def set_load_balancer(self, name=None):
        if not name and len(self.get_load_balancer_list()['data']) == 1:
            self.loadbalancer = self.get_load_balancer_list()['data'][0]['id']
        else:
            self.loadbalancer = name
            
    def set_service_id(self, name=None):
        if not name and len(self.get_service_list()['data']) == 1:
            self.serviceid = self.get_service_list()['data'][0]['id']
        else:
            self.serviceid = name
            
    def set_data(self):
        self.data['type'] = 'stack'
        self.data['name'] = (self.name or "Unknown-stack")
        self.data['description'] = (self.description or "No description")
        self.data['group'] = self.group
        self.data['environment'] = self.environment
        if self.dockercompose: self.data['dockerCompose'] = self.dockercompose
        if self.ranchercompose: self.data['rancherCompose'] = self.ranchercompose

    @auth
    @error
    @post_processing
    def create_stack(self, **kwargs):
        assert self.project
        self.set_data()
        x = requests.post(self.base_url  + '/v2-beta/projects/{}/stacks'.format(self.project), data=json.dumps(self.data), **kwargs)
        return x.json()

    @auth
    @error
    def remove_stack(self, **kwargs):
        assert self.project
        assert self.id
        x = requests.delete(self.base_url  + '/v2-beta/projects/{}/stacks/{}'.format(self.project, self.id), **kwargs)
        return x.json()

    @auth
    @error
    def update_stack(self, **kwargs):
        assert self.project
        assert self.id
        self.set_data()
        x = requests.put(self.base_url  + '/v2-beta/projects/{}/stacks/{}'.format(self.project, self.id), data=self.data, **kwargs)
        return x.json()

    @auth
    @error
    @post_processing
    def get_stack(self, id, **kwargs):
        assert self.project
        x = requests.get(self.base_url  + '/v2-beta/projects/{}/stacks/{}'.format(self.project, id), **kwargs)
        r = x.json()
        if r.get('group') == "io.rancher.service.create_by_app": return r

    @auth
    @error
    def register_lb(self, **kwargs):
        assert self.project
        assert self.loadbalancer
        assert self.serviceid
        data = {"serviceLink": {"name":self.name + '_lb', "serviceid": self.serviceid, "uuid": uuid.uuid4()}}
        x = requests.post(self.base_url + '/v2-beta/projects/{}/loadbalancerservices/{}/?action=addservicelink'.format(self.project, self.loadbalancer), data=json.dumps(data), **kwargs)
        return x.json()
    
    @auth
    @error
    def get_service_list(self, **kwargs):
        assert self.project
        assert self.id
        x = requests.get(self.base_url + '/v2-beta/projects/{}/stacks/{}/services'.format(self.project, self.id), **kwargs)
        return x.json()
