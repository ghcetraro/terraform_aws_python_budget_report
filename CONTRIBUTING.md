# Contribuir a terraform-aws-python-budget-report

Gracias por interesarte en el proyecto.

## Antes de empezar

1. Revisá [README.md](README.md) y las dependencias del módulo.
2. **No commitees secretos**: `terraform.tfvars` con credenciales reales, `.terraform/`, state files, claves AWS.

## Cómo reportar bugs

1. Buscá si ya existe un [issue](https://github.com/ghcetraro/terraform_aws_python_budget_report/issues) similar.
2. Abrí uno nuevo con:
   - Versión / commit
   - Configuración relevante (**sin secretos**)
   - Comportamiento esperado vs actual

Para vulnerabilidades, seguí [SECURITY.md](SECURITY.md).

## Pull requests

1. Fork del repo y branch desde `main`:
   ```bash
   git checkout -b feature/mi-cambio
   ```
2. Cambios acotados y commits claros en español o inglés.
3. Verificá localmente:
   ```bash
   terraform validate
   terraform fmt -check -recursive
   ```
4. Actualizá README.md y CHANGELOG.md si cambiás comportamiento.
5. Abrí el PR describiendo el **por qué** del cambio.

## Estilo

- HCL formateado con `terraform fmt`
- Cambios mínimos y acotados al módulo
- Documentar variables nuevas en README.md

## Releases

Versiones etiquetadas (`v1.0.0`, …) documentadas en [CHANGELOG.md](CHANGELOG.md).

## Preguntas

Abrí un issue con etiqueta `question`.
