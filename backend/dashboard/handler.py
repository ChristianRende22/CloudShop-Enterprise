"""
Módulo 6 - Dashboard Ejecutivo.

Exclusivo de rol Administrador ("consulta reportes", sección 5 del enunciado).
Un único endpoint (GET /dashboard) que agrega las 6 métricas pedidas sobre
las tablas Pedidos y Productos.

Nota de diseño: se usa Scan paginado sobre Pedidos y Productos para calcular
las métricas en memoria. Es un trade-off aceptable para el volumen de datos
de un proyecto académico. En producción esto se resolvería con DynamoDB
Streams alimentando tablas de agregados, o un servicio de analítica
(Athena/QuickSight) — fuera del alcance del temario visto en el curso.
"""
import collections
import decimal

from common.auth import require_roles
from common.db import table
from common.responses import ok

TABLA_PEDIDOS = "PEDIDOS_TABLE"
TABLA_PRODUCTOS = "PRODUCTOS_TABLE"
TOP_N = 5


def _escanear_todo(tabla):
    """Scan con paginación completa (DynamoDB Scan devuelve máx. ~1MB por página)."""
    items = []
    resp = tabla.scan()
    items.extend(resp.get("Items", []))
    while "LastEvaluatedKey" in resp:
        resp = tabla.scan(ExclusiveStartKey=resp["LastEvaluatedKey"])
        items.extend(resp.get("Items", []))
    return items


@require_roles("Administrador")
def resumen(event, context):
    """GET /dashboard"""
    pedidos = _escanear_todo(table(TABLA_PEDIDOS))
    productos = _escanear_todo(table(TABLA_PRODUCTOS))

    # Las ventas excluyen pedidos Cancelados; "pedidos por estado" si los incluye
    # (es información operativa, no solo comercial).
    pedidos_validos = [p for p in pedidos if p.get("estado") != "Cancelado"]

    total_ventas = sum((p.get("total") or 0) for p in pedidos_validos)

    ventas_por_tienda = collections.defaultdict(lambda: decimal.Decimal(0))
    unidades_por_producto = collections.Counter()
    nombre_producto = {}
    compras_por_cliente = collections.defaultdict(lambda: decimal.Decimal(0))
    # OJO: "cliente_username" viene de cognito:username, que con
    # username_attributes=["email"] en el User Pool es un UUID autogenerado
    # por Cognito, NO el correo. Para mostrar algo legible en el Dashboard se
    # usa cliente_email (que si es el correo real, guardado en cada pedido).
    email_por_cliente = {}

    for pedido in pedidos_validos:
        cliente_id = pedido.get("cliente_id", "desconocido")
        compras_por_cliente[cliente_id] += pedido.get("total") or 0
        email_por_cliente[cliente_id] = pedido.get("cliente_email", cliente_id)

        for item in pedido.get("items", []):
            producto_id = item.get("producto_id")
            if not producto_id:
                continue
            ventas_por_tienda[item.get("tienda_id", "desconocida")] += item.get("subtotal") or 0
            unidades_por_producto[producto_id] += int(item.get("cantidad", 0))
            nombre_producto[producto_id] = item.get("nombre", producto_id)

    pedidos_por_estado = collections.Counter(p.get("estado", "Desconocido") for p in pedidos)

    productos_agotados = [
        {"producto_id": p["producto_id"], "nombre": p.get("nombre", "")}
        for p in productos
        if int(p.get("inventario_disponible", 0)) == 0
    ]

    productos_mas_vendidos = [
        {"producto_id": pid, "nombre": nombre_producto.get(pid, pid), "unidades_vendidas": cant}
        for pid, cant in unidades_por_producto.most_common(TOP_N)
    ]

    clientes_top = [
        {"cliente_id": cid, "cliente_email": email_por_cliente.get(cid, cid), "total_comprado": monto}
        for cid, monto in sorted(compras_por_cliente.items(), key=lambda kv: kv[1], reverse=True)[:TOP_N]
    ]

    return ok({
        "total_ventas": total_ventas,
        "ventas_por_tienda": [{"tienda_id": t, "total": v} for t, v in ventas_por_tienda.items()],
        "productos_mas_vendidos": productos_mas_vendidos,
        "productos_agotados": productos_agotados,
        "clientes_top": clientes_top,
        "pedidos_por_estado": dict(pedidos_por_estado),
    })
