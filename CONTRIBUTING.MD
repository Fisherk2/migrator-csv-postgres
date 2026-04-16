# 🤝 Guía de Contribución

## 🎯 Cómo Contribuir

### Reportar Problemas
1. **Issues:** Abre un issue describiendo el problema
2. **Información requerida:** Sistema, versión, pasos para reproducir
3. **Screenshots:** Incluye capturas de pantalla si aplica

### Proponer Mejoras
1. **Discusión:** Abre un issue para discutir cambios grandes
2. **Pull Requests:** Para cambios pequeños y claros
3. **Testing:** Asegúrate que `verify_setup.sh` pasa después de cambios

### Convenciones de Contribución
- **Commits:** Mensajes claros y descriptivos
- **Código:** Sigue las [convenciones de nomenclatura](naming_conventions.md)
- **Documentación:** Actualiza README si agregas nuevos scripts
- **Tests:** Ejecuta validación completa antes de PR

## 📋 Checklist para Contribuciones
- [ ] El código sigue las convenciones establecidas
- [ ] La documentación está actualizada
- [ ] `verify_setup.sh` pasa exitosamente
- [ ] No hay información sensible en los cambios
- [ ] Los commits tienen mensajes descriptivos

## 🔄 Flujo de Trabajo

### 1. Preparación
```bash
# Fork y clona el repositorio
git clone https://github.com/Fisherk2/plantilla-proyecto-sistema-datos
cd plantilla-proyecto-sistema-datos

# Crea tu rama
git checkout -b feature/tu-mejora
```

### 2. Desarrollo
- Haz tus cambios siguiendo las convenciones
- Ejecuta `./verify_setup.sh` para validar
- Actualiza la documentación si es necesario

### 3. Submit
```bash
# Commit con mensaje claro
git commit -m "feat: agrega nueva funcionalidad"

# Push a tu fork
git push origin feature/tu-mejora

# Crea Pull Request
```

## 📝 Estándares de Código

### SQL
- Usa snake_case para nombres
- Comenta decisiones importantes
- Scripts idempotentes

### Bash
- Usa quotes en variables
- Maneja errores explícitamente
- Comentarios descriptivos

### Markdown
- Headers jerárquicos
- Links relativos internos
- Código formateado

## 🐛 Reporte de Issues

### Template para Bugs
```markdown
## Descripción
Breve descripción del problema

## Pasos para Reproducir
1. Paso 1
2. Paso 2
3. Paso 3

## Resultado Esperado
Lo que debería pasar

## Resultado Actual
Lo que realmente pasa

## Ambiente
- OS: 
- PostgreSQL: 
- Versión del proyecto:
```

## 🚀 Sugerencias de Mejora

### Ideas Bienvenidas
- Nuevos scripts de utilidad
- Mejoras en documentación
- Optimizaciones de rendimiento
- Nuevas convenciones

### Proceso
1. Abre issue para discutir
2. Espera feedback del equipo
3. Implementa en rama separada
4. Submit PR con tests

## 📚 Recursos

- [Convenciones de Nomenclatura](naming_conventions.md)
- [Decisiones Arquitectónicas](ADR.md)
- [README Principal](README.md)

---

**¡Gracias por contribuir!** 🎉