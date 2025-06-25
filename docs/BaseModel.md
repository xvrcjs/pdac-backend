# BaseModel Documentation

El `BaseModel` es una clase base abstracta que proporciona funcionalidad común para todos los modelos en el sistema. Esta clase extiende el modelo base de Django y agrega características adicionales para el manejo de auditoría, permisos y gestión de estados.

## Características Principales

### 1. Campos Base
- `uuid`: Identificador único universal (UUID) que sirve como clave primaria
- `created_at`: Fecha y hora de creación (UTC)
- `created_by`: Usuario que creó el registro
- `created_from`: IP desde donde se creó el registro
- `modified_at`: Fecha y hora de última modificación (UTC)
- `modified_by`: Usuario que realizó la última modificación
- `modified_from`: IP desde donde se realizó la última modificación

### 2. Gestión de Estados

#### Método `is_new`
- Propiedad que indica si el objeto es nuevo (no ha sido guardado en la base de datos)
- Retorna `True` si el objeto está en estado de creación

#### Método `old`
- Propiedad que permite acceder al estado anterior del objeto
- Útil para comparar cambios antes y después de una modificación
- Retorna `None` si el objeto es nuevo

### 3. Operaciones CRUD

#### Método `save()`
- Extiende el método save de Django
- Parámetros adicionales:
  - `by_system`: Indica si la operación es realizada por el sistema
  - `do_not_log`: Evita el registro de auditoría
- Actualiza automáticamente los campos de auditoría

#### Método `duplicate()`
- Crea una copia del objeto actual con un nuevo UUID
- Permite modificar atributos específicos en la copia
- Parámetros:
  - `by_system`: Indica si la duplicación es realizada por el sistema
  - `do_not_log`: Evita el registro de auditoría
  - `**kwargs`: Atributos adicionales para modificar en la copia

### 4. Sistema de Permisos

#### Método `get_permissions()`
- Método de clase que verifica los permisos de un usuario
- Parámetros:
  - `account`: Cuenta del usuario
  - `pk`: ID del objeto (opcional)
- Retorna diccionario con permisos:
  - `view_permission`
  - `add_permission`
  - `modify_permission`
  - `delete_permission`

#### Método `_get_permissions()`
- Método interno para obtener permisos basados en módulos y roles
- Verifica:
  - Permisos a nivel de cliente
  - Roles administrativos
  - Políticas específicas de usuario

## Uso del BaseModel

```python
from common.models import BaseModel

class MiModelo(BaseModel):
    # Tus campos específicos aquí
    nombre = models.CharField(max_length=100)

    class Meta:
        # El BaseModel ya es abstracto, no necesitas declararlo aquí
        pass

# Ejemplo de uso
objeto = MiModelo()
objeto.save()  # Registra automáticamente created_at, created_by, etc.

# Verificar si es nuevo
print(objeto.is_new)  # False después de guardar

# Acceder al estado anterior
objeto_anterior = objeto.old
```

## Consideraciones Importantes

1. **Auditoría Automática**: Todos los modelos que heredan de BaseModel tienen seguimiento automático de creación y modificación.

2. **Gestión de UUIDs**: Usa UUIDs como claves primarias en lugar de IDs auto-incrementales.

3. **Control de Permisos**: Implementa un sistema de permisos granular basado en:
   - Roles de usuario
   - Pertenencia a cliente
   - Políticas específicas

4. **Duplicación Segura**: Proporciona un método seguro para duplicar registros manteniendo la integridad de los datos.

## Mejores Prácticas

1. Siempre hereda de BaseModel para nuevos modelos que requieran auditoría.
2. Utiliza el parámetro `do_not_log=True` cuando no necesites registro de auditoría.
3. Implementa permisos específicos sobrescribiendo `get_permissions()` si es necesario.
4. Usa el método `duplicate()` para crear copias seguras de registros.
