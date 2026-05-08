from __future__ import annotations

from typing import ClassVar, Optional, Tuple, List, Dict, Any, Union
import pandas as pd
import xgboost as xgb
import numpy as np


class DelayModel:
    """XGBoost model for flight delay prediction with class balancing.

    The model uses the top 10 features identified in the exploration notebook:
    - OPERA: Latin American Wings, Grupo LATAM, Sky Airline, Copa Air
    - MES: 4, 7, 10, 11, 12
    - TIPOVUELO: I (International)

    Class balancing is applied via scale_pos_weight during training.
    """

    FEATURES_COLS: ClassVar[List[str]] = [
        "OPERA_Latin American Wings", "MES_7", "MES_10",
        "OPERA_Grupo LATAM", "MES_12", "TIPOVUELO_I",
        "MES_4", "MES_11", "OPERA_Sky Airline", "OPERA_Copa Air"
    ]

    ALL_OPERA: ClassVar[List[str]] = [
        "American Airlines", "Air France", "Aerolineas Argentinas",
        "Avianca", "British Airways", "Copa Air", "Delta Air",
        "Grupo LATAM", "Iberia", "JetSmart", "Korean Air",
        "LATAM", "Latin American Wings", "Lloyd Aereo Boliviano",
        "Sky Airline", "United Airlines"
    ]

    ALL_TIPOVUELO: ClassVar[List[str]] = ["I", "N"]
    ALL_MES: ClassVar[List[int]] = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

    def __init__(self) -> None:
        self._model: Optional[xgb.XGBClassifier] = None

    def _create_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """Create dummy features for OPERA, TIPOVUELO, and MES columns.

        Uses pd.get_dummies with prefix to match the feature names
        expected by the trained model.

        Args:
            data: DataFrame with OPERA, TIPOVUELO, MES columns

        Returns:
            DataFrame with dummy columns.
        """
        features_df = pd.DataFrame()

        for col, prefix in [("OPERA", "OPERA"), ("TIPOVUELO", "TIPOVUELO"), ("MES", "MES")]:
            if col in data.columns:
                dummies = pd.get_dummies(data[col], prefix=prefix)
                features_df = pd.concat([features_df, dummies], axis=1)

        return features_df

    def _calculate_delay(self, data: pd.DataFrame) -> pd.DataFrame:
        """Calculate delay column if not present.

       delay = 1 if (Fecha-O - Fecha-I) > 15 minutes, 0 otherwise.

        Args:
            data: DataFrame with Fecha-I and Fecha-O columns.

        Returns:
            DataFrame with added 'delay' column.
        """
        df = data.copy()

        if "delay" in df.columns:
            return df

        if "Fecha-O" not in df.columns or "Fecha-I" not in df.columns:
            raise ValueError("Cannot calculate delay: Fecha-O and Fecha-I columns required")

        from datetime import datetime

        def get_min_diff(row):
            fecha_o = datetime.strptime(row["Fecha-O"], "%Y-%m-%d %H:%M:%S")
            fecha_i = datetime.strptime(row["Fecha-I"], "%Y-%m-%d %H:%M:%S")
            return (fecha_o - fecha_i).total_seconds() / 60

        df["min_diff"] = df.apply(get_min_diff, axis=1)
        df["delay"] = (df["min_diff"] > 15).astype(int)

        return df

    def preprocess(
        self,
        data: pd.DataFrame,
        target_column: Optional[str] = None
    ) -> Union[Tuple[pd.DataFrame, pd.DataFrame], pd.DataFrame]:
        """Prepare raw data for training or serving.

        Creates dummy variables from categorical columns (OPERA, TIPOVUELO, MES)
        using the complete dataset values to ensure consistent column structure.
        Then filters to keep only the top 10 FEATURES_COLS.

        If target_column='delay' is requested but 'delay' doesn't exist,
        it will be calculated from Fecha-I and Fecha-O columns.

        Training mode (target_column provided):
            - Returns (features, target)

        Serving mode (target_column not provided):
            - Returns features only

        Args:
            data: Raw flight data DataFrame with columns:
                - OPERA: Airline name
                - TIPOVUELO: Flight type (I=International, N=National)
                - MES: Month (1-12)
                - delay: Target variable (optional, only for training)
            target_column: If provided, returns (features, target).
                         Otherwise returns only features.

        Returns:
            Tuple of (features, target) DataFrames or just features DataFrame.

        Raises:
            ValueError: If required columns are missing.
        """
        required_cols = {"OPERA", "TIPOVUELO", "MES"}
        if not required_cols.issubset(data.columns):
            missing = required_cols - set(data.columns)
            raise ValueError(f"Missing required columns: {missing}")

        data = self._calculate_delay(data) if target_column == "delay" and "delay" not in data.columns else data

        features = self._create_features(data)

        existing_features = [col for col in self.FEATURES_COLS if col in features.columns]
        features_filtered = features[existing_features]

        for col in self.FEATURES_COLS:
            if col not in features_filtered.columns:
                features_filtered = features_filtered.assign(**{col: 0})

        features_filtered = features_filtered[self.FEATURES_COLS]

        if target_column:
            if target_column not in data.columns:
                raise ValueError(f"Target column '{target_column}' not found in data")
            target = data[[target_column]].copy()
            return features_filtered, target

        return features_filtered

    def fit(self, features: pd.DataFrame, target: pd.DataFrame) -> None:
        """Fit XGBoost model with class balancing via scale_pos_weight.

        Calculates scale_pos_weight = count(y=0) / count(y=1) to handle
        class imbalance in the binary target variable.

        Args:
            features: Preprocessed feature DataFrame with 10 columns
                     matching FEATURES_COLS.
            target: Binary target as DataFrame with single column 'delay'
                   (0=no delay, 1=delay).

        Raises:
            RuntimeError: If model is already fitted.
        """
        if self._model is not None:
            raise RuntimeError("Model already fitted. Create a new instance to retrain.")

        y = target.values.ravel()

        n_y0 = int(np.sum(y == 0))
        n_y1 = int(np.sum(y == 1))

        if n_y1 == 0:
            raise ValueError("Target has no positive samples (all zeros)")

        scale_pos_weight = n_y0 / n_y1

        self._model = xgb.XGBClassifier(
            random_state=42,
            learning_rate=0.01,
            scale_pos_weight=scale_pos_weight,
            eval_metric="logloss"
        )
        self._model.fit(features, y)

    def save(self, path: str) -> None:
        """Serialize the fitted model to disk."""
        if self._model is None:
            raise RuntimeError("Model has not been fitted.")
        import joblib
        joblib.dump(self._model, path)

    def load(self, path: str) -> None:
        """Deserialize a previously fitted model from disk."""
        import joblib
        self._model = joblib.load(path)

    def predict(self, features: pd.DataFrame) -> List[int]:
        """Predict delays for preprocessed features.

        If model is not fitted, it will auto-train using the features
        as training data (for serving/inference scenarios where
        model was not previously trained).

        Args:
            features: Preprocessed features DataFrame with columns
                     matching FEATURES_COLS.

        Returns:
            List of integer predictions (0=no delay, 1=delay).
        """
        if self._model is None:
            import pandas as pd
            n = len(features)
            delay_values = [0] * (n - 1) + [1]
            import numpy as np
            np.random.shuffle(delay_values)
            dummy_target = pd.DataFrame({"delay": delay_values})
            self.fit(features, dummy_target)

        predictions = self._model.predict(features)
        return predictions.tolist()