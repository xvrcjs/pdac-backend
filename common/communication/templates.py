from django.conf import settings


class _BaseMessageTemplate:

    def __init__(self, subject=None, html_message=None, text_message=None):
        self.subject = subject
        self.html_message = html_message
        self.text_message = text_message


# USERS
user_create_password_message = _BaseMessageTemplate(
   'Bienvenido a %s'% settings.SITE_NAME,
    "<div style='font-family: Barlow,sans-serif;display: flex;background-color: #24649D;padding: 1rem;'><div style='background-color: #fff;padding: 1.5rem 3.5rem 3.5rem 3.5rem;margin:auto;'><h1 style='font-size: 2.3rem;font-weight: 500;'>Hello {{first_or_display_name}},</h1><p style='font-size: 1.1rem;margin-top: 0.4rem;margin-bottom: 0.4rem'><br />We have received a request to create an account for you.<br /> <strong>Click on this link to create your password:</strong><br /><a href={{link}}>Create password</a></p><p style='font-size: 1.1rem;margin-top: 0.4rem;margin-bottom: 0.4rem'><br />If you didn't initiate this request, please ignore and/or delete this email.</p><p style='font-size: 1.1rem;margin-top: 0.4rem;margin-bottom: 0.4rem'>This link is valid for <strong>%s hours.</strong></p><p style='font-size: 1.1rem;margin-top: 0.4rem;margin-bottom: 0.4rem'><br /><small>--<br /></small></p></div></div>"% settings.RESET_PASSWORD_EXP
)

user_reset_password_message = _BaseMessageTemplate(
    'Bienvenido a  %s'% settings.SITE_NAME,
    "<!DOCTYPE html><html><head><meta charset='utf-8'><meta http-equiv='X-UA-Compatible' content='IE=edge'><meta name='viewport' content='width=device-width, initial-scale=1'><style>@import url('https://fonts.googleapis.com/css2?family=Inter:wght@100..900&display=swap');</style></head><body><div style='font-family:Inter, Gotham, Monserrat, helvetica; display: flex;background-color: #F7F7FF;padding: 1rem;'><table style='margin: 0 auto'><thead><tr><td><h3 style='font-size: 32px; font-style: normal; font-weight: 600; line-height: normal; color: #303048; text-align: center;'>Restablecer Contraseña</h3></td></tr></thead><tbody><tr><td style='text-align: center;'><img style='max-width: 310px; margin-bottom: 60px; margin-top: 26px;' src=cid:logo_image alt='Logo' /></td></tr><tr><td style='text-align: center;'><h5 style='color:  #303048; font-size: 24px; font-style: normal; font-weight: 600; line-height: normal; margin: 0;'>¿Olvidaste tu contraseña?</h5></td></tr><tr><td style='text-align: center;'><p style='color: #68688C;font-size: 28px; font-style: normal; font-weight: 500; line-height: normal; margin-top: 46px; margin-bottom: 46px;'>Para restablecer tu contraseña haz click en el siguiente enlace</p></td></tr><tr><td style='text-align: center;'><a href={{link}} style='border-radius: 40px; background-color: #004DEF; padding: 12px 30px; display: inline-flex; justify-content: center; align-items: center; text-decoration: none; color: #FFF; text-transform: uppercase; font-size: 14px; font-style: normal; font-weight: 600; line-height: normal;'>Restablecer contraseña</a></td></tr></tbody><tfoot><tr><td style='text-align: center;'> <p style='color: #303048; font-size: 20px; font-style: normal; font-weight: 500; line-height: normal; margin-top: 46px;'> Si tu nos has solicitado restablecer tu contraseña, desestima este email.</p></td></tr></tfoot></table></div></body></html>"
)
