import sqlite3
import json
from os.path import join, abspath, dirname


class ChatDbError(Exception):
    pass


class ChatDb:

    def __init__(self):
        self._db_file = join(dirname(abspath(__file__)), 'chat.db')
        self._tables_creation_file = join(dirname(abspath(__file__)), 'tables_creation_commands')
        self._db_commands = self._get_commands_from_file()
        self._connection = self._create_connection()
        self._create_tables()

    def _get_commands_from_file(self):
        with open(self._tables_creation_file, 'r') as file:
            return dict(json.load(file))

    def _create_connection(self):
        conn = sqlite3.connect(self._db_file)
        conn.row_factory = sqlite3.Row
        return conn

    def _create_tables(self):
        self._set_to_db(self._db_commands["create table user"])
        self._set_to_db(self._db_commands["create table chat"])
        self._set_to_db(self._db_commands["create table user_in_chat"])
        self._set_to_db(self._db_commands["create table message"])
        self._connection.commit()

    def _set_to_db(self, command):
        try:
            cur = self._connection.cursor()
            cur.execute(command)
        except sqlite3.IntegrityError:
            raise ChatDbError("Instance already exist")

    def _get_from_db(self, command, convert_to_json = False):
        cur = self._connection.cursor()
        cur.execute(command)
        rows = cur.fetchall()
        values = [dict(row) for row in rows]
        if convert_to_json:
            return json.dumps(values)
        else:
            return values

    def users_add(self, name):
        insert_user_command = self._db_commands["user insert"].format(name)
        self._set_to_db(insert_user_command)

        select_user_command = self._db_commands["user select"].format(name)
        user_field = self._get_from_db(select_user_command, convert_to_json=True)

        self._connection.commit()
        return user_field

    def chats_add(self, name, users):
        if not self._check_users_existence(users):
            raise ChatDbError("User does not exist")

        insert_chat_command = self._db_commands["chat insert"].format(name)
        self._set_to_db(insert_chat_command)

        select_chat_command = self._db_commands["chat select"].format(name)
        chat_field = self._get_from_db(select_chat_command)
        chat_id = chat_field[0]['id']

        for users_id in users:
            self._set_to_db(self._db_commands["user in chat insert"].format(users_id, chat_id))
        self._connection.commit()
        return json.dumps(chat_field)

    def _check_users_existence(self, users_id):
        for id in users_id:
            row = self._get_from_db(self._db_commands["user by id select"].format(id))
            if not bool(row):
                return False
        return True

    def messages_add(self, chat, author, text):
        if not self._check_users_existence([author]):
            raise ChatDbError("User does not exist")
        if not self._check_chats_existence([chat]):
            raise ChatDbError("Chat does not exist")
        if not self._check_user_in_chat_existence(chat, author):
            raise ChatDbError("User does not belong to this chat")

        insert_message_command = self._db_commands["message insert"].format(chat, author, text)
        self._set_to_db(insert_message_command)

        select_message_command = self._db_commands["message select"].format(chat, author, text)
        row = self._get_from_db(select_message_command, convert_to_json=True)
        self._connection.commit()
        return row

    def _check_chats_existence(self, chats_id):
        for id in chats_id:
            row = self._get_from_db(self._db_commands["chat by id select"].format(id))
            if not bool(row):
                return False
        return True

    def _check_user_in_chat_existence(self, chat_id, user_id):
        row = self._get_from_db(self._db_commands["user in chat select"].format(chat_id, user_id))
        return bool(row)

    def chats_get(self, user_id):
        if not self._check_users_existence([user_id]):
            raise ChatDbError("User does not exist")

        select_chats_command = self._db_commands["user in chat by user id select"].format(user_id)
        return self._get_from_db(select_chats_command, convert_to_json=True)

    def messages_get(self, chat_id):
        if not self._check_chats_existence([chat_id]):
            raise ChatDbError("Chat does not exist")

        select_messages_command = self._db_commands["message by chat id select"].format(chat_id)
        return self._get_from_db(select_messages_command, convert_to_json=True)


