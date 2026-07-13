# CloudShop Enterprise

Plataforma de comercio electrónico cloud-native sobre AWS, 100% serverless y desplegada íntegramente con Terraform (Infrastructure as Code). Proyecto final del curso Desarrollo de Software en la Nube I.

**Repositorio:** [github.com/ChristianRende22/CloudShop-Enterprise](https://github.com/ChristianRende22/CloudShop-Enterprise)

## Arquitectura

```
                    ┌─────────────┐
   usuario ───────▶ │  CloudFront │◀── WAFv2 (managed rules + rate limit 2000/IP)
                    └──────┬──────┘
                    ┌──────┴──────┐
              ┌─────▼────┐   ┌────▼─────────┐
              │ S3 (SPA) │   │ API Gateway   │── Cognito Authorizer (JWT)
              └──────────┘   └──────┬────────┘
                                     │
                        ┌────────────┴────────────┐
                        │   26 Lambdas (Python)    │── require_roles() por función
                        └────────────┬─────────────┘
              ┌──────────────┬───────┴───────┬──────────────┐
        ┌─────▼─────┐  ┌─────▼─────┐  ┌──────▼─────┐  ┌─────▼──────┐
        │ DynamoDB   │  │EventBridge│  │ CloudWatch │  │    SES     │
        │ (6 tablas) │  │(PedidoCre-│  │(logs/métr./│  │(notif. de  │
        │            │  │ado/Cancel)│  │ alarmas)   │  │  pedidos)  │
        └────────────┘  └─────┬─────┘  └────────────┘  └─────▲──────┘
                               └───────────────────────────────┘
                          Lambda "notificaciones" (rol IAM propio)
```

## Stack

| Capa | Tecnología |
|---|---|
| Frontend | React 18 + Vite 5, `amazon-cognito-identity-js` (login SRP) |
| Autenticación | Amazon Cognito (User Pool + App Client propios, atributo `custom:role`) |
| API | API Gateway REST + Cognito Authorizer, 26 endpoints |
| Cómputo | AWS Lambda, Python 3.12, 26 funciones (una operación CRUD por función) |
| Datos | DynamoDB (6 tablas, `PAY_PER_REQUEST`, 2 GSI) |
| Eventos | EventBridge (bus propio, `PedidoCreado` / `PedidoCancelado`) |
| Notificaciones | SES (rol IAM exclusivo, scoped por `ses:FromAddress`) |
| Entrega del frontend | S3 (privado) + CloudFront (OAC) + WAFv2 |
| Observabilidad | CloudWatch (logs estructurados, alarmas, dashboard) + SNS |
| Infraestructura | Terraform (100% del stack, sin recursos creados a mano) |

## Estructura del repositorio

```
cloudshop-enterprise/
├── backend/
│   ├── common/           # capa compartida: auth (RBAC), respuestas HTTP, auditoría, eventos, validación, acceso a DynamoDB
│   ├── usuarios/         # Módulo 1 — CRUD + roles + auditoría
│   ├── productos/        # Módulo 2 — CRUD + roles + GSI tienda_id
│   ├── tiendas/          # Módulo 3 — CRUD + borrado lógico
│   ├── carrito/          # Módulo 4 — clave compuesta usuario_id+producto_id
│   ├── pedidos/          # Módulo 5 — inventario atómico, EventBridge, auditoría
│   ├── notificaciones/   # consumer de eventos -> SES
│   └── dashboard/        # Módulo 6 — reportes agregados, solo Administrador
├── infra/terraform/
│   ├── modules/
│   │   ├── api_method/       # method + integration + permission, reutilizable por endpoint
│   │   └── cors_options/     # OPTIONS + mock integration para CORS, reutilizable por recurso
│   ├── provider.tf, variables.tf, locals.tf, outputs.tf
│   ├── dynamodb.tf, iam.tf, lambda.tf, api_gateway.tf, eventbridge.tf, ses.tf, cognito.tf
│   ├── s3_frontend.tf, cloudfront.tf, waf.tf, cloudwatch.tf
│   └── terraform.tfvars.example
└── frontend/
    └── src/
        ├── auth/          # AuthContext + envoltorio de amazon-cognito-identity-js
        ├── services/      # un cliente por módulo (usuarios, productos, tiendas, carrito, pedidos, dashboard)
        ├── components/    # Navbar, ProtectedRoute, RoleGate
        └── pages/         # Login, Signup, ConfirmSignup, Productos, Tiendas, Carrito, Pedidos, Dashboard
```

## Módulos

| # | Módulo | Descripción |
|---|---|---|
| 1 | Usuarios | Perfil de aplicación sobre la identidad de Cognito. Administrador gestiona cualquiera; Operador/Cliente solo el propio. |
| 2 | Productos | Catálogo con inventario. Administrador CRUD completo; Operador solo inventario; Cliente solo lectura. DELETE exclusivo de Administrador. |
| 3 | Tiendas | Catálogo de tiendas, borrado lógico. Gestión exclusiva de Administrador. |
| 4 | Carrito | Siempre "el mío" — el `usuario_id` sale del JWT, no de la URL. |
| 5 | Pedidos | Reserva de inventario atómica (`ConditionExpression`), rollback compensatorio, máquina de estados secuencial, publica eventos a EventBridge. |
| 6 | Dashboard | Reportes agregados (ventas, más vendidos, agotados, clientes top) — exclusivo Administrador. |

## Roles (RBAC vía Cognito)

| Rol | Puede |
|---|---|
| Administrador | Gestionar usuarios, tiendas, productos (CRUD completo), ver reportes del Dashboard |
| Operador | Gestionar inventario de productos, gestionar el ciclo de vida de pedidos |
| Cliente | Comprar productos, ver y cancelar sus propios pedidos |

La autorización se valida en dos capas: el Cognito Authorizer de API Gateway rechaza tokens inválidos antes de invocar cómputo, y cada Lambda vuelve a validar el rol server-side con el decorador `common.auth.require_roles(...)` — nunca se confía únicamente en lo que oculta o muestra el frontend.

## Cómo desplegar

Requisitos: cuenta de AWS, [AWS CLI](https://docs.aws.amazon.com/cli/) configurado (`aws configure`) con un usuario/rol con permisos suficientes, [Terraform](https://developer.hashicorp.com/terraform/install), y Node.js 18+.

```bash
cd infra/terraform
cp terraform.tfvars.example terraform.tfvars   # editar con tu correo real (ses_sender_email, alert_email)
terraform init
terraform plan
terraform apply
```

Terraform crea el Cognito User Pool y App Client propios del proyecto (no hace falta ninguno externo). AWS envía un correo de verificación a `ses_sender_email` — hay que confirmarlo desde el enlace para que salgan las notificaciones de pedido (SES está en modo sandbox por defecto, así que el correo del cliente que compre también debe estar verificado, o pedir salida del sandbox).

Con los outputs del apply, configurar y desplegar el frontend:

```bash
cd ../../frontend
cp .env.production.example .env.production
# completar con los valores de:
#   terraform -chdir=../infra/terraform output -raw api_invoke_url
#   terraform -chdir=../infra/terraform output -raw cognito_user_pool_id
#   terraform -chdir=../infra/terraform output -raw cognito_client_id
npm install
npm run build
aws s3 sync dist/ s3://$(terraform -chdir=../infra/terraform output -raw frontend_bucket_name) --delete
aws cloudfront create-invalidation \
  --distribution-id $(terraform -chdir=../infra/terraform output -raw cloudfront_distribution_id) \
  --paths "/*"
```

La URL pública queda en `terraform output cloudfront_domain_name`.

Para desmontar todo y dejar de generar costo: `terraform destroy` (no hay `prevent_destroy` en ningún recurso).

## Testing

Backend, con [moto](https://github.com/getmoto/moto) simulando AWS en memoria (sin credenciales reales ni red):

```bash
cd backend
pip install -r requirements.txt
export AWS_DEFAULT_REGION=us-east-1 AWS_ACCESS_KEY_ID=testing AWS_SECRET_ACCESS_KEY=testing
pytest -v
```

56 tests cubriendo los 6 módulos + el consumer de notificaciones, incluyendo el flujo completo de un pedido (reserva de inventario, evento, notificación) y los casos de rollback por falta de stock.

## Estado del proyecto

- [x] Los 6 módulos (backend + tests + Terraform)
- [x] Infraestructura completa: DynamoDB, IAM (mínimo privilegio), API Gateway + Cognito Authorizer, EventBridge, SES, CloudFront + WAF + S3, CloudWatch, Cognito User Pool propio
- [x] Frontend (React + Vite, autenticación Cognito SRP, páginas por módulo con control de UI por rol)
- [x] Desplegado y probado de punta a punta en una cuenta real de AWS (los 3 roles, los 6 módulos, notificaciones por correo)
- [x] Documento técnico (arquitectura, diseño de API, diseño de base de datos, diseño de seguridad — entregado aparte)
