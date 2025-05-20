import telebot

class ExceptionHandler(telebot.ExceptionHandler):
    def handle(self, exception):
        print("Exception occured: ", exception)