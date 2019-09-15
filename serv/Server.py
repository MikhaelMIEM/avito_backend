from http.server import HTTPServer, BaseHTTPRequestHandler
from serv.ChatDb import ChatDb
from serv.ChatDb import ChatDbError
import json


def get_server_class(database):
    class Server(BaseHTTPRequestHandler):
        def __init__(self, request, client_address, server):
            self.db = database
            super(BaseHTTPRequestHandler, self).__init__(request, client_address, server)

        def do_POST(self):
            try:
                self.post_data = self._get_data()
                response, code = self._request_handler()
            except json.decoder.JSONDecodeError:
                response, code = json.dumps('Wrong json structure'), 400
            finally:
                self._send_response(response, code)

        def _get_data(self):
            content_length = int(self.headers['Content-Length'])
            content = self.rfile.read(content_length)
            return dict(json.loads(content.decode('utf-8')))

        def _request_handler(self):
            handler = self._path_to_handler()
            return handler()

        def _send_response(self, response, code=200):
            self.send_response(code)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(response.encode('utf-8'))

        def _path_to_handler(self):
            if self.path=='/users/add':
                return self._handle_users_add
            elif self.path=='/chats/add':
                return self._handle_chats_add
            elif self.path=='/chats/get':
                return self._handle_chats_get
            elif self.path=='/messages/add':
                return self._handle_messages_add
            elif self.path=='/messages/get':
                return self._handle_messages_get

        def _check_error(func):
            def wrapped(self):
                try:
                    return func(self)
                except ChatDbError as e:
                    return json.dumps(str(e)), 400
                except KeyError:
                    return json.dumps('Wrong keys for this command'), 400
                except Exception as e:
                    return json.dumps('Internal error'), 500
            return wrapped

        @ _check_error
        def _handle_users_add(self):
            username = self.post_data['username']
            response_user_id = self.db.users_add(username)
            return response_user_id, 200

        @_check_error
        def _handle_chats_add(self):
            name, users = self.post_data['name'], self.post_data['users']
            response_chat_id = self.db.chats_add(name, users)
            return response_chat_id, 200

        @_check_error
        def _handle_messages_add(self):
            chat, author, text = self.post_data['chat'], self.post_data['author'], self.post_data['text']
            response_message_id = self.db.messages_add(chat, author, text)
            return response_message_id, 200

        @_check_error
        def _handle_messages_get(self):
            chat = self.post_data['chat']
            response_messages = self.db.messages_get(chat)
            return response_messages, 200

        @_check_error
        def _handle_chats_get(self):
            user = self.post_data['user']
            response_chats = self.db.chats_get(user)
            return response_chats, 200

    return Server


if __name__ == '__main__':
    database = ChatDb()
    Server = get_server_class(database)
    httpd = HTTPServer(('0.0.0.0', 9000), Server)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()

