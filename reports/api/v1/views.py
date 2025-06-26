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

class ReportClaims(BaseView):
    fields = ['id']
    model = ClaimRegular

    @csrf_exempt
    def dispatch(self, request, *args, **kwargs):
        if 'uuid' in kwargs:
            self.required_fields= {}
        return super().dispatch(request,*args,**kwargs)

    def data_list_json(self, query_set, fields, **kwargs):
        claims = super().data_list_json(query_set, fields, **kwargs)

        # Crear el buffer para el PDF
        pdf_buffer = io.BytesIO()
        pdf = canvas.Canvas(pdf_buffer, pagesize=A4)
        width, height = A4

        margin_top = 50  # Margen desde la parte superior
        y_position = height - margin_top  # Posición inicial de escritura
        
        # Crear y configurar el gráfico de pie
        drawing = Drawing(400, 200)
        pie = Pie()
        pie.x = 150
        pie.y = 0
        pie.width = 180
        pie.height = 180
        pie.data = [45, 25, 15, 10, 5]       # % de mercado
        pie.labels = ["Producto A","B","C","D","E"]
        pie.slices[0].popout = 10              # resaltar la mayor porción
        pie.slices[0].strokeWidth = 0
        pie.slices[0].fillColor = colors.HexColor("#ff7f0e")
        
        # Agregar el pie al drawing
        drawing.add(pie)
        
        # Dibujar el gráfico en el PDF
        renderPDF.draw(drawing, pdf, 50, 400)
        pdf.showPage()
        pdf.save()

        # Preparar la respuesta HTTP
        pdf_buffer.seek(0)
        response = HttpResponse(pdf_buffer.getvalue(), content_type='application/pdf')
        response['Content-Disposition'] = 'attachment; filename="report.pdf"'
        
        return response

class ReportGenerateClaims(BaseView):
    model = ClaimRegular
    fields = ['id','claim_access','type_of_claim','claim_status','category','heading','subheading','suppliers']
    list_fields_related = {
        "suppliers": ["fullname"],
    }
    def get(self, request, *args, **kwargs):
        # Obtener parámetros de filtrado y paginación
        start_date = request.GET.get('start_date')
        finish_date = request.GET.get('finish_date')
        filters = request.GET.get('filters')
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 10))

        # Iniciar el queryset base
        queryset = self.model.objects.all()

        # Aplicar filtro por fechas si se proporcionan
        if start_date and finish_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                finish_date = datetime.strptime(finish_date, '%Y-%m-%d')
                queryset = queryset.filter(created_at__range=(start_date, finish_date))
            except ValueError:
                return JsonResponse(
                    {'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}, 
                    status=400
                )

        # Aplicar filtros adicionales si se proporcionan
        if filters:
            try:
                filters_dict = json.loads(filters)

                # Manejar el caso especial del filtro de suppliers
                if 'suppliers' in filters_dict:
                    supplier_name = filters_dict.pop('suppliers')
                    # Usar un filtro por nombre de proveedor
                    queryset = queryset.filter(
                        suppliers__in=Supplier.objects.filter(fullname=supplier_name)
                    )
                # Aplicar el resto de los filtros
                if filters_dict:
                    queryset = queryset.filter(**filters_dict)
            except json.JSONDecodeError:
                return JsonResponse(
                    {'error': 'Formato de filtros inválido. Debe ser un JSON válido'}, 
                    status=400
                )
            except Exception as e:
                return JsonResponse(
                    {'error': f'Error al aplicar filtros: {str(e)}'}, 
                    status=400
                )

        # Calcular total de registros
        total_records = queryset.count()
        total_pages = (total_records + page_size - 1) // page_size

        # Aplicar paginación
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        queryset = queryset[start_idx:end_idx]

        # Serializar y retornar los datos
        data = self.data_list_json(queryset, self.fields)
        for claim in data:
            suppliers_names = [supplier['fullname'] for supplier in claim['suppliers']]
            claim['suppliers'] = ', '.join(suppliers_names)

        return JsonResponse({
            'data': data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_records': total_records,
                'total_pages': total_pages
            }
        }, status=200)

