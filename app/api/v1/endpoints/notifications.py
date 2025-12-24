from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.schemas.notification import NotificationResponse
from app.core.database import get_db
from app.core.security import get_current_user

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=List[NotificationResponse])
async def list_notifications(
    limit: int = 50,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Lister les notifications de l'entreprise"""
    notifications = await db.notification.find_many(
        where={"entreprise_id": current_user.entreprise_id},
        order={"created_at": "desc"},
        take=limit
    )
    return notifications


@router.get("/non-lues", response_model=List[NotificationResponse])
async def list_notifications_non_lues(
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Lister les notifications non lues"""
    notifications = await db.notification.find_many(
        where={
            "entreprise_id": current_user.entreprise_id,
            "statut": "EN_ATTENTE"
        },
        order={"created_at": "desc"}
    )
    return notifications


@router.patch("/{notification_id}/marquer-lue")
async def marquer_notification_lue(
    notification_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Marquer une notification comme lue"""
    notification = await db.notification.find_unique(where={"id": notification_id})
    
    if not notification or notification.entreprise_id != current_user.entreprise_id:
        raise HTTPException(status_code=404, detail="Notification non trouvée")
    
    updated = await db.notification.update(
        where={"id": notification_id},
        data={"statut": "RECUE"}
    )
    return updated


@router.delete("/{notification_id}")
async def supprimer_notification(
    notification_id: str,
    db=Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Supprimer une notification"""
    notification = await db.notification.find_unique(where={"id": notification_id})
    
    if not notification or notification.entreprise_id != current_user.entreprise_id:
        raise HTTPException(status_code=404, detail="Notification non trouvée")
    
    await db.notification.delete(where={"id": notification_id})
    return {"message": "Notification supprimée"}
