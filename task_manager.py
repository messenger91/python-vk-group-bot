from commander import Commander
from library.vk import VkBotMessanger
from models.Ban import BanModel
from models.Command import CommandModel, CommandType
from models.Content import ContentModel
from models.Reward import RewardModel
from models.User import UserModel
from models.Warning import WarningModel
from helpers import current_datetime, get_date_ago, get_number_from_string, list_get
import traceback

# models
command_datasource = CommandModel()
content_datasource = ContentModel()
user_datasource = UserModel()
WarningDataSource = WarningModel()
BanDataSource = BanModel()
reward_datasource = RewardModel()

group_users = user_datasource.get_user_ids_map()


class TaskManager:
    def __init__(self, bot_messanger: VkBotMessanger) -> None:
        self.__bot_messanger = bot_messanger
        self.__group_users = group_users

    def process_text(self, commander: Commander) -> None:
        
        # Обновляем время последнего сообщения у пользователя и обновляем счетчик сообщений
        user_datasource.update_user_messages(commander.from_id)

        exist = self.__group_users.get(commander.from_id)

        user_info = self.__bot_messanger.user_info(commander.from_id)

        if (not exist):
            user_datasource.createByUserInfo(commander.from_id, user_info)
            self.__group_users = user_datasource.get_user_ids_map()

        if (commander.from_reply_id and commander.text.lower() in user_datasource.add_reputation_words.split()):

            if (commander.from_reply_id != commander.from_id):
                user_datasource.add_reputation(commander.from_reply_id)
                self.__bot_messanger.send_message(
                    commander.peer_id, 'Репутация повышена!')
            else:
                self.__bot_messanger.send_message(
                    commander.peer_id, 'Нельзя повышать себе репутацию!')

        if (commander.from_reply_id and commander.text.lower() in user_datasource.remove_reputation_words.split()):

            if (commander.from_reply_id != commander.from_id):
                user_datasource.remove_reputation(commander.from_reply_id)
                self.__bot_messanger.send_message(
                    commander.peer_id, 'Репутация понижена!')
            else:
                user_datasource.remove_reputation(commander.from_reply_id)
                self.__bot_messanger.send_message(
                    commander.peer_id, 'Самоосуждение одобряем! Репутация понижена')

        isHyperLink = False

        if (commander.attachments):

            for attachment in commander.attachments:
                if (attachment['type'] == 'link'):
                    isHyperLink = True

        if (commander.text):
            if (commander.text.find('http://') != -1 or commander.text.find('https://') != -1):
                isHyperLink = True

        if (commander.text):
            alias_command = command_datasource.findone(
                [{'field': 'alias', 'value': f'{commander.text}'.lower()}])

            if (alias_command):
                commander.cmd = alias_command.get('name')
                commander.is_command = True
                TaskManager.process_command(self, commander)

        if (isHyperLink):
            self.__bot_messanger.send_message(
                commander.peer_id, 'Ссылки запрещены. Пока прощай')
            self.__bot_messanger.removeChatUser(commander.peer_id, commander.from_id)
            self.__bot_messanger.delete_message(
                commander.group_id, commander.peer_id, f'{commander.message_id}', f'{commander.conversation_message_id}')

    def process_command(self, commander: Commander):

        # Обновляем время последнего сообщения у пользователя и обновляем счетчик сообщений
        user_datasource.update_user_messages(commander.from_id)

        text = None
        attachment = None
        is_user_admin = False
        is_user_editor = False
        is_user_moderator = False
        send_message_params = { 'disable_mentions': 1 }

        user = user_datasource.findbypk(commander.from_id)

        if (user != None and user.get('level') == 4):
            is_user_admin = True

        if (user != None):
            is_user_editor = user.get('editor')
            is_user_moderator = user.get('moderator')

        if (commander.is_command):
            command = command_datasource.findbypk(commander.cmd)

            if (command == None):
                return

            if (command.get('action_type') == command_datasource.ACTION_TYPES.get('get_command')):
                text = command.get('text')
                attachment = command.get('attachment')

            if (command.get('action_type') == command_datasource.ACTION_TYPES.get('find_commands')):
                text = command_datasource.find_commands()

            if (command.get('action_type') == command_datasource.ACTION_TYPES.get('get_content')):
                key = command_datasource.get_custom_key(
                    command, commander) or commander.value or commander.cmd
                content = content_datasource.find_by_command_id(
                    key, command.get('id'))
                if (content):
                    text = content.get('text')
                    attachment = content.get('attachment')
                else:
                    text = command.get('text')
                    attachment = command.get('attachment')

            if (command.get('action_type') == command_datasource.ACTION_TYPES.get('add_content')):
                key = commander.from_id
                command_id = command.get('bind_id') or command.get('id')

     
                attachment = commander.get_photos_links or ''
                print('attachment', attachment)
                self.__create_or_update_content(key, command_id, commander.data, attachment)

                text = command.get('text')
                attachment = command.get('attachment')

            if (command.get('action_type') == command_datasource.ACTION_TYPES.get('create_content')):
                if (is_user_editor == False):
                    text = command.get('text')
                else:
                    try:
                        upd_command = command_datasource.findbypk(
                            commander.line_args[1].strip())
                        content_key = commander.line_args[2].strip()
                        content_text = None
                        content_attachment = None

                        if (list_get(commander.line_args, 4)):
                            content_text = list_get(
                                commander.line_args, 4).strip()

                        if (list_get(commander.line_args, 3)):
                            content_attachment = list_get(
                                commander.line_args, 3).strip()

                        update_options = {}
                        if (content_text):
                            update_options['text'] = content_text

                        if (content_attachment):
                            update_options['attachment'] = content_attachment

                        where_options = [{'field': 'command_id', 'value': upd_command.get('id')}, {
                            'field': 'key', 'value': content_key}]

                        content_datasource.update(
                            where_options, update_options)
                        text = command.get('success')
                    except:
                        traceback.print_exc()
                        text = command.get('fail')

            if (command.get('action_type') == command_datasource.ACTION_TYPES.get('update_content')):
                if (is_user_editor == False):
                    text = command.get('text')
                else:
                    try:
                        update_string = list_get(
                            commander.line_args, 1).strip()
                        print('update_string', update_string)

                        cmd = update_string.split(' ')[0]
                        print('cmd', cmd)

                        text = commander.data[len(update_string)+2:]
                        print('text', text)

                        attachment = commander.get_photo_link
                        print('attachment', attachment)

                        update_command = command_datasource.findbypk(cmd)

                        print('update_command', update_command)

                        content_key = update_string[len(cmd):].strip() or cmd
                        print('content_key', content_key)

                        
                        update_options = {}
 
                        if (update_command.get('action_type') == command_datasource.ACTION_TYPES.get('get_command')):
                            self.__update_command(update_command.get('id'), text, attachment)

                        if (update_command.get('action_type') == command_datasource.ACTION_TYPES.get('get_content')):
                            self.__create_or_update_content(content_key, update_command.get('id'), text, attachment)

                        text = command.get('success')
                    except:
                        traceback.print_exc()
                        text = command.get('fail')

            if (command.get('action_type') == command_datasource.ACTION_TYPES.get('find_contents')):
                text = content_datasource.find_contents(
                    {'field': 'command_id', 'value': command.get('id')})

            if (command.get('action_type') == command_datasource.ACTION_TYPES.get('create_warn')):
                if (is_user_moderator == False):
                    text = command.get('text')
                else:
                    reason = f"'{commander.value}'"
                    user_id = command_datasource.get_custom_key(
                        command, commander)

                    data = WarningDataSource.create_warn(user_id, reason)
                    text = command.get('success')

            if (command.get('action_type') == command_datasource.ACTION_TYPES.get('create_ban')):
                if (is_user_moderator == False):
                    text = command.get('text')
                else:
                    reason = f"'{commander.value}'"
                    user_id = command_datasource.get_custom_key(
                        command, commander)
                    data = BanDataSource.create_ban(user_id, reason)
                    try:
                        self.__bot_messanger.ban(commander.peer_id, user_id)
                        text = command.get('success')
                        attachment = command.get('attachment')
                    except Exception as e:
                        text = command.get('fail')

            if (command.get('action_type') == command_datasource.ACTION_TYPES.get('delete_warn')):
                if (is_user_moderator == False):
                    text = command.get('text')
                else:

                    user_id = command_datasource.get_custom_key(
                        command, commander)

                    data = WarningDataSource.delete_warn(user_id)
                    text = command.get('success')

            if (command.get('action_type') == command_datasource.ACTION_TYPES.get('user_warn')):
                text = content_datasource.find_contents(
                    {'field': 'command_id', 'value': command.get('id')})

                user_id = command_datasource.get_custom_key(command, commander)
                data = WarningDataSource.find_user_warn(user_id)
                if (data):
                    text = data
                else:
                    text = command.get('text')

            if (command.get('action_type') == CommandType.PROFILE.value):
                user = user_datasource.findbypk(
                    commander.from_reply_or_from_id)
                text = command.get('template') % user

            if (command.get('action_type') == 0):
                return

            if (command.get('action_type') == CommandType.UPDATE_NICKNAME.value):
                user_datasource.update_nickname(
                    commander.from_id, commander.value)
                text = command.get('success')

            if (command.get('action_type') == CommandType.UPDATE_BIO.value):
                update_options = {}

                if (commander.data):
                    update_options['bio'] = commander.data

                user_datasource.update(
                    [{'field': 'user_id', 'value': commander.from_id}], update_options)
                text = command.get('success')

            if (command.get('action_type') == CommandType.ADD_REWARD.value):
                user_id = commander.args[1].split('|')[0][3:]
                reward_name = ' '.join(commander.args[2:])
                reward_datasource.add_reward(user_id, reward_name)

                text = command.get('success')

            if (command.get('action_type') == CommandType.REMOVE_REWARD.value):
                user_id = commander.args[1].split('|')[0][3:]
                reward_name = ' '.join(commander.args[2:])
                reward_datasource.remove_reward(user_id, reward_name)

                text = command.get('success')

            if (command.get('action_type') == CommandType.REWARDS.value):
                user_id = commander.from_reply_or_from_id
                user = user_datasource.findbypk(user_id)
                rewards = reward_datasource.user_rewards(
                    user_id, user.get('nickname'))

                if (rewards):
                    text = rewards
                else:
                    text = command.get('text')

            if (command.get('action_type') == CommandType.USER_STATS.value):
                members = self.__bot_messanger.chat_members(commander.peer_id)
                text = user_datasource.get_user_stats(members)
                
            if (command.get('action_type') == CommandType.SILENT_USERS.value):
                members = self.__bot_messanger.chat_members(commander.peer_id)
                stat = user_datasource.get_silent_users(members)
                if (stat):
                    text = stat
                else:
                    text = command.get('text')

            if (command.get('action_type') == CommandType.INACTIVE_USERS.value):
                days = get_number_from_string(commander.value or '3')
                
                if (days < 3): days = 3

                date = get_date_ago(days)
               
                members = self.__bot_messanger.chat_members(commander.peer_id)
                data = user_datasource.show_inactive_users(members, date)
            
                if (data):
                    text = data
                    userIds = user_datasource.get_inactive_users(members, date)
                    user_datasource.remove_users(userIds)
                    self.__bot_messanger.batchRemoveChatUsers(commander.peer_id, userIds)

                else:
                    text = command.get('text')

            if (command.get('action_type') == 0):
                return

        if (text or attachment):
            self.__bot_messanger.send_message(
                commander.peer_id, text, attachment, send_message_params)
        else:
            print('[WARNING] Attempt to send empty text or attachment')


    def __send_message(self, peer_id, text, attachment, params):
          self.__bot_messanger.send_message(peer_id, text, attachment, params)

    def __create_or_update_content(self, key, command_id, text, attachment) -> None:
    
        exist = content_datasource.find_by_command_id(key, command_id)
     
        if (exist):
            where_options = [{'field': 'key', 'value': key }, {'field': 'command_id', 'value': command_id }]
            update_options = { 'updated_at': current_datetime() }

            if (text):
                update_options['text'] = text
            if (attachment):
                update_options['attachment'] = attachment

            content_datasource.update(where_options, update_options)
        else: 
            content_datasource.create_from_key(key, command_id, text, attachment)

    def __update_command(self, command_id, text, attachment) -> None:
        where_options = [{'field': 'id', 'value': command_id }]
        update_options = {}

        if (text):
            update_options['text'] = text
        if (attachment):
            update_options['attachment'] = attachment
        
        command_datasource.update(where_options, update_options)