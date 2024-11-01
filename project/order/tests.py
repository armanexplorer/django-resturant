from django.test import TestCase
from django.urls import reverse

from .models import Item, Order, OrderItem
from .serializers import OrderSerializer


class OrderModelTest(TestCase):
    def setUp(self):
        self.item = Item.objects.create(name="Pizza", price=10.00)
        self.order = Order.objects.create(
            customer_name="John Doe",
            phone="1234567890",
            address="123 Street Name",
        )

    def test_order_creation(self):
        self.assertIsInstance(self.order, Order)

    def test_order_item_creation(self):
        order_item = OrderItem.objects.create(order=self.order, item=self.item, count=2)
        self.assertEqual(order_item.order, self.order)
        self.assertEqual(order_item.count, 2)


class OrderSerializerTest(TestCase):
    def test_order_serializer_valid_data(self):
        order_data = {
            "customer_name": "Jane Doe",
            "phone": "0987654321",
            "address": "456 Another St",
            "status": "new",
            "order_items": [{"item_id": self.item.id, "count": 1}],
        }
        serializer = OrderSerializer(data=order_data)
        self.assertTrue(serializer.is_valid())
        order = serializer.save()
        self.assertEqual(order.total_price, 10.00)  # Assuming the item price is 10.00


class OrderViewTest(TestCase):
    # def setUp(self):
    #     self.item = Item.objects.create(name='Pizza', price=10.00)
    #     self.order = Order.objects.create(
    #         customer_name='John Doe',
    #         phone='1234567890',
    #         address='123 Street Name',
    #         total_price=0,
    #         status='new'
    #     )

    def test_create_order(self):
        url = reverse("order-list")  # Adjust based on your URL configuration
        data = {
            "customer_name": "Jane Doe",
            "phone": "0987654321",
            "address": "456 Another St",
            "order_items": [
                {"item_id": self.item.id, "count": 2},
                {"item_id": self.item.id, "count": 1},
            ],
        }

        response = self.client.post(url, data, format="json")

        self.assertEqual(response.status_code, 201)  # Check for successful creation
        self.assertEqual(Order.objects.count(), 1)  # Ensure one order is created
        self.assertEqual(Order.objects.first().customer_name, "Jane Doe")

    def test_retrieve_order(self):
        order = Order.objects.create(
            customer_name="John Doe",
            phone="1234567890",
            address="123 Street Name",
        )
        url = reverse(
            "order-detail", args=[order.id]
        )  # Adjust based on your URL configuration

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)  # Check for successful retrieval
        self.assertEqual(response.data["customer_name"], "John Doe")

    def test_update_order_status(self):
        order = Order.objects.create(
            customer_name="John Doe",
            phone="1234567890",
            address="123 Street Name",
        )
        url = reverse(
            "order-detail", args=[order.id]
        )  # Adjust based on your URL configuration
        data = {"status": "delivered"}

        response = self.client.patch(url, data, format="json")

        self.assertEqual(response.status_code, 200)  # Check for successful update
        self.assertEqual(Order.objects.get(id=order.id).status, "delivered")

    def test_delete_order(self):
        order = Order.objects.create(
            customer_name="John Doe",
            phone="1234567890",
            address="123 Street Name",
        )
        url = reverse(
            "order-detail", args=[order.id]
        )  # Adjust based on your URL configuration

        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)  # Check for successful deletion
        self.assertEqual(Order.objects.count(), 0)  # Ensure no orders remain

    def test_list_orders(self):
        Order.objects.create(
            customer_name="John Doe",
            phone="1234567890",
            address="123 Street Name",
        )
        Order.objects.create(
            customer_name="Jane Doe",
            phone="0987654321",
            address="456 Another St",
        )
        url = reverse("order-list")  # Adjust based on your URL configuration

        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)  # Check for successful retrieval
        self.assertEqual(len(response.data), 2)  # Ensure both orders are returned
