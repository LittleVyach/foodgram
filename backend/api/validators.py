from django.core.validators import RegexValidator

validate_username = RegexValidator(
    regex=r'^[\w.@+-]+\Z',
    message='Имя пользователя содержит недопустимые символы.'
)
