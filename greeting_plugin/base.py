# -*- coding: utf-8 -*-
from marvinbot.plugins import Plugin
from marvinbot.utils import trim_markdown
from marvinbot.handlers import CommandHandler, CommonFilters, MessageHandler
from jinja2 import Template

from greeting_plugin.models import ChatGreeting, ChatMemberGreeting
import logging

log = logging.getLogger(__name__)

class GreetingPlugin(Plugin):
    def __init__(self):
        super(GreetingPlugin, self).__init__('greeting_plugin')

    def get_default_config(self):
        return {
            'short_name': self.name,
            'enabled': True,
        }

    def configure(self, config):
        pass

    def setup_handlers(self, adapter):
        self.add_handler(CommandHandler('greeting', self.on_greeting_command, command_description='Allows the user to set the greeting on a group chat.')
            .add_argument('--remove', help='Remove greeting', action='store_true'))
        self.add_handler(MessageHandler([CommonFilters.status_update.left_chat_member], self.on_left_chat_member))
        self.add_handler(MessageHandler([CommonFilters.status_update.new_chat_members], self.on_new_chat_members))

    def setup_schedules(self, adapter):
        pass

    def provide_blueprint(self, config):
        pass

    def on_greeting_command(self, update, **kwargs):
        message = update.effective_message
        chat_id = message.chat.id
        user_id = message.from_user.id
        remove_greeting = kwargs.get('remove')

        greeting = ChatGreeting.by_chat_id(chat_id)

        if remove_greeting:
            if greeting:
                greeting.delete()
                message.reply_text(text='🗑 Greeting removed.')
            else:
                message.reply_text(text='❌ Not possible')
            return

        replying = bool(message.reply_to_message)
        if not replying:
            greeting = ChatGreeting.by_chat_id(chat_id)
            self.send_greeting(chat_id, greeting, [message.from_user])
            return

        if not self.can_user_change_info(message, user_id):
            message.reply_text(text='❌ You are not allowed to do that.')
            return

        reply_has_text = bool(message.reply_to_message.text)
        if not reply_has_text:
            message.reply_text(text="❌ Use /greeting when replying to a message containing text.")
            return

        fields = {
            'chat_id': chat_id,
            'greeting_text': message.reply_to_message.text,
            'user_id': user_id,
            'username': message.from_user.username,
        }

        if greeting:
            greeting.delete()

        try:
            template = Template(message.reply_to_message.text)
            template.render(names='test')
        except:
            message.reply_text(text='❌ Invalid format.')
            return

        if not self.add_greeting(**fields):
            message.reply_text(text='❌ Unable to add greeting.')
            return

        message.reply_text(text='✅ Greeting added.')

    def interpolate(self, greeting_text, users):
        names = [GreetingPlugin.user_link(user) for user in users]
        template = Template(greeting_text)
        return template.render(names=', '.join(names))

    def send_greeting(self, chat_id, greeting, users):
        names = [GreetingPlugin.user_link(user) for user in users]
        greeting_text = self.interpolate(greeting.greeting_text, users) if greeting is not None else 'Welcome {}'.format(', '.join(names))
        self.adapter.bot.sendMessage(
            chat_id=chat_id,
            text=greeting_text,
            parse_mode='Markdown')

    def on_left_chat_member(self, update):
        message = update.effective_message
        user = GreetingPlugin.user_link(message.left_chat_member)

        message.reply_text(text='Good bye {}'.format(user), parse_mode='Markdown')

    def on_new_chat_members(self, update):
        message = update.effective_message
        chat_id = message.chat.id
        greeting = ChatGreeting.by_chat_id(chat_id)
        self.send_greeting(chat_id, greeting, message.new_chat_members)

    def can_user_change_info(self, message, user_id):
        member = message.chat.get_member(user_id=user_id)
        return message.chat.all_members_are_administrators \
            or member.status == 'creator' \
            or (member.status == 'administrator' and member.can_change_info)

    @staticmethod
    def add_greeting(**kwargs):
        try:
            greeting = ChatGreeting(**kwargs)
            greeting.save()
            return True
        except Exception as ex:
            log.error(ex)
            return False

    @staticmethod
    def user_link(user):
        first_name = trim_markdown(user.first_name)
        last_name = trim_markdown(user.last_name) if user.last_name is not None else None
        return "[{name}](tg://user?id={id})".format(
            name='{} {}'.format(first_name, last_name) if last_name is not None else first_name,
            id=user.id)