class ReportGenerateCharts(BaseView):
    model = ClaimRegular
    fields = ['id','claim_access','type_of_claim','claim_status','category','heading','subheading','suppliers']
   
    def generate_pie_chart(self,regular_claims,date_filter):
        hv_count = regular_claims.filter(type_of_claim__contains='HV -').count()
        common_count = regular_claims.filter(type_of_claim='Común - Común').count()
        unassigned_count = regular_claims.filter(claim_status='S/A').count()
        
        # Obtener estadísticas de reclamos HV por subcategoría
        hv_subcategories = {
            'nnya': regular_claims.filter(type_of_claim='HV - Por afectacion de derechos de NNyA').count(),
            'jubilados': regular_claims.filter(type_of_claim='HV - Jubilados o pensionados').count(),
            'estado_fisico': regular_claims.filter(type_of_claim='HV - Por estado físico o mental').count(),
            'ruralidad': regular_claims.filter(type_of_claim='HV - Por ruralidad').count(),
            'socioeconomico': regular_claims.filter(type_of_claim='HV - Por razones, sociales, económicas o culturales').count(),
            'turista': regular_claims.filter(type_of_claim='HV - Por turista').count(),
            'migrante': regular_claims.filter(type_of_claim='HV - Por migrante').count(),
            'lgbt': regular_claims.filter(type_of_claim='HV - Por colectivo LGTB+').count(),
            'pueblos_originarios': regular_claims.filter(type_of_claim='HV - Por pueblos originarios').count(),
            'mayores_70': regular_claims.filter(type_of_claim='HV - Mayores de 70años').count(),
            'otro': regular_claims.filter(type_of_claim='HV - Otro').count()
        }
        
        # Obtener estadísticas de reclamos IVE
        ive_claims = ClaimIVE.objects.filter(**date_filter).count()

        total_claims = hv_count + common_count + unassigned_count + ive_claims
        return {
            'total_claims': total_claims,
            'hv_claims': hv_count,
            'common_claims': common_count,
            'unassigned_claims': unassigned_count,
            'ive_claims': ive_claims,
            'hv_subcategories': hv_subcategories
        }

    def generate_bar_chart(self, regular_claims, date_filter):
        # Obtener el año actual si no hay filtro de fecha
        current_year = datetime.now().year
        if date_filter and 'created_at__range' in date_filter:
            current_year = date_filter['created_at__range'][0].year

        # Crear diccionario para almacenar conteos por mes
        monthly_data = {month: 0 for month in range(1, 13)}

        # Contar reclamos regulares por mes
        regular_by_month = regular_claims.filter(
            created_at__year=current_year
        ).annotate(
            month=ExtractMonth('created_at')
        ).values('month').annotate(
            count=Count('id')
        )

        for item in regular_by_month:
            monthly_data[item['month']] = item['count']

        # Convertir a formato para el gráfico
        months_names = [
            'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
            'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'
        ]

        bar_data = [
            {
                'name': months_names[month - 1],
                'value': count,
                'month': month
            }
            for month, count in monthly_data.items()
        ]

        # Ordenar por mes
        bar_data.sort(key=lambda x: x['month'])

        return {
            'data': bar_data,
            'year': current_year,
            'total_by_month': monthly_data
        }

    def get(self, request, *args, **kwargs):
        start_date = request.GET.get('start_date')
        finish_date = request.GET.get('finish_date')
        filters = request.GET.get('filters')
        
        # Preparar filtros de fecha
        date_filter = {}
        if start_date and finish_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                finish_date = datetime.strptime(finish_date, '%Y-%m-%d')
                date_filter = {'created_at__range': (start_date, finish_date)}
            except ValueError:
                return JsonResponse(
                    {'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}, 
                    status=400
                )

        # Obtener estadísticas de reclamos regulares
        regular_claims = self.model.objects.filter(**date_filter)
        
        # Aplicar filtros adicionales si se proporcionan
        if filters:
            try:
                filters_dict = json.loads(filters)
                
                # Manejar el caso especial del filtro de suppliers
                if 'suppliers' in filters_dict:
                    supplier_name = filters_dict.pop('suppliers')
                    # Usar un filtro por nombre de proveedor
                    regular_claims = regular_claims.filter(
                        suppliers__in=Supplier.objects.filter(fullname=supplier_name)
                    )
                # Aplicar el resto de los filtros
                if filters_dict:
                    regular_claims = regular_claims.filter(**filters_dict)
                    
            except json.JSONDecodeError:
                return JsonResponse(
                    {'error': 'Formato de filtros inválido. Debe ser un JSON válido'}, 
                    status=400
                )
            except Exception as e:
                return JsonResponse(
                    {'error': f'Error al aplicar filtros: {str(e)}'}, 
                    status=400
                )
                
        # Generar datos para ambos gráficos
        pie_data = self.generate_pie_chart(regular_claims, date_filter)
        bar_data = self.generate_bar_chart(regular_claims, date_filter)

        return JsonResponse({
            'data': {
                'pie_data': pie_data,
                'bar_data': bar_data
            }
        }, status=200)

class ReportGenerateSuppliersCharts(BaseView):
    model = ClaimRegular
    fields = ['id','claim_access','type_of_claim','claim_status','category','heading','subheading','suppliers']

    def get_top_suppliers(self, claims):
        # Diccionario para almacenar el conteo de reclamos por empresa
        supplier_counts = {}

        # Iterar sobre cada reclamo
        for claim in claims:
            # Obtener los suppliers del reclamo
            suppliers = claim.suppliers.all()
            for supplier in suppliers:
                # Usar el nombre completo como clave
                supplier_name = supplier.fullname.strip()
                if supplier_name:
                    supplier_counts[supplier_name] = supplier_counts.get(supplier_name, 0) + 1

        # Convertir el diccionario a lista de tuplas y ordenar por cantidad de reclamos
        sorted_suppliers = sorted(
            supplier_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )

        # Tomar los primeros 10
        top_10 = sorted_suppliers[:10]

        # Formatear los datos para el gráfico
        bar_data = [
            {
                'name': supplier_name,
                'value': count,
                'position': index + 1
            }
            for index, (supplier_name, count) in enumerate(top_10)
        ]

        return {
            'data': bar_data,
            'total_suppliers': len(supplier_counts),
            'total_claims_with_suppliers': sum(supplier_counts.values())
        }

    def get(self, request, *args, **kwargs):
        year = request.GET.get('year')
        month = request.GET.get('month')
        
        if not year:
            return JsonResponse({
                'error': 'Debe especificar un año (parámetro year)'
            }, status=400)

        try:
            # Validar año y mes si se proporciona
            year = int(year)
            if month:
                month = int(month)
                if month < 1 or month > 12:
                    return JsonResponse({
                        'error': 'El mes debe estar entre 1 y 12'
                    }, status=400)

            # Obtener reclamos del año especificado
            claims = self.model.objects.filter(created_at__year=year)

            # Si se especifica el mes, filtrar por mes
            if month:
                claims = claims.filter(created_at__month=month)

            # Prefetch suppliers para optimizar consultas
            claims = claims.prefetch_related('suppliers')

            # Obtener top 10 de suppliers
            suppliers_data = self.get_top_suppliers(claims)

            response_data = {
                'year': year,
                'suppliers': suppliers_data
            }

            # Agregar información del mes si se especificó
            if month:
                months_names = [
                    'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                    'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
                ]
                response_data['month'] = {
                    'number': month,
                    'name': months_names[month - 1]
                }

            return JsonResponse({
                'data': response_data
            }, status=200)

        except ValueError:
            return JsonResponse({
                'error': 'Formato de año o mes inválido. Use números enteros'
            }, status=400)
class ReportGenerateIveCharts(BaseView):
    model = ClaimIVE
    fields = ['id', 'created_at']

    def get(self, request, *args, **kwargs):
        # Obtener parámetros de filtrado
        start_date = request.GET.get('start_date')
        finish_date = request.GET.get('finish_date')
        
        # Preparar filtros de fecha
        date_filter = {}
        if start_date and finish_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                finish_date = datetime.strptime(finish_date, '%Y-%m-%d')
                date_filter = {'created_at__range': (start_date, finish_date)}
            except ValueError:
                return JsonResponse(
                    {'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}, 
                    status=400
                )

        # Obtener reclamos IVE en el rango de fechas
        ive_claims = self.model.objects.filter(**date_filter)
        
        # Contar total de reclamos
        total_claims = ive_claims.count()

        # Obtener conteo por mes si hay un rango de fechas
        monthly_data = []
        if start_date and finish_date:
            claims_by_month = (
                ive_claims
                .annotate(month=ExtractMonth('created_at'))
                .values('created_at__year', 'month')
                .annotate(count=Count('id'))
                .order_by('created_at__year', 'month')
            )

            months_names = [
                'Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio',
                'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'
            ]

            for item in claims_by_month:
                month_data = {
                    'year': item['created_at__year'],
                    'month': item['month'],
                    'month_name': months_names[item['month'] - 1],
                    'count': item['count']
                }
                monthly_data.append(month_data)

        response_data = {
            'total_claims': total_claims,
            'date_range': {
                'start_date': start_date.strftime('%Y-%m-%d') if start_date else None,
                'finish_date': finish_date.strftime('%Y-%m-%d') if finish_date else None
            },
            'monthly_distribution': monthly_data
        }

        return JsonResponse({
            'data': response_data
        }, status=200)

class ReportGetSuppliers(BaseView):
    model=Supplier
    fields = ['id','fullname']

class ReportGenerateCSV(BaseView):
    model = ClaimRegular
    fields = ['id','claim_access','type_of_claim','claim_status','category','heading','subheading','suppliers','created_at']
    list_fields_related = {
        "suppliers": ["fullname"],
    }

    def get(self, request, *args, **kwargs):
        # Obtener parámetros de filtrado
        start_date = request.GET.get('start_date')
        finish_date = request.GET.get('finish_date')
        filters = request.GET.get('filters')
        
        # Preparar filtros de fecha
        date_filter = {}
        if start_date and finish_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                finish_date = datetime.strptime(finish_date, '%Y-%m-%d')
                date_filter = {'created_at__range': (start_date, finish_date)}
            except ValueError:
                return JsonResponse(
                    {'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}, 
                    status=400
                )

        # Obtener todos los reclamos con los filtros aplicados
        queryset = self.model.objects.filter(**date_filter)
        
        # Aplicar filtros adicionales si se proporcionan
        if filters:
            try:
                filters_dict = json.loads(filters)
                queryset = queryset.filter(**filters_dict)
            except json.JSONDecodeError:
                return JsonResponse(
                    {'error': 'Formato de filtros inválido. Debe ser un JSON válido'}, 
                    status=400
                )
            except Exception as e:
                return JsonResponse(
                    {'error': f'Error al aplicar filtros: {str(e)}'}, 
                    status=400
                )

        # Crear el archivo CSV en memoria
        output = io.StringIO()
        headers = ['ID', 'Acceso', 'Tipo', 'Estado', 'Categoría', 'Rubro', 'Subrubro', 'Empresas', 'Fecha de Creación']
        
        # Escribir los headers
        output.write(','.join(headers) + '\n')
        
        # Escribir los datos
        for claim in queryset:
            suppliers = ', '.join([s.fullname for s in claim.suppliers.all()])
            row = [
                str(claim.id),
                str(claim.claim_access),
                str(claim.type_of_claim),
                str(claim.claim_status),
                str(claim.category),
                str(claim.heading),
                str(claim.subheading),
                suppliers,
                claim.created_at.strftime('%Y-%m-%d %H:%M:%S')
            ]
            # Escapar comas en los campos si es necesario
            row = ["\""+field.replace("\"", "\"\"")+"\"" if ',' in field else field for field in row]
            output.write(','.join(row) + '\n')
        
        # Preparar la respuesta
        output.seek(0)
        response = HttpResponse(output.getvalue(), content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="claims_report.csv"'
        
        return response