from dataclasses import dataclass

@dataclass
class BotMessages:
    start: str = "Привіт! Я бот для парсингу {}"
    add_product_first_step: str = "Введи посилання на товар iз сайту {}"
    add_product_second_step: str = "➕ Тепер я слiдкую за товаром:\n{}\n\n- Назва: {}\n- Оптова ціна: {}\n{}- Рекомендована роздрібна ціна: {} грн\n- Наявність: {}"
    add_product_second_step_fail: str = "Ой! Сталася помилка, перевір посилання та спробуй ще раз."
    optional_discount_string: str = "- Оптова ціна зі знижкою: {} грн\n"
    set_time_first_step: str = "О котрiй менi краще перевiряти товари?\n\nЗараз це {}"
    set_time_second_step_fail: str = "Перевiр формат вводу. Повинно бути два числа з двукрапкою: 19:00, 20:00...\n\nЗапусти команду /time ще раз та введи час у потрiбному форматi"
    set_time_second_step_success: str = "Добре, заводжу годинник на {}:{}!\n\nЧекай апдейти по товарам ⭐"
    remove_product_first_step: str = "🔗 Вiдправ посилання на продукт, який хочеш видалити"
    remove_product_second_step_success: str = "Товар з id {} бiльше не вiдслiдковується 👌"
    remove_product_second_step_fail: str = "Я не змiг дiстати iнфу по цьому товару, вибач 😭"
    info: str = "👷‍♂️ Звiтую про роботу"
    info_string: str = "1. Зараз я слiдкую за {} товарами 🔍\n2. Я надсилаю тобi апдейти у {} ⌚"
    help: str = f"⭐ Усі команди бота\n\n/start - Старт\n/add - Додати товар\n/remove - Видалити товар\n/info - Звiт про роботу\n/time - Задати час парсингу"
    scheduler_start_parsing: str = "✅ Прийшов час перевiрити товари на сайтi...\n\nЦе займе хвилинку-двi. Я сповiщу по завершенню!"
    scheduler_parse_string_start: str = "Характеристики товару {} змінились:\n{}\n\n"
    scheduler_parse_string_add: str = "{} товару змінилась.\nРаніше: {}\nЗараз: {}\n\n"
    scheduler_parse_string_no_changes: str = "🤙 Я все перевiрив! Товари не змінились"
    parse_final: str = "🕵️‍♂️ Я перевiрив всi товари! Бiльше нiяких змiн"

    product_not_found: str = "❌ На жаль, такого товару немає на сайтi!"

messages = BotMessages()