# CloudShop Enterprise — Proyecto Final

Plataforma de comercio electrónico cloud-native sobre AWS (S3, CloudFront, WAF, API Gateway, Lambda, DynamoDB, EventBridge, CloudWatch, SES) desplegada 100% con Terraform.

## Estructura

```
cloudshop-enterprise/
├── backend/
│   ├── common/          # capa compartida: auth, respuestas HTTP, auditoría, eventos, validación, acceso a DynamoDB
│   ├── usuarios/        # Módulo 1
│   ├── productos/       # Módulo 2 (listo)
│   ├── tiendas/         # Módulo 3 (listo)
│   ├── carrito/         # Módulo 4 (listo)
│   ├── pedidos/         # Módulo 5 (listo)
│   ├── notificaciones/  # consumer de eventos -> SES (listo)
│   └── dashboard/       # Módulo 6 (listo)
├── infra/terraform/
│   ├── modules/
│   │   ├── api_method/      # method + integration + permission por endpoint
│   │   └── cors_options/    # OPTIONS + mock integration para CORS
│   ├── provider.tf, variables.tf, locals.tf, outputs.tf
│   ├── dynamodb.tf, iam.tf, lambda.tf, api_gateway.tf, eventbridge.tf, ses.tf
│   ├── s3_frontend.tf, cloudfront.tf, waf.tf, cloudwatch.tf, cognito.tf
│   └── terraform.tfvars.example
├── frontend/              # React 18 + Vite 5 + Cognito (SRP) — listo
│   └── src/{auth,services,components,pages}
└── docs/                 # documento técnico (entregado aparte, no versionado)
```

## Estado actual

- [x] Estructura base + capa común (`backend/common`)
- [x] Módulo 1 — Usuarios (CRUD + roles + auditoría)
- [x] Terraform base: provider, IAM (mínimo privilegio), DynamoDB usuarios/auditoría, API Gateway + Cognito Authorizer, Lambdas de usuarios, EventBridge bus
- [x] Módulo 2 — Productos (CRUD + roles + auditoría + GSI tienda_id)
- [x] Módulo 3 — Tiendas (CRUD + borrado lógico + roles)
- [x] Módulo 4 — Carrito (agregar/modificar/eliminar/vaciar, propio del usuario)
- [x] Módulo 5 — Pedidos (inventario atómico + rollback, EventBridge, auditoría, SES)
- [x] Módulo 6 — Dashboard Ejecutivo (agregación sobre Pedidos + Productos, solo Administrador)
- [x] CloudFront + WAF + S3 frontend (OAC, fallback SPA, managed rules + rate limit)
- [x] SES + consumer de notificaciones
- [x] CloudWatch (alarmas por Lambda/API Gateway + SNS + dashboard operativo)
- [x] Cognito User Pool + App Client propios (`infra/terraform/cognito.tf`, atributo `custom:role`)
- [x] Frontend (React 18 + Vite 5, login/signup/confirm con Cognito SRP, páginas por módulo con control de UI por rol)
- [ ] Documento técnico completo (se entrega aparte, no se sube al repo)

## Cómo desplegar

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars   # editar con tus valores reales
terraform init
terraform plan
terraform apply
```

El propio Terraform crea el Cognito User Pool (ya no hace falta uno externo). Después del apply:

```bash
cd ../../frontend
cp .env.production.example .env.production
# rellenar con:
#   terraform -chdir=../infra/terraform output api_invoke_url
#   terraform -chdir=../infra/terraform output cognito_user_pool_id
#   terraform -chdir=../infra/terraform output cognito_client_id
npm install
npm run build   # sube dist/ al bucket S3 del frontend (aws s3 sync dist/ s3://<frontend_bucket_name>)
```

## Convención de roles (IAM de la aplicación, vía Cognito)

| Rol | Puede |
|---|---|
| Administrador | gestionar usuarios, tiendas, productos, ver reportes |
| Operador | gestionar inventario, gestionar pedidos |
| Cliente | comprar productos, ver sus propios pedidos |

Cada Lambda valida rol con `common.auth.require_roles(...)` antes de tocar datos — nunca se confía solo en el frontend (mismo principio de Clase 28).
