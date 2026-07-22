from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from apps.cluster.models import GPUNode

class APITests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.node = GPUNode.objects.create(
            node_id='gpu-test-node',
            hostname='test-host-api',
            gpu_model='NVIDIA A100',
            total_memory_gb=80.0
        )

    def test_node_list_api(self):
        response = self.client.get('/api/v1/nodes/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_node_detail_api(self):
        response = self.client.get('/api/v1/nodes/gpu-test-node/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['node_id'], 'gpu-test-node')

    def test_dashboard_summary_api(self):
        response = self.client.get('/api/v1/dashboard/summary/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_nodes', response.data)

    def test_dashboard_views(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get('/nodes/gpu-test-node/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.get('/alerts/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
