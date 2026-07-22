from .models import IsolationForestModel


class ModelStore:
    """Helper for model persistence and metadata inspection."""

    @staticmethod
    def get_model_status(node):
        try:
            model = IsolationForestModel.objects.get(node=node)
            return {
                'status': model.status,
                'trained_at': model.trained_at,
                'training_samples': model.training_samples,
                'contamination': model.contamination,
            }
        except IsolationForestModel.DoesNotExist:
            return {
                'status': 'not_trained',
                'trained_at': None,
                'training_samples': 0,
                'contamination': 0.05,
            }
