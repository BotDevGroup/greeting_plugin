import mongoengine
from marvinbot.utils import localized_date

class ChatGreeting(mongoengine.Document):
    chat_id = mongoengine.LongField(required=True)

    greeting_text = mongoengine.StringField(required=True)

    user_id = mongoengine.LongField(required=True)
    username = mongoengine.StringField()

    date_added = mongoengine.DateTimeField(default=localized_date)
    date_modified = mongoengine.DateTimeField(default=localized_date)
    date_deleted = mongoengine.DateTimeField(required=False, null=True)

    def __repr__(self):
        return self.greeting_text

    def __str__(self):
        return self.__repr__()

    @classmethod
    def by_chat_id(cls, chat_id):
        try:
            return cls.objects.get(chat_id=chat_id)
        except cls.DoesNotExist:
            return None
