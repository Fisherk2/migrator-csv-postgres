# Convenciones de Nomenclatura PostgreSQL

## Propósito
Este documento establece las convenciones de nomenclatura para mantener consistencia, legibilidad y mantenibilidad en el diseño de bases de datos PostgreSQL. La consistencia en nombres reduce errores y facilita la colaboración en equipo.

## Principios Fundamentales
- **Snake_case**: Todos los identificadores usan minúsculas con guiones bajos
- **Inglés**: Nombres técnicos en inglés (estándar de la industria)
- **Pronunciables**: Nombres que se puedan decir y recordar fácilmente
- **Autoexplicativos**: Nombres que revelan su propósito sin contexto adicional

---

## 1. Convenciones para Tablas

### Reglas
- **Formato**: snake_case en plural
- **Propósito**: Representar colecciones de entidades
- **Ejemplos**: `users`, `projects`, `user_sessions`, `order_items`

### Por qué plural
Las tablas almacenan múltiples instancias de la misma entidad, por lo que el plural refleja correctamente su naturaleza de colección.

| Bueno | Malo | Razón |
|-------|------|-------|
| `users` | `user` | Tabla almacena múltiples usuarios |
| `project_members` | `projectMember` | Snake_case + plural |
| `order_items` | `orderitem` | Más legible y separado |

---

## 2. Convenciones para Columnas

### Reglas
- **Formato**: snake_case en singular
- **Propósito**: Atributos individuales de una entidad
- **Ejemplos**: `username`, `email_address`, `created_at`, `is_active`

### Por qué singular
Las columnas representan un atributo individual de cada fila, no una colección.

| Bueno | Malo | Razón |
|-------|------|-------|
| `username` | `usernames` | Cada usuario tiene un username |
| `email_address` | `emailAddress` | Snake_case consistente |
| `created_at` | `createdAt` | Snake_case en lugar de camelCase |

---

## 3. Convenciones para Claves Primarias (PK)

### Reglas
- **Formato**: `id` (simple y universal)
- **Tipo**: SERIAL o BIGINT
- **Propósito**: Identificador único por defecto

### Por qué `id`
Es el estándar de la industria, fácil de recordar y consistente across todas las tablas.

| Bueno | Malo | Razón |
|-------|------|-------|
| `id` | `user_id` (como PK) | `id` es estándar para PK |
| `id` | `userId` | Snake_case requerido |
| `id` | `pk_users` | Demasiado verboso para PK |

---

## 4. Convenciones para Claves Foráneas (FK)

### Reglas
- **Formato**: `tabla_referenciada_id`
- **Propósito**: Referenciar la PK de otra tabla
- **Ejemplos**: `user_id`, `project_id`, `role_id`

### Por qué este formato
Indica claramente qué tabla se referencia y mantiene consistencia con el nombre de la PK (`id`).

| Bueno | Malo | Razón |
|-------|------|-------|
| `user_id` | `userId` | Snake_case consistente |
| `project_id` | `project_fk` | `_id` indica FK directamente |
| `role_id` | `id_role` | Orden tabla_id es más natural |

---

## 5. Convenciones para Índices

### Reglas
- **Formato**: `idx_tabla_columna(s)`
- **Propósito**: Mejorar rendimiento de consultas
- **Múltiples columnas**: `idx_tabla_col1_col2`

### Por qué `idx_` prefijo
Distingue fácilmente los índices de otros objetos y facilita su identificación.

| Bueno | Malo | Razón |
|-------|------|-------|
| `idx_users_email` | `users_email_index` | Prefijo estándar `idx_` |
| `idx_orders_status_date` | `order_status_date_idx` | Orden consistente |
| `idx_projects_name` | `project_name_idx` | Prefijo `idx_` primero |

---

## 6. Convenciones para Secuencias

### Reglas
- **Formato**: `tabla_id_seq`
- **Propósito**: Generar valores para columnas SERIAL
- **Autogenerado**: PostgreSQL crea automáticamente

### Por qué este formato
PostgreSQL usa este patrón por defecto y es autoexplicativo.

| Bueno | Malo | Razón |
|-------|------|-------|
| `users_id_seq` | `user_sequence` | Formato estándar PostgreSQL |
| `projects_id_seq` | `seq_projects` | Orden tabla_columna_seq |
| `orders_id_seq` | `order_seq` | Incluir `_id` para claridad |

