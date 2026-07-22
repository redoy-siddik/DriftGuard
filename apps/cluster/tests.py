from django.test import TestCase
from apps.cluster.models import GPUNode

class GPUNodeModelTest(TestCase):
    def setUp(self):
        self.node = GPUNode.objects.create(
            node_id='test-gpu-01',
            hostname='test-host-01',
            gpu_model='NVIDIA A100-SXM4-80GB',
            total_memory_gb=80.0,
            is_active=True
        )

    def test_gpu_node_creation(self):
        self.assertEqual(self.node.node_id, 'test-gpu-01')
        self.assertEqual(self.node.current_status, 'normal')
        self.assertTrue(self.node.is_active)
        self.assertEqual(str(self.node), 'test-gpu-01 (NVIDIA A100-SXM4-80GB)')
