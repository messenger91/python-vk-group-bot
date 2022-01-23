import sqlite3
from sqlite3 import Connection
from action import ActionType
import config

class Db:
    def __init__(self) -> None:
        self.__connection: Connection = sqlite3.connect(config.database)

    def query(self, sql, mode: str = None):
        cursor = self.__connection.cursor()
        cursor.execute(sql)
        if (mode == 'fetchone'):
            return cursor.fetchone()
        if (mode == 'fetchall'):
            return cursor.fetchall()
        if (mode == 'insert'):
           self.__connection.commit()

class Datasource:
    def __init__(self, db: Db) -> None:
        self.__db = db

    def get_command(self, command_name: str):
        sql = f'select * from commands where name = "{command_name}"'
        row = self.__db.query(sql, mode='fetchone')
        return row

    def create_content(self, content_key: str, action_type: int, data: str):
        sql = f'insert into contents (key, action_type, text, created_at, updated_at) values ({content_key}, {action_type}, "{data}", CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);'
        row = self.__db.query(sql, mode='insert')
        return row

    def get_content(self, content_key: str, action_type: int):
        sql = f'select key, action_type, text, attachment from contents where action_type = {action_type} and key = \'{content_key.lower()}\' order by created_at desc'
        row = self.__db.query(sql, mode='fetchone')
        return row

    def get_action_type_by_command(self, command_name: str) -> str:
        sql = f'SELECT action_type FROM commands WHERE name = "{command_name}"'
        row = self.__db.query(sql, mode='fetchone')
        if (row):
            return row[0]
        else:
            return 0

    def find_commands(self):
        sql = f'select action_type, name, help from commands order by action_type asc'
        rows = self.__db.query(sql, mode='fetchall')
        return rows
    
    def query_by_task(self, task):
        if (task['datasource'] == 'find_commands'):
            return self.find_commands()
        if (task['datasource'] == 'get_content'):
            return self.get_content(task['content_key'], task['action_type'])
        if (task['datasource'] == 'create_content'):
            return self.create_content(task['content_key'], task['action_type'], task['data'])

class DataMapper(object):
    @staticmethod
    def get_help(rows: list):
        commands = ['Список комманд бота:']
        for row in rows:
            commands.append(f'\n{row[1]} - {row[2]}')
        return ''.join(commands)


    @staticmethod
    def get_text(row: list):
        text = ''
        if (row[2]):
            text= row[2]

        return text

    @staticmethod
    def get_attachment(row: list):
        attachment = ''
        if (row[3]):
            attachment= row[3]

        return attachment

    @staticmethod
    def mapping_by_action_type(task, data):
        if (task['datasource'] == 'create_content'):
            return None

        action_type = task['action_type']
        mapper = { 'data': None, 'type': None }

        if (action_type == ActionType.HELP.value):
            help = DataMapper.get_help(data)
            mapper.update(data = help)
            mapper.update(type = 'message')
            return mapper
            
        if (action_type == ActionType.GUIDE.value):
            
            if (data):
                attachment = DataMapper.get_attachment(data)
                text = DataMapper.get_text(data)
                
                mapper.update(type = 'message')
                mapper.update(data = text)
                
                if (attachment):
                    mapper.update(data = attachment)
                    mapper.update(type = 'attachment')
            else:
                mapper.update(data = 'Гайд не найден')
                mapper.update(type = 'message')
            return mapper

        if (action_type == ActionType.WORKSHEET.value):
   
            if (data):
                text = DataMapper.get_text(data)
                
                mapper.update(type = 'message')
                mapper.update(data = text)
            else:
                mapper.update(data = 'Анкета не найдена')
                mapper.update(type = 'message')
            return mapper

        if (action_type == ActionType.ALERT.value):
        
            if (data):
                text = DataMapper.get_text(data)
                
                mapper.update(type = 'message')
                mapper.update(data = text)
            else:
                mapper.update(data = 'записей об админах нет')
                mapper.update(type = 'message')
            return mapper

        if (action_type == ActionType.LEVELING.value):
            if (data):
                attachment = DataMapper.get_attachment(data)
                text = DataMapper.get_text(data)
                
                mapper.update(type = 'message')
                mapper.update(data = text)
                
                if (attachment):
                    mapper.update(data = attachment)
                    mapper.update(type = 'attachment')
            else:
                mapper.update(data = 'Гайд не найден')
                mapper.update(type = 'message')
            return mapper

        if (action_type == ActionType.FARMING.value):
            if (data):
                attachment = DataMapper.get_attachment(data)
                text = DataMapper.get_text(data)

                mapper.update(type = 'message')
                mapper.update(data = text)

                if (attachment):
                    mapper.update(data = attachment)
                    mapper.update(type = 'attachment')
            else:
                mapper.update(data = 'День недели введен не корректно!')
                mapper.update(type = 'message')
                
            return mapper

        if (action_type == ActionType.FARMING_TODAY.value):
            if (data):
                attachment = DataMapper.get_attachment(data)
                text = DataMapper.get_text(data)
                
                mapper.update(type = 'message')
                mapper.update(data = text)
                
                if (attachment):
                    mapper.update(data = attachment)
                    mapper.update(type = 'attachment')
            else:
                mapper.update(data = 'День недели введен не корректно!')
                mapper.update(type = 'message')
            return mapper

        return None