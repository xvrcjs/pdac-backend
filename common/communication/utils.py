from email.mime.image import MIMEImage
import os
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
import logging
import smtplib
from django.template.loader import get_template

logger = logging.getLogger(__name__)

def send_email(email_address, subject, body):
    """
    Sends an email to an address.

    :param email_address: The address to send the email.
    :param subject: The subject of the email.
    :param body: The body of the email.
    :return: Tuple with (Successful, Message ID).
    """

    if not settings.EMAIL_SENDER_ENABLED:
        logger.error('Will not send email "%s" to %s. Email Sender are disabled.' % (subject, email_address))
        template = get_template('communication/send_email.html')
        rendered_template = template.render({'body': body})

        email = EmailMultiAlternatives(
            subject,
            '',
            settings.EMAIL_HOST_USER,
            [email_address]
        )
        email.attach_alternative(rendered_template, 'text/html')
        email.send()
        
        return (False, '')
    try:
        template = get_template('communication/send_email.html')
        rendered_template = template.render({'body': body})

        email = EmailMultiAlternatives(
            subject,
            '',
            settings.EMAIL_HOST_USER,
            [email_address]
        ) 
        email.attach_alternative(rendered_template, 'text/html')
        
        image_path = 'static/logo.png'
        with open(image_path, 'rb') as f:
            logo_image = MIMEImage(f.read())
            logo_image.add_header('Content-ID', '<logo_image>')
            logo_image.add_header('Content-Disposition', 'inline', filename='logo.png')
            email.attach(logo_image)
        email.send()

    except Exception as e:
        logger.error(str(e))
    return (False, None)