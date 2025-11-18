"""AI pricing helper utilities."""
from __future__ import annotations

from typing import List

import numpy as np
from sklearn.neighbors import KNeighborsRegressor


class PriceRecommendationService:
    """Provide lightweight kNN-based price suggestions."""

    def __init__(self) -> None:
        self._knn = KNeighborsRegressor(n_neighbors=5)
        self._is_fitted = False

    def fit(self, feature_matrix: List[List[float]], targets: List[float]) -> None:
        """Fit the KNN model with historical data."""

        matrix = np.array(feature_matrix)
        y = np.array(targets)
        self._knn.fit(matrix, y)
        self._is_fitted = True

    def suggest_price(self, features: List[float]) -> float:
        """Return a predicted price based on current features."""

        if not self._is_fitted:
            raise RuntimeError("Model not trained yet")
        prediction = self._knn.predict([features])
        return float(prediction[0])


def get_default_price_service() -> PriceRecommendationService:
    """Return a singleton-like instance for dependency injection."""

    return PriceRecommendationService()