---

## 7. Convenciones para Funciones y Stored Procedures

### Reglas
- **Formato**: `verbo_sustantivo` o `verbo_sustantivo_por_condición`
- **Propósito**: Realizar operaciones específicas
- **Ejemplos**: `get_user_by_id`, `create_project`, `calculate_total_amount`

### Por qué formato verbo-sustantivo
Sigue el patrón de acción-objeto, haciendo el propósito inmediatamente claro.

| Bueno | Malo | Razón |
|-------|------|-------|
| `get_user_by_id` | `getUserById` | Snake_case requerido |
| `create_project` | `project_create` | Orden verbo-sustantivo |
| `calculate_order_total` | `calc_ord_total` | Sin abreviaciones crípticas |

---

## 8. Convenciones para Vistas

### Reglas
- **Formato**: `v_tabla` o `tabla_view`
- **Propósito**: Consultas predefinidas complejas
- **Consistencia**: Elegir un formato y mantenerlo

### Por qué prefijo/sufijo
Distingue las vistas de las tablas reales y previene conflictos de nombres.

| Bueno | Malo | Razón |
|-------|------|-------|
| `v_active_users` | `active_users` | Prefijo `v_` identifica vista |
| `users_view` | `userview` | Sufijo `_view` también válido |
| `v_project_summary` | `project_summary` | Confundiría con tabla real |

---

## 9. Convenciones para Triggers

### Reglas
- **Formato**: `tg_tabla_evento_timing`
- **Evento**: `before_insert`, `after_update`, `before_delete`
- **Timing**: `before` o `after`

### Por qué `tg_` prefijo
Identifica claramente los triggers y su propósito.

| Bueno | Malo | Razón |
|-------|------|-------|
| `tg_users_before_insert` | `users_bi_trigger` | Prefijo `tg_` estándar |
| `tg_orders_after_update` | `after_order_update` | Orden consistente |
| `tg_projects_before_delete` | `tg_bd_projects` | Sin abreviaciones |

---

## 10. Ejemplos Comparativos: Buenas vs Malas Prácticas

| Tipo | Bueno | Malo | Problema |
|------|-------|------|----------|
| Tabla | `users` | `usr` | Abreviación críptica |
| Columna | `email_address` | `email` | Ambiguo (podría ser email_id) |
| PK | `id` | `user_pk` | Demasiado verboso |
| FK | `project_id` | `proj_fk` | Abreviación poco clara |
| Índice | `idx_users_username` | `username_idx` | Orden inconsistente |
| Función | `get_user_by_email` | `getUserByEmail` | camelCase en lugar de snake_case |
| Vista | `v_active_projects` | `active_projects_view` | Mezcla de formatos |
| Trigger | `tg_users_before_update` | `users_bu_trg` | Abreviaciones confusas |

---

## Excepciones Permitidas

### Legacy Systems
- Al integrar con sistemas existentes, mantener nombres originales para compatibilidad
- Documentar claramente las excepciones y su justificación

### Constraints Específicas
- Nombres de constraints pueden incluir prefijos como `fk_`, `pk_`, `ck_`, `uq_`
- Ejemplo: `fk_users_project_id` (foreign key constraint)

---

## Checklist de Validación

### Para Tablas
- [ ] Nombre en plural
- [ ] Snake_case
- [ ] Inglés
- [ ] Pronunciable

### Para Columnas
- [ ] Nombre en singular
- [ ] Snake_case
- [ ] Descriptivo (no abreviado)
- [ ] Consistente con dominio

### Para Relaciones
- [ ] PK siempre `id`
- [ ] FK formato `tabla_id`
- [ ] Índices con prefijo `idx_`
- [ ] Constraints con prefijos específicos

---

## Conclusión

La consistencia en nomenclatura no es estética, es una herramienta fundamental para:
- **Reducir errores**: Nombres predecibles minimizan confusiones
- **Facilitar mantenimiento**: Código autodocumentado
- **Mejorar colaboración**: Equipo habla el mismo "lenguaje"
- **Acelerar onboarding**: Nuevos miembros se adaptan rápidamente

Estas convenciones deben seguirse rigurosamente y actualizarse solo con consenso del equipo completo.