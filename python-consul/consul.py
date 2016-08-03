import requests
import json
from base64 import b64decode


class Consul:
    def __init__(self, server='http://localhost:8500'):
        """Create a new consul object

        Args:
            server: URL to consul (defaults to http://localhost:8500)
        """
        self.server = server

    @staticmethod
    def _http(method, url, data=None):
        """Function to call requests to speak to the consul HTTP API"""
        if method == 'PUT':
            r = requests.put(url, data)
        elif method == 'GET':
            r = requests.get(url, params=data)
        elif method == 'DELETE':
            r = requests.delete(url)
        else:
            return None
        try:
            return r.status_code, r.json()
        except ValueError:
            return r.status_code, None

    @staticmethod
    def _get(url, data=None):
        """Calls _http with method='GET'"""
        return Consul._http('GET', url, data)

    @staticmethod
    def _put(url, data):
        """Calls _http with method='PUT'"""
        return Consul._http('PUT', url, data)

    @staticmethod
    def _delete(url):
        """Calls _http with method='PUT'"""
        return Consul._http('DELETE', url)

    @staticmethod
    def is_passing(nodes, node):
        """Check if a node is passing all of its consul defined health checks.

        Args:
            node: name or IP of node
            nodes: parsed dump from services API call
        Returns:
            Boolean
        """
        for this in nodes:
            this_node = this['node']
            if this_node['Node'] == node or this_node['Address'] == node:
                for check in node['Checks']:
                    if check['Status'] != 'passing':
                        break
                else:
                    return False
            return True

    def get_kv(self, key):
        """Reads b64 decoded value from Consul for given key

        Args:
            key (str): key to get
        Returns:
            Decoded string
        """
        url = "{}/v1/kv/{}".format(self.server, key)
        resp = self._get(url)
        if resp[0] == 200:
            return b64decode(resp[1][0]['Value'])

    def put_kv(self, key, value, acquire=None):
        """Puts a key/value in to Consul.

        Args:
            key: string
            value: string
            acquire: Optional session ID to lock
        Returns:
            HTTP Status Code
        """
        url = "{}/v1/kv/{}".format(self.server, key)
        if acquire:
            url += "?acquire=%s" % acquire
        resp = self._put(url, data=value)
        return resp

    def delete_kv(self, key):
        """Delete a key/value from Consul

        Args:
            key: string
        :return: HTTP_STATUS_CODE
        """
        url = "{}/v1/kv/{}".format(self.server, key)
        return self._delete(url)

    def create_session(self, data):
        """Create a session

        Args:
            data: Dict of options to pass to Consul
        Returns:
            Session ID (string)
        """
        url = "{}/v1/session/create".format(self.server,)
        resp = self._put(url, json.dumps(data))
        return resp[1]

    def destroy_session(self, session_id):
        """Destroy a session (thereby removing associated locks)

        Args:
            session_id
        Returns:
            (HTTP Status Code, RESPONSE)
        """
        url = "{}/v1/session/destroy/{}".format(self.server, session_id)
        return self._put(url, '')

    def get_nodes(self, service):
        """Return a list of healthy nodes from Consul

        Args:
            service: string
        Returns:
            List of IPs
        """
        url = "{}/v1/health/service/{}".format(self.server, service)
        ips = list()
        nodes = self._get(url)[1]
        for node in nodes:
            if Consul.is_passing(nodes, node):
                ips.append(node['Node']['Address'])
        return ips
