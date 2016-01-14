from aiohttp import web, log
import json
import socket


def bma_peering_generator(port):
    return {
          "version": 1,
          "currency": "test_currency",
          "endpoints": [
            "BASIC_MERKLED_API 127.0.0.1 {port}".format(port=port)
          ],
          "status": "UP",
          "block": "30152-00003E7F9234E7542FCF669B69B0F84FF79CCCD3",
          "signature": "cXuqZuDfyHvxYAEUkPH1TQ1M+8YNDpj8kiHGYi3LIaMqEdVqwVc4yQYGivjxFMYyngRfxXkyvqBKZA6rKOulCA==",
          "raw": "Version: 1\nType: Peer\nCurrency: meta_brouzouf\nPublicKey: HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk\nBlock: 30152-00003E7F9234E7542FCF669B69B0F84FF79CCCD3\nEndpoints:\nBASIC_MERKLED_API 127.0.0.1 {port}\n".format(port=port),
          "pubkey": "HnFcSms8jzwngtVomTTnzudZx7SHUQY8sVE1y8yBmULk"
        }


class Request():
    def __init__(self, method, url, content):
        self.url = url
        self.method = method
        self.content = content


class MockServer():
    def __init__(self, loop):
        self.lp = loop
        self.requests = []
        self.app = web.Application(loop=self.lp)

        self.handler = self.app.make_handler(
            keep_alive_on=False,
            access_log=log.access_logger)

    def get_request(self, i):
        return self.requests[i]

    async def _handler(self, request, data_dict, http_code):
        await request.read()
        self.requests.append(Request(request.method, request.path, request.content))
        return web.Response(body=bytes(json.dumps(data_dict), "utf-8"),
                            headers={'Content-Type': 'application/json'},
                            status=http_code)

    def add_route(self, req_type, url, data_dict, http_code=200):
        self.app.router.add_route(req_type, url,
                             lambda request: self._handler(request, data_dict=data_dict, http_code=http_code))

    def find_unused_port(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(('127.0.0.1', 0))
        port = s.getsockname()[1]
        s.close()
        return port

    async def create_server(self, ssl_ctx=None):
        port = self.find_unused_port()
        srv = await self.lp.create_server(self.handler, '127.0.0.1', port)
        protocol = "https" if ssl_ctx else "http"
        url = "{}://127.0.0.1:{}".format(protocol, port)

        self.add_route('GET', '/network/peering', bma_peering_generator(port))

        return srv, port, url