"""
Role-Based Access Control (RBAC) enforcement
Provides decorators and utilities for permission checking
"""

from functools import wraps
from typing import Callable, List, Any
from fastapi import Depends, HTTPException, status
from app.core.security import get_current_user
import logging

logger = logging.getLogger(__name__)


class Permission:
    """Permission definitions for the system"""
    
    # Article permissions
    CREATE_ARTICLE = "create_article"
    READ_ARTICLE = "read_article"
    UPDATE_ARTICLE = "update_article"
    DELETE_ARTICLE = "delete_article"
    
    # Stock movement permissions
    CREATE_MOUVEMENT = "create_mouvement"
    READ_MOUVEMENT = "read_mouvement"
    UPDATE_MOUVEMENT = "update_mouvement"
    DELETE_MOUVEMENT = "delete_mouvement"
    
    # Supplier permissions
    CREATE_FOURNISSEUR = "create_fournisseur"
    READ_FOURNISSEUR = "read_fournisseur"
    UPDATE_FOURNISSEUR = "update_fournisseur"
    DELETE_FOURNISSEUR = "delete_fournisseur"
    
    # Purchase order permissions
    CREATE_BON_COMMANDE = "create_bon_commande"
    READ_BON_COMMANDE = "read_bon_commande"
    UPDATE_BON_COMMANDE = "update_bon_commande"
    VALIDATE_BON_COMMANDE = "validate_bon_commande"
    DELETE_BON_COMMANDE = "delete_bon_commande"
    
    # Dashboard & analytics
    READ_DASHBOARD = "read_dashboard"
    READ_ANALYTICS = "read_analytics"
    READ_REPORTS = "read_reports"
    
    # Settings & admin
    MANAGE_USERS = "manage_users"
    MANAGE_WAREHOUSES = "manage_warehouses"
    MANAGE_SETTINGS = "manage_settings"
    VIEW_AUDIT_LOG = "view_audit_log"
    
    # Warehouse/Magasin permissions
    CREATE_MAGASIN = "create_magasin"
    READ_MAGASIN = "read_magasin"
    UPDATE_MAGASIN = "update_magasin"
    DELETE_MAGASIN = "delete_magasin"
    
    # Sales permissions
    CREATE_VENTE = "create_vente"
    READ_VENTE = "read_vente"
    UPDATE_VENTE = "update_vente"
    DELETE_VENTE = "delete_vente"
    
    # Transfer permissions
    CREATE_TRANSFERT = "create_transfert"
    READ_TRANSFERT = "read_transfert"
    UPDATE_TRANSFERT = "update_transfert"
    DELETE_TRANSFERT = "delete_transfert"
    
    # Other permissions
    CREATE_INVENTAIRE = "create_inventaire"
    READ_INVENTAIRE = "read_inventaire"
    CREATE_NOTIFICATION = "create_notification"
    READ_NOTIFICATION = "read_notification"
    READ_PEREMPTION = "read_peremption"
    READ_PREVISION = "read_prevision"
    CREATE_EXPORT = "create_export"
    READ_EXPORT = "read_export"


