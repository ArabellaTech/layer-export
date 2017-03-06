from __future__ import print_function

import json
import os.path
import sys
import urllib.request
from datetime import date
from time import sleep

import click
import dateutil.parser
import requests
from Crypto.PublicKey import RSA

METHOD_PATCH = 'patch'


def safe_unicode(string):
    if sys.version_info[0] < 3:
        return unicode(string)  # NOQA
    return str(string)


class LayerPlatformException(Exception):
    def __init__(self, message, http_code=None, code=None, error_id=None):
        super(LayerPlatformException, self).__init__(message)
        self.http_code = http_code
        self.code = code
        self.error_id = error_id


class LayerExport(object):
    api_host = 'api.layer.com'

    def __init__(self, app_id, bearer_token):
        self.app_uuid = self._normalize_id(app_id)
        self.bearer_token = bearer_token
        self.setup()
        self.register_key()
        self.request_export()
        self.get_export()
        self.get_downloads()

    def _log(self, message):
        click.echo(message)

    def _normalize_id(self, id):
        return id.split('/')[-1]

    def setup(self):
        self.directory = 'export'
        self.downloads_directory = 'export/downloads'
        if not os.path.exists(self.downloads_directory):
            os.makedirs(self.downloads_directory)

    def register_key(self):
        self._log('Registering Public Key...')

        if not os.path.isfile("key.public") or not os.path.isfile("key.private"):
            self.key = RSA.generate(2048)
            key_public = self.key.publickey().exportKey('PEM').decode("utf-8")
            key_private = self.key.exportKey('PEM').decode("utf-8")

            with open("key.public", 'w') as content_file:
                content_file.write(key_public)
            with open("key.private", 'w') as content_file:
                content_file.write(key_private)
        else:
            with open("key.public", 'r') as content_file:
                key_public = content_file.read()
            with open("key.private", 'r') as content_file:
                key_private = content_file.read()

        self._raw_request(
            'put',
            'export_security',
            {'public_key': key_public}
        )

    def get_export(self):
        self._log('Getting export...')
        while True:
            export = self._raw_request('get', 'exports/{export_id}/status'.format(export_id=self.export_id))
            print(export)  # FIXME: remove
            if not export['download_url']:
                self._log('No export yet, sleeping for 1 min...')
                sleep(60)
            else:
                break

        urllib.request.urlretrieve(export['download_url'], self.directory + '/export.enc.tar.gz')

        self._log('ENCRYPTED_AES_KEY: ' + export['encrypted_aes_key'])
        self._log('AES_IV: ' + export['aes_iv'])
        click.confirm('Please manually decode and continue. Continue?', abort=True)

    def request_export(self):
        self._log('Requesting export...')
        exports = self._raw_request('get', 'exports')
        if exports:
            export_date = dateutil.parser.parse(exports[0]['created_at'])
            if export_date.date() == date.today():
                self.export_id = exports[-1]['id']
                return
        self.export_id = self._raw_request('post', 'exports')['id']

    def get_downloads(self):
        self._log('Getting downloads...')
        i = 1

        with open(self.directory + '/export.json', 'r') as f:
            content = json.loads(f.read())
            for item in content:
                for message in item['messages']:
                    for part in message.get('parts', []):
                        if part.get('content', {}).get('download_url'):
                            urllib.request.urlretrieve(part['content']['download_url'],
                                                       '{}/{}'.format(self.downloads_directory, i))
                            part['content']['download_url'] = i
                            i += 1

        with open(self.directory + '/export.json', 'w') as f:
            f.write(json.dumps(content))

    def _get_layer_uri(self, *suffixes):
        """
        Used for building Layer URIs for different API endpoints.
        Parameter`suffixes`: An array of strings, which will be joined as the
            end portion of the URI body.
        Return: A complete URI for an endpoint with optional arguments
        """
        return 'https://{host}/apps/{app_id}/{suffix}'.format(
            host=self.api_host,
            app_id=self.app_uuid,
            suffix='/'.join(map(safe_unicode, suffixes)),
        )

    def _get_layer_headers(self, method):
        """
        Convenience method for retrieving the default set of authenticated
        headers.
        Return: The headers required to authorize ourselves with the Layer
        platform API.
        """

        content_type = 'application/json'
        if method == METHOD_PATCH:
            content_type = 'application/vnd.layer-patch+json'

        return {
            'Accept': 'application/vnd.layer+json; version=1.0',
            'Authorization': 'Bearer ' + self.bearer_token,
            'Content-Type': content_type
        }

    def _raw_request(self, method, path, data=None, extra_headers=None,
                     params=None):
        """
        Actually make a call to the Layer API.
        If the response does not come back as valid, raises a
        LayerPlatformException with the error data from Layer.
        Parameters:
        - `method`: The HTTP method to use
        - `url`: The target URL
        - `data`: Optional post body. Must be json encodable.
        Return: Raw JSON doc of the Layer API response
        Exception: `LayerPlatformException` if the API returns non-OK response
        """
        url = self._get_layer_uri(path)
        print(url)  # FIXME: remove
        headers = self._get_layer_headers(method)
        if extra_headers:
            headers.update(extra_headers)
        result = requests.request(
            method,
            url,
            headers=headers,
            data=(json.dumps(data) if data else None),
            params=params
        )

        if result.ok:
            try:
                return result.json()
            except ValueError:
                # On patch requests it fails because there is no response
                return result
        try:
            error = result.json()
            raise LayerPlatformException(
                error.get('message'),
                http_code=result.status_code,
                code=error.get('code'),
                error_id=error.get('id'),
            )
        except ValueError:
            # Catches the JSON decode error for failures that do not have
            # associated data
            raise LayerPlatformException(
                result.text,
                http_code=result.status_code,
            )


@click.command()
@click.option('--app-id', prompt='App ID')
@click.option('--token', prompt='Bearer Token', hide_input=True)
def cli(app_id, token):
    LayerExport(app_id, token)


if __name__ == '__main__':
    cli()
