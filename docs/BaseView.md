# BaseView Documentation

El `BaseView` es una clase base que implementa una API REST completa con funcionalidades CRUD (Create, Read, Update, Delete) y manejo avanzado de permisos. Esta clase está diseñada para trabajar en conjunto con el `BaseModel` y proporciona una estructura robusta para crear vistas API en Django.

## Características Principales

### 1. Configuración Base
```python
class MiVista(BaseView):
    model = MiModelo
    fields = ['campo1', 'campo2']  # Campos a mostrar en respuestas
    foreign_keys = {               # Definición de claves foráneas
        'relacion': OtroModelo
    }
    instance_fields = ['campo3']   # Campos adicionales para vista detalle
```

### 2. Endpoints Implementados

#### GET (Lista y Detalle)
- **Lista**: `GET /api/recurso/`
  - Soporta paginación
  - Filtrado dinámico
  - Ordenamiento
  - Búsqueda

- **Detalle**: `GET /api/recurso/{id}/`
  - Obtiene instancia específica
  - Incluye permisos
  - Campos adicionales configurables

#### POST (Creación y Duplicación)
- **Crear**: `POST /api/recurso/`
  - Validación automática
  - Manejo de relaciones
  - Respuesta formateada

- **Duplicar**: `POST /api/recurso/{id}/duplicate/`
  - Copia instancia existente
  - Permite modificar campos

#### PATCH (Actualización)
- `PATCH /api/recurso/{id}/`
  - Actualización parcial
  - Validación de campos
  - Manejo de conflictos

#### DELETE (Eliminación)
- `DELETE /api/recurso/{id}/`
  - Validación de dependencias
  - Manejo de errores de protección

### 3. Características Avanzadas

#### Manejo de Permisos
```python
def get_permissions(self, request, *args, **kwargs):
    # Personalizar lógica de permisos
    return {
        'view_permission': True,
        'add_permission': True,
        'modify_permission': True,
        'delete_permission': True
    }
```

#### Filtrado y Búsqueda
- Soporte para filtros complejos
- Búsqueda en múltiples campos
- Ordenamiento personalizable

#### Formato de Respuesta
```json
{
    "messages": [
        {
            "level": "success|error|warning",
            "title": "Mensaje principal",
            "description": "Descripción opcional"
        }
    ],
    "data": {},
    "permissions": {}
}
```

### 4. Personalización

#### Mensajes Personalizados
```python
def message_success_created(self):
    return f"{self.model._meta.verbose_name} creado exitosamente"

def message_error_conflict(self, err):
    return {
        "title": "Conflicto detectado",
        "description": str(err)
    }
```

#### Procesamiento de Datos
```python
def clean_body(self, request_body, **kwargs):
    # Personalizar validación de datos
    return cleaned_data, None

def data_json(self, fields, **kwargs):
    # Personalizar serialización
    return serialized_data
```

## Uso Avanzado

### 1. Manejo de Archivos
- Soporte para `MultiPartParser`
- Procesamiento automático de archivos
- Validación de tipos de archivo

### 2. Validación Personalizada
```python
def clean_before_save(sender, instance, *args, **kwargs):
    # Validación antes de guardar
    instance.full_clean()
```

### 3. Anotaciones y Agregaciones
```python
class MiVista(BaseView):
    annotate = {
        'campo_calculado': Count('relacion')
    }
```

## Mejores Prácticas

1. **Seguridad**
   - Siempre implementar `get_permissions`
   - Validar datos de entrada
   - Manejar excepciones apropiadamente

2. **Rendimiento**
   - Usar `select_related` y `prefetch_related`
   - Implementar paginación
   - Optimizar consultas

3. **Mantenibilidad**
   - Documentar configuraciones personalizadas
   - Mantener consistencia en respuestas
   - Usar mensajes descriptivos

4. **Extensibilidad**
   - Heredar métodos según necesidad
   - Mantener la lógica de negocio separada
   - Usar mixins para funcionalidad compartida

## Consideraciones de Implementación

### 1. Configuración Requerida
```python
class MiVista(BaseView):
    model = MiModelo                # Obligatorio
    fields = ['campo1', 'campo2']   # Recomendado
    foreign_keys = {}               # Según necesidad
```

### 2. Manejo de Errores
- Validación de entrada
- Conflictos de unicidad
- Errores de protección (CASCADE)
- Errores de integridad

### 3. Personalización de Respuestas
- Formato consistente
- Mensajes claros
- Códigos HTTP apropiados

### 4. Seguridad
- Validación de permisos
- Sanitización de entrada
- Protección CSRF
- Manejo de sesiones