# Role to permissions mapping
ROLE_PERMISSIONS = {
    "PATRON": [
        # Patron has full access
        Permission.CREATE_ARTICLE,
        Permission.READ_ARTICLE,
        Permission.UPDATE_ARTICLE,
        Permission.DELETE_ARTICLE,
        Permission.CREATE_MOUVEMENT,
        Permission.READ_MOUVEMENT,
        Permission.UPDATE_MOUVEMENT,
        Permission.DELETE_MOUVEMENT,
        Permission.CREATE_FOURNISSEUR,
        Permission.READ_FOURNISSEUR,
        Permission.UPDATE_FOURNISSEUR,
        Permission.DELETE_FOURNISSEUR,
        Permission.CREATE_BON_COMMANDE,
        Permission.READ_BON_COMMANDE,
        Permission.UPDATE_BON_COMMANDE,
        Permission.VALIDATE_BON_COMMANDE,
        Permission.DELETE_BON_COMMANDE,
        Permission.READ_DASHBOARD,
        Permission.READ_ANALYTICS,
        Permission.READ_REPORTS,
        Permission.MANAGE_USERS,
        Permission.MANAGE_WAREHOUSES,
        Permission.MANAGE_SETTINGS,
        Permission.VIEW_AUDIT_LOG,
        Permission.CREATE_MAGASIN,
        Permission.READ_MAGASIN,
        Permission.UPDATE_MAGASIN,
        Permission.DELETE_MAGASIN,
    ],
    "GERANT": [
        # Manager has most permissions except user management
        Permission.CREATE_ARTICLE,
        Permission.READ_ARTICLE,
        Permission.UPDATE_ARTICLE,
        Permission.DELETE_ARTICLE,
        Permission.CREATE_MOUVEMENT,
        Permission.READ_MOUVEMENT,
        Permission.UPDATE_MOUVEMENT,
        Permission.DELETE_MOUVEMENT,
        Permission.CREATE_FOURNISSEUR,
        Permission.READ_FOURNISSEUR,
        Permission.UPDATE_FOURNISSEUR,
        Permission.DELETE_FOURNISSEUR,
        Permission.CREATE_BON_COMMANDE,
        Permission.READ_BON_COMMANDE,
        Permission.UPDATE_BON_COMMANDE,
        Permission.VALIDATE_BON_COMMANDE,
        Permission.DELETE_BON_COMMANDE,
        Permission.READ_DASHBOARD,
        Permission.READ_ANALYTICS,
        Permission.READ_REPORTS,
        Permission.MANAGE_WAREHOUSES,
        Permission.VIEW_AUDIT_LOG,
        Permission.CREATE_MAGASIN,
        Permission.READ_MAGASIN,
        Permission.UPDATE_MAGASIN,
        Permission.DELETE_MAGASIN,
    ],
    "EMPLOYE": [
        # Employee can do basic operations
        Permission.READ_ARTICLE,
        Permission.CREATE_MOUVEMENT,
        Permission.READ_MOUVEMENT,
        Permission.READ_FOURNISSEUR,
        Permission.READ_BON_COMMANDE,
        Permission.READ_DASHBOARD,
        Permission.READ_MAGASIN,
    ],
    "COMPTABLE": [
        # Accountant has read-only access to financial data
        Permission.READ_ARTICLE,
        Permission.READ_MOUVEMENT,
        Permission.READ_FOURNISSEUR,
        Permission.READ_BON_COMMANDE,
        Permission.READ_ANALYTICS,
        Permission.READ_REPORTS,
        Permission.VIEW_AUDIT_LOG,
        Permission.READ_MAGASIN,
    ]
}


def get_user_permissions(role: str) -> List[str]:
    """Get list of permissions for a role"""
    return ROLE_PERMISSIONS.get(role.upper(), [])


async def verify_permission(
    current_user: dict,
    required_permission: str
) -> bool:
    """Verify that user has required permission"""
    user_permissions = get_user_permissions(current_user.get("role"))
    return required_permission in user_permissions


def check_permission(required_permission: str):
    """Dependency to check permission"""
    async def check(current_user: dict = Depends(get_current_user)):
        has_permission = await verify_permission(current_user, required_permission)
        
        if not has_permission:
            logger.warning(
                f"Permission denied: User {current_user['id']} "
                f"(role: {current_user['role']}) attempted access to {required_permission}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Vous n'avez pas la permission pour cette action"
            )
        
        return current_user
    
    return check


def require_permission(permission: str):
    """Decorator for endpoints requiring specific permission"""
    async def permission_checker(current_user: dict = Depends(check_permission(permission))):
        return current_user
    
    return permission_checker


def require_role(*allowed_roles: str):
    """Dependency to check if user has one of the allowed roles"""
    async def verify_role(current_user: dict = Depends(get_current_user)):
        user_role = current_user.get("role", "").upper()
        allowed = [r.upper() for r in allowed_roles]
        
        if user_role not in allowed:
            logger.warning(
                f"Role check failed: User {current_user['id']} "
                f"(role: {user_role}) not in {allowed}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Accès refusé. Rôles requis: {', '.join(allowed_roles)}"
            )
        
        return current_user
    
    return verify_role
