"""
model_store.py

Handles persistence and retrieval of trained scikit-learn IsolationForest models.
Models are serialized with joblib (preferred over pickle for sklearn objects)
and stored in two places:
  1. Database (IsolationForestModel.model_blob) — source of truth
  2. Local filesystem cache (/tmp/driftguard_models/<node_id>.joblib) — fast load

On load: check filesystem cache first; if missing or stale vs DB, reload from DB and refresh cache.
On save: write to DB first, then write filesystem cache.
"""

import io
import os
import logging
from pathlib import Path
from datetime import datetime, timezone

import joblib

logger = logging.getLogger(__name__)

MODEL_CACHE_DIR = Path(os.environ.get('MODEL_CACHE_DIR', '/tmp/driftguard_models'))
MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)


class ModelStore:
    def __init__(self, node):
        self.node = node
        self.cache_path = MODEL_CACHE_DIR / f"{node.node_id}.joblib"

    def save(self, pipeline, feature_names, training_samples, contamination=0.05):
        """
        Serialize pipeline (StandardScaler + IsolationForest) and persist to DB + cache.
        Args:
            pipeline: fitted sklearn Pipeline object
            feature_names: list of feature column names used during training
            training_samples: int, number of samples used to train
            contamination: float, contamination parameter used
        Returns:
            IsolationForestModel instance
        """
        from apps.detection.models import IsolationForestModel

        # Serialize to bytes using joblib
        buffer = io.BytesIO()
        joblib.dump(pipeline, buffer)
        model_bytes = buffer.getvalue()

        # Save to database
        obj, created = IsolationForestModel.objects.update_or_create(
            node=self.node,
            defaults={
                'model_blob': model_bytes,
                'feature_names': feature_names,
                'training_samples': training_samples,
                'contamination': contamination,
                'status': 'trained',
            }
        )

        # Write filesystem cache
        try:
            joblib.dump(pipeline, self.cache_path)
            logger.info(f"Model cached to {self.cache_path}")
        except Exception as e:
            logger.warning(f"Filesystem cache write failed for {self.node.node_id}: {e}")

        action = "created" if created else "updated"
        logger.info(f"Model {action} in DB for node {self.node.node_id} "
                    f"({training_samples} samples, contamination={contamination})")
        return obj

    def load(self):
        """
        Load pipeline from filesystem cache if fresh, otherwise from DB.
        Returns:
            (pipeline, IsolationForestModel) tuple, or (None, None) if no model exists
        """
        from apps.detection.models import IsolationForestModel

        try:
            db_model = IsolationForestModel.objects.get(node=self.node, status='trained')
        except IsolationForestModel.DoesNotExist:
            logger.warning(f"No trained model found in DB for node {self.node.node_id}")
            return None, None

        # Try filesystem cache
        if self._cache_is_fresh(db_model):
            try:
                pipeline = joblib.load(self.cache_path)
                logger.debug(f"Model loaded from cache for {self.node.node_id}")
                return pipeline, db_model
            except Exception as e:
                logger.warning(f"Cache load failed for {self.node.node_id}: {e}")

        # Fall back to DB
        return self._load_from_db(db_model), db_model

    def _load_from_db(self, db_model):
        """Deserialize from DB blob and refresh filesystem cache."""
        buffer = io.BytesIO(bytes(db_model.model_blob))
        pipeline = joblib.load(buffer)

        # Refresh filesystem cache
        try:
            joblib.dump(pipeline, self.cache_path)
        except Exception as e:
            logger.warning(f"Cache refresh failed for {self.node.node_id}: {e}")

        logger.info(f"Model loaded from DB for {self.node.node_id}")
        return pipeline

    def _cache_is_fresh(self, db_model):
        """Returns True if filesystem cache exists and is newer than DB model."""
        if not self.cache_path.exists():
            return False
        cache_mtime = datetime.fromtimestamp(
            self.cache_path.stat().st_mtime, tz=timezone.utc
        )
        return cache_mtime >= db_model.trained_at

    def delete(self):
        """Remove model from DB and filesystem cache."""
        from apps.detection.models import IsolationForestModel
        IsolationForestModel.objects.filter(node=self.node).delete()
        if self.cache_path.exists():
            self.cache_path.unlink()
        logger.info(f"Model deleted for node {self.node.node_id}")

    @staticmethod
    def clear_all_caches():
        """Wipe all filesystem cache files. Does not touch DB."""
        for f in MODEL_CACHE_DIR.glob("*.joblib"):
            f.unlink()
        logger.info("All model caches cleared")


def get_model_store(node):
    """Convenience factory function."""
    return ModelStore(node)
