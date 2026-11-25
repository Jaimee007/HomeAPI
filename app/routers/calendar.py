from fastapi import APIRouter, HTTPException, Query
from .. import calendar_config, calendar_sync
from ..schemas import CalendarStatusOut, CalendarSyncOut

router = APIRouter(prefix="/calendar", tags=["calendar"])


@router.get("/status", response_model=CalendarStatusOut)
def estado_calendario():
    """Estado de la integración: si está activa y qué queda por sincronizar"""
    return calendar_sync.queue_status()


@router.post("/sync", response_model=CalendarSyncOut)
def sincronizar_calendario(
    mes: int = Query(None, ge=1, le=12),
    año: int = Query(None, ge=2000),
):
    """Forzar una sincronización.

    Sin mes/año procesa la cola pendiente. Con mes/año reencola el mes completo
    y lo procesa: es la reconciliación completa, útil para el backfill inicial.
    """
    if not calendar_config.is_enabled():
        raise HTTPException(status_code=400, detail="Integración de Google Calendar desactivada")

    if (mes is None) != (año is None):
        raise HTTPException(status_code=400, detail="Indica mes y año juntos, o ninguno")

    queued = calendar_sync.enqueue_month(mes, año) if mes else 0

    try:
        results = calendar_sync.drain_queue(limit=500)
    except calendar_sync.CalendarUnavailable as e:
        raise HTTPException(status_code=503, detail=str(e))

    return {'queued': queued, 'results': results, 'pending': calendar_sync.queue_status()['pending']}
