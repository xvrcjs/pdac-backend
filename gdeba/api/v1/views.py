import base64
from datetime import datetime, timezone
import io
import json
import os
from django.utils.timezone import localtime
from babel.dates import format_datetime
from datetime import datetime
from babel import Locale
from django.conf import settings
from django.http import HttpResponseBadRequest,HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from administration.models import Omic, TrafficLightSystemTimes
from claims.models import ClaimIVE, ClaimRegular, Claimer, File, Supplier
from tickets.models import Ticket
from common.communication.utils import send_email
from common.models import BaseModel
from common.views import BaseView
from users.models import Account
from django.core.files.uploadedfile import TemporaryUploadedFile
from django.db import transaction
from django.db.models.functions import ExtractMonth
from django.db.models import Count

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from textwrap import wrap  # Para dividir texto largo en líneas
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.graphics import renderPDF
locale = Locale('es', 'AR')


import requests
from zeep import Client
from zeep.transports import Transport
from requests import Session
from django.conf import settings
from django.core.cache import cache

class GdebaService:
    def __init__(self):
        self.base_url = settings.GDEBA_IOP_BASE_URL.rstrip('/')
        self.username = settings.GDEBA_USERNAME
        self.password = settings.GDEBA_PASSWORD
        self.jwt_url = f"{self.base_url}/servicios/JWT/1/REST/jwt"
        self.wsdl_url = f"{self.base_url}/servicios/GDEBA/1/SOAP"
        self.gedo_service_url = f"{self.base_url}/servicios/GDEBA/1/SOAP/generacionDocumentos?wsdl"

    def get_jwt_token(self):
        """Obtiene un token JWT de GDEBA. Primero intenta obtenerlo del cache."""
        cached_token = cache.get('gdeba_jwt_token')
        if cached_token:
            return cached_token

        try:
            response = requests.post(
                self.jwt_url,
                json={
                    "usuario": self.username,
                    "contrasena": self.password
                }
            )
            response.raise_for_status()
            token = response.json().get('token')
            
            # Guardar el token en cache por 50 minutos (el token dura 1 hora)
            cache.set('gdeba_jwt_token', token, 60 * 50)
            
            return token
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error al obtener token JWT: {str(e)}")

    def get_soap_client(self):
        """Crea un cliente SOAP con el token JWT en los headers"""
        token = self.get_jwt_token()
        
        session = Session()
        session.headers.update({
            'Authorization': f'Bearer {token}'
        })
        
        transport = Transport(session=session)
        return Client(wsdl=self.gedo_service_url, transport=transport)

    def generate_gedo(self, data):
        """Genera un documento GEDO"""
        try:
            client = self.get_soap_client()
            result = client.service.generarDocumento(request=data)
            return result
        except Exception as e:
            raise Exception(f"Error al generar GEDO: {str(e)}")

from PyPDF2 import PdfMerger
import base64
from claims.models import ClaimRegular

class GenerateGedoView(BaseView):
    model = ClaimRegular

    def post(self, request, *args, **kwargs):
        try:
            # Obtener el reclamo
            claim_uuid = kwargs.get('uuid')
            claim = ClaimRegular.objects.get(uuid=claim_uuid)

            # Generar el PDF del reclamo
            pdf_buffer = io.BytesIO()
            pdf = canvas.Canvas(pdf_buffer, pagesize=A4)
            width, height = A4

            # Primera página
            pdf.drawImage("common/templates/claim/reclamo-comun-1.png", 0, 0, width=width, height=height)
            
            # Datos del reclamo
            margin_top = 50
            y_position = height - margin_top
            
            # ID y fecha
            pdf.setFont("Helvetica", 8)
            pdf.drawString(440, y_position-2, str(claim.id))
            pdf.drawString(473, y_position-11, format_datetime(claim.created_at, format="dd/MM/yyyy"))

            y_position -= 28
            # Datos del solicitante
            pdf.setFont("Helvetica", 10)
            pdf.drawString(50, y_position-58, claim.claimer.fullname)
            pdf.drawString(50, y_position-106, claim.claimer.dni)
            pdf.drawString(50, y_position-151, claim.claimer.cuit or '')
            pdf.drawString(50, y_position-198, claim.claimer.email)

            # Segunda página
            pdf.showPage()
            pdf.drawImage("common/templates/claim/reclamo-comun-2.png", 0, 0, width=width, height=height)
            
            # Descripción del problema
            y_position = height - 120
            pdf.setFont("Helvetica", 8)
            pdf.drawString(440, y_position+68, str(claim.id))
            pdf.drawString(473, y_position+58, format_datetime(claim.created_at, format="dd/MM/yyyy"))
            
            wrapped_text = wrap(claim.problem_description, 100)
            for line in wrapped_text:
                pdf.drawString(50, y_position, line)
                y_position -= 15

            pdf.save()
            pdf_buffer.seek(0)

            # Crear un merger de PDFs
            merger = PdfMerger()
            merger.append(pdf_buffer)

            # Agregar los archivos adjuntos que sean PDFs
            for file in claim.files.all():
                if file.file_name.lower().endswith('.pdf'):
                    merger.append(file.file.path)

            # Crear un buffer para el PDF combinado
            output_buffer = io.BytesIO()
            merger.write(output_buffer)
            merger.close()

            # Convertir el PDF a base64
            output_buffer.seek(0)
            
            # Si es preview, devolver el PDF directamente
            if request.GET.get('preview') == 'true':
                response = HttpResponse(output_buffer.getvalue(), content_type='application/pdf')
                response['Content-Disposition'] = f'inline; filename="reclamo_{claim.id}_preview.pdf"'
                return response
            
            # Si no es preview, continuar con la generación del GEDO
            archivo_b64 = base64.b64encode(output_buffer.read()).decode('utf-8')

            # Generar el GEDO
            # gdeba_service = GdebaService()
            # result = gdeba_service.generate_gedo({
            #     "acronimoTipoDocumento": "MEMO",
            #     "data": archivo_b64,
            #     "idTransaccion": str(claim.id),
            #     "usuario": settings.GDEBA_USERNAME,
            #     "tipoArchivo": "application/pdf",
            #     "metaDatos": {
            #         "entry": [
            #             {"key": "asunto", "value": f"Reclamo N° {claim.id}"},
            #             {"key": "urgente", "value": "no"},
            #         ]
            #     },
            #     "listaUsuariosDestinatarios": [settings.GDEBA_USERNAME]
            # })
            
            return JsonResponse({
                'success': True,
                'data': result
            })
        except ClaimRegular.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Reclamo no encontrado'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            }, status=400)