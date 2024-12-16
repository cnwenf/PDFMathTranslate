import requests
from flask import Flask, request, Response, stream_with_context
from gunicorn.app.base import BaseApplication
from multiprocessing import Process


# 定义 gunicorn 服务
class StandaloneApplication(BaseApplication):
    def __init__(self, options=None):
        self.options = options or {}
        super(StandaloneApplication, self).__init__()

    def load_config(self):
        config = {key: value for key, value in self.options.items()
                  if key in self.cfg.settings and value is not None}
        for key, value in config.items():
            self.cfg.set(key.lower(), value)

    def load(self):
        app = Flask(__name__)

        # Flask 代理服务器路由，捕获所有路径和方法
        @app.route('/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD'])
        @app.route('/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD'])
        def proxy(path):
            req_headers = {key: value for (key, value) in request.headers}
            query_string = request.query_string.decode("utf-8")
            base_url = f'http://127.0.0.1:{self.options["gradio_port"]}/{path}'  # noqa
            full_url = f'{base_url}?{query_string}' if query_string else base_url
            req_data = request.get_data()
            resp = requests.request(
                method=request.method,
                url=full_url,
                headers=req_headers,
                data=req_data,
                cookies=request.cookies,
                allow_redirects=False,
                stream=True,
            )
            if 'text/event-stream' in resp.headers.get('Content-Type').lower():
                def generate():
                    for chunk in resp.iter_content(chunk_size=1):
                        yield chunk

                return Response(stream_with_context(generate()), content_type='text/event-stream')
            else:
                resp_headers = {name: value for (name, value) in resp.raw.headers.items()}
                response = Response(resp.content, status=resp.status_code, headers=resp_headers)
                return response

        return app


def run_server(proxy_port, gradio_port):
    options = {
        'bind': f'0.0.0.0:{proxy_port}',
        'workers': 4,
        'proxy_port': proxy_port,
        'gradio_port': gradio_port,
        'accesslog': '-',  # '-' means log to stdout
        'errorlog': '-',  # '-' means log to stdout
    }
    StandaloneApplication(options).run()


# 后台启动代理
def create_flask_proxy(proxy_port: int, gradio_port: int):
    Process(target=run_server, args=(proxy_port, gradio_port)).start()


if __name__ == '__main__':
    create_flask_proxy(proxy_port=8080, gradio_port=7860)