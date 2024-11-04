from decimal import Decimal
from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from order.models import Order, Item, OrderItem


class OrderViewSetTests(APITestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        # Create test items
        self.item1 = Item.objects.create(
            name="Pizza", price=Decimal("10.99"), quantity=50
        )
        self.item2 = Item.objects.create(
            name="Burger", price=Decimal("8.99"), quantity=30
        )

        # Create test order
        self.order = Order.objects.create(
            customer_name="John Doe",
            phone="1234567890",
            address="123 Main St",
            status="new",
        )
        OrderItem.objects.create(order=self.order, item=self.item1, count=2)

        # Set up API client
        self.client = APIClient()
        self.orders_url = reverse("order-list")
        self.order_detail_url = reverse("order-detail", kwargs={"pk": self.order.pk})

    def test_list_orders_unauthenticated(self):
        """Test that unauthenticated users can list orders"""
        response = self.client.get(self.orders_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)

    def test_retrieve_order_unauthenticated(self):
        """Test that unauthenticated users can retrieve specific orders"""
        response = self.client.get(self.order_detail_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["customer_name"], "John Doe")

    def test_create_order_unauthenticated(self):
        """Test that unauthenticated users cannot create orders"""
        data = {
            "customer_name": "Jane Smith",
            "phone": "9876543210",
            "address": "456 Oak St",
            "order_items": [{"item_id": self.item1.id, "count": 1}],
        }
        response = self.client.post(self.orders_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_order_unauthenticated(self):
        """Test that unauthenticated users cannot update orders"""
        data = {"customer_name": "Jane Smith"}
        response = self.client.put(self.order_detail_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_partial_update_order_unauthenticated(self):
        """Test that unauthenticated users cannot partially update orders"""
        data = {"customer_name": "Jane Smith"}
        response = self.client.patch(self.order_detail_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_create_order_authenticated(self):
        """Test that authenticated users can create orders"""
        self.client.force_authenticate(user=self.user)
        data = {
            "customer_name": "Jane Smith",
            "phone": "9876543210",
            "address": "456 Oak St",
            "order_items": [{"item_id": self.item1.id, "count": 1}],
        }
        response = self.client.post(self.orders_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Order.objects.count(), 2)
        self.assertEqual(response.data["customer_name"], "Jane Smith")

    def test_update_order_authenticated(self):
        """Test that authenticated users can update orders"""
        self.client.force_authenticate(user=self.user)
        data = {
            "customer_name": "Jane Smith",
            "phone": "9876543210",
            "address": "456 Oak St",
            "order_items": [{"item_id": self.item2.id, "count": 2}],
        }
        response = self.client.put(self.order_detail_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.customer_name, "Jane Smith")
        self.assertEqual(self.order.order_items.count(), 1)

    def test_partial_update_order_authenticated(self):
        """Test that authenticated users can partially update orders"""
        self.client.force_authenticate(user=self.user)
        data = {"customer_name": "Jane Smith"}
        response = self.client.patch(self.order_detail_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.customer_name, "Jane Smith")

    def test_list_orders_pagination(self):
        """Test orders list pagination"""
        # Create 11 additional orders (12 total)
        for i in range(11):
            Order.objects.create(
                customer_name=f"Customer {i}",
                phone="1234567890",
                address="Test Address",
                status="new",
            )

        response = self.client.get(self.orders_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue("results" in response.data)
        self.assertTrue("count" in response.data)
        self.assertEqual(response.data["count"], 12)

    def test_retrieve_nonexistent_order(self):
        """Test retrieving a non-existent order"""
        url = reverse("order-detail", kwargs={"pk": 99999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_create_order_invalid_data(self):
        """Test creating order with invalid data"""
        self.client.force_authenticate(user=self.user)
        data = {
            "customer_name": "",  # Invalid: empty name
            "phone": "9876543210",
            "address": "456 Oak St",
        }
        response = self.client.post(self.orders_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_order_invalid_items(self):
        """Test updating order with invalid items"""
        self.client.force_authenticate(user=self.user)
        data = {
            "customer_name": "Jane Smith",
            "phone": "9876543210",
            "address": "456 Oak St",
            "order_items": [{"item_id": 99999, "count": 1}],  # Non-existent item
        }
        response = self.client.put(self.order_detail_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_order_insufficient_stock(self):
        """Test creating order with insufficient stock"""
        self.client.force_authenticate(user=self.user)
        data = {
            "customer_name": "Jane Smith",
            "phone": "9876543210",
            "address": "456 Oak St",
            "order_items": [
                {"item_id": self.item1.id, "count": 51}  # Exceeds quantity
            ],
        }
        response = self.client.post(self.orders_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_update_order_read_only_fields(self):
        """Test updating read-only fields"""
        self.client.force_authenticate(user=self.user)
        data = {
            "customer_name": "Jane Smith",
            "status": "delivered",  # Should be ignored
            "total_price": "100.00",  # Should be ignored
        }
        response = self.client.patch(self.order_detail_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.order.refresh_from_db()
        self.assertEqual(self.order.status, "new")  # Status shouldn't change

    def test_create_order_response_structure(self):
        """Test the structure of create order response"""
        self.client.force_authenticate(user=self.user)
        data = {
            "customer_name": "Jane Smith",
            "phone": "9876543210",
            "address": "456 Oak St",
            "order_items": [{"item_id": self.item1.id, "count": 1}],
        }
        response = self.client.post(self.orders_url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertIn("customer_name", response.data)
        self.assertIn("total_price", response.data)
        self.assertIn("order_items", response.data)
        self.assertIn("created_at", response.data)
