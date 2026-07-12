# CloudShop Enterprise — Proyecto Final

Plataforma de comercio electrónico cloud-native sobre AWS (S3, CloudFront, WAF, API Gateway, Lambda, DynamoDB, EventBridge, CloudWatch, SES) desplegada 100% con Terraform.

## Estructura

```
cloudshop-enterprise/
├── backend/
│   ├── common/          # capa compartida: auth, respuestas HTTP, auditoría, eventos, validación, acceso a DynamoDB
│   ├── usuarios/        # Módulo 1
│   ├── productos/       # Módulo 2 (listo)
│   ├── tiendas/         # Módulo 3 (pendiente)
│   ├── carrito/         # Módulo 4 (pendiente)
│   ├── pedidos/         # Módulo 5 (pendiente)
│   ├── notificaciones/  # consumer de eventos -> SES (pendiente)
│   └── dashboard/       # Módulo 6 (pendiente)
├── infra/terraform/
│   ├── modules/
│   │   ├── api_method/      # method + integration + permission por endpoint
│   │   └── cors_options/    # OPTIONS + mock integration para CORS
│   ├── provider.tf, variables.tf, locals.tf, outputs.tf
│   ├── dynamodb.tf, iam.tf, lambda.tf, api_gateway.tf, eventbridge.tf
│   └── terraform.tfvars.example
└── docs/                 # documento técnico (pendiente)
```

## Estado actual

- [x] Estructura base + capa común (`backend/common`)
- [x] Módulo 1 — Usuarios (CRUD + roles + auditoría)
- [x] Terraform base: provider, IAM (mínimo privilegio), DynamoDB usuarios/auditoría, API Gateway + Cognito Authorizer, Lambdas de usuarios, EventBridge bus
- [x] Módulo 2 — Productos (CRUD + roles + auditoría + GSI tienda_id)
- [ ] Módulos 3-6 (Tiendas, Carrito, Pedidos+SES, Dashboard)
- [ ] CloudFront + WAF + S3 frontend
- [ ] SES + consumer de notificaciones
- [ ] CloudWatch alarms
- [ ] Documento técnico completo

## Cómo desplegar (una vez completo)

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars   # editar con tus valores reales
terraform init
terraform plan
terraform apply
```

Requiere un Cognito User Pool existente (ARN en `cognito_user_pool_arn`) con un atributo custom `custom:role` (`Administrador` | `Operador` | `Cliente`) — el mismo patrón de autorización visto en Clase 16/29.

## Convención de roles (IAM de la aplicación, vía Cognito)

| Rol | Puede |
|---|---|
| Administrador | gestionar usuarios, tiendas, productos, ver reportes |
| Operador | gestionar inventario, gestionar pedidos |
| Cliente | comprar productos, ver sus propios pedidos |

Cada Lambda valida rol con `common.auth.require_roles(...)` antes de tocar datos — nunca se confía solo en el frontend (mismo principio de Clase 28).
