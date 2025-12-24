from fastapi import HTTPException, status


class StockFlowException(HTTPException):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST):
        super().__init__(status_code=status_code, detail=detail)


class ArticleNotFoundException(StockFlowException):
    def __init__(self, article_id: str):
        super().__init__(
            detail=f"Article {article_id} not found",
            status_code=status.HTTP_404_NOT_FOUND
        )


class MagasinNotFoundException(StockFlowException):
    def __init__(self, magasin_id: str):
        super().__init__(
            detail=f"Magasin {magasin_id} not found",
            status_code=status.HTTP_404_NOT_FOUND
        )


class InsufficientStockException(StockFlowException):
    def __init__(self, article_code: str, available: int, requested: int):
        super().__init__(
            detail=f"Stock insuffisant pour {article_code}. Disponible: {available}, Demandé: {requested}",
            status_code=status.HTTP_400_BAD_REQUEST
        )


class UnauthorizedException(StockFlowException):
    def __init__(self, detail: str = "Non autorisé"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_401_UNAUTHORIZED
        )


class ForbiddenException(StockFlowException):
    def __init__(self, detail: str = "Accès interdit"):
        super().__init__(
            detail=detail,
            status_code=status.HTTP_403_FORBIDDEN
        )
