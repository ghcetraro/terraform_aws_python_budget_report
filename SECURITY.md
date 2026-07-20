# Seguridad

## Secretos

**Nunca commitees** al repositorio:

- `terraform.tfvars` con credenciales, tokens o passwords reales
- Archivos de state (`terraform.tfstate`, `*.tfstate.backup`)
- Claves AWS, kubeconfig, certificados privados
- API tokens (FortiGate, GitHub, etc.)

Usá variables de entorno, AWS SSO o archivos locales gitignored.

## Buenas prácticas

1. Copiá valores de ejemplo en tfvars; los reales quedan fuera del repo
2. Revisá `terraform plan` antes de `apply`, especialmente en producción
3. Principio de mínimo privilegio en roles IAM
4. Rotá credenciales periódicamente

## Reporte de vulnerabilidades

Si encontrás un problema de seguridad, abrí un [GitHub Security Advisory](https://github.com/ghcetraro/terraform_aws_python_budget_report/security/advisories/new) o contactá al mantenedor del repo. No abras issues públicos con detalles explotables.

Usá `terraform.tfvars.example` como plantilla; nunca subas `*.tfvars` ni `*.tfstate`.
