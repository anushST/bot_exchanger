from decouple import config

DB_LINK = config('DB_LINK')
TOKEN = config('TOKEN')
ADMINS = [int(admin_id) for admin_id in config('ADMINS').split(',')]
TIMEZONE = 'Europe/Moscow'
FFIO_APIKEY = config('FFIO_APIKEY')
FFIO_SECRET = config('FFIO_SECRET')


class KeyboardCallbackData:
    START = "start"
    CANCEL = "cancel"
    CHANGE_LANGUAGE = "change_lang"
    SET_LANGUAGE = "set_lang_"

    EXCHANGE_CREATE = "exchange_create"
    EXCHANGE_CONFIRM = "exchange_confirm"
    EXCHANGE_FIX_RATE = "exchange_fix_rate"
    EXCHANGE_FLOAT_RATE = "exchange_float_rate"

    FAQ = "faq"
    FAQ_QUESTION = "faq_question_"

    @staticmethod
    def get_faq_question(question_id):
        return KeyboardCallbackData.FAQ_QUESTION + str(question_id)
