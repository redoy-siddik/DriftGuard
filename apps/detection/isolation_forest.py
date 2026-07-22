import pickle
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from apps.telemetry.models import TelemetrySnapshot
from apps.detection.models import IsolationForestModel


class IsolationForestDetector:
    FEATURES = [
        'utilization_pct', 'memory_used_gb', 'temperature_c',
        'power_draw_w', 'ecc_errors', 'fan_speed_pct', 'sm_clock_mhz'
    ]
    MIN_TRAINING_SAMPLES = 200
    BASELINE_WINDOW = 2016   # 2016 × 5min = 7 days

    def __init__(self, node):
        self.node = node

    def train(self):
        qs = TelemetrySnapshot.objects.filter(node=self.node).order_by('-timestamp')[:self.BASELINE_WINDOW]
        snapshots = list(qs)
        if len(snapshots) < self.MIN_TRAINING_SAMPLES:
            return False

        data = [{f: getattr(s, f) for f in self.FEATURES} for s in snapshots]
        df = pd.DataFrame(data)
        X = self._build_feature_matrix(df)

        pipeline = Pipeline([
            ('scaler', StandardScaler()),
            ('model', IsolationForest(
                contamination=0.05,
                random_state=42,
                n_estimators=100
            ))
        ])
        pipeline.fit(X)

        model_bytes = pickle.dumps(pipeline)

        IsolationForestModel.objects.update_or_create(
            node=self.node,
            defaults={
                'model_blob': model_bytes,
                'feature_names': self.FEATURES,
                'training_samples': len(snapshots),
                'contamination': 0.05,
                'status': 'trained'
            }
        )
        return True

    def predict(self, current_df):
        pipeline = self._load_model()
        if pipeline is None:
            return None, None

        if current_df.empty:
            return False, 0.0

        # Mean feature vector of current window
        feature_means = [current_df[f].mean() for f in self.FEATURES]
        X_cur = np.array([feature_means])

        # predict returns -1 for anomaly, 1 for normal
        preds = pipeline.predict(X_cur)
        is_anomaly = bool(preds[0] == -1)

        # decision_function returns raw anomaly score (lower means more anomalous)
        raw_score = float(pipeline.decision_function(X_cur)[0])

        return is_anomaly, raw_score

    def _load_model(self):
        try:
            model_record = IsolationForestModel.objects.get(node=self.node, status='trained')
            if not model_record.model_blob:
                return None
            pipeline = pickle.loads(model_record.model_blob)
            return pipeline
        except (IsolationForestModel.DoesNotExist, Exception):
            return None

    def _build_feature_matrix(self, df):
        return df[self.FEATURES].to_numpy()
