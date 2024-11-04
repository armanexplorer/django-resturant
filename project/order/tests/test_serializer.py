from decimal import Decimal
from django.test import TestCase
from rest_framework.exceptions import ValidationError
from order.models import Order, Item, OrderItem
from order.serializers import (
    BaseItemSerializer,
    OrderSerializer,
    OrderItemSerializer,
    BaseOrderSerializer,
)


class OrderSerializerTests(TestCase):
    def setUp(self):
        # Create test items
        self.item1 = Item.objects.create(
            name="Pizza", price=Decimal("10.99"), quantity=50
        )
        self.item2 = Item.objects.create(
            name="Burger", price=Decimal("8.99"), quantity=30
        )

        # Create a basic order
        self.order = Order.objects.create(
            customer_name="John Doe",
            phone="1234567890",
            address="123 Main St",
            status="new",
        )

    def test_item_serializer(self):
        """Test BaseItemSerializer serialization"""
        serializer = BaseItemSerializer(self.item1)
        expected_data = {"id": self.item1.id, "name": "Pizza", "price": "10.99"}
        self.assertEqual(serializer.data, expected_data)

    def test_base_order_serializer(self):
        """Test BaseOrderSerializer serialization"""
        serializer = BaseOrderSerializer(self.order)
        self.assertEqual(serializer.data["customer_name"], "John Doe")
        self.assertEqual(serializer.data["phone"], "1234567890")
        self.assertEqual(serializer.data["status"], "new")

    def test_order_item_serializer_validation(self):
        """Test OrderItemSerializer count validation"""
        data = {"item_id": self.item1.id, "count": 0}
        serializer = OrderItemSerializer(data=data)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_order_item_serializer_read(self):
        """Test OrderItemSerializer read operations"""
        order_item = OrderItem.objects.create(
            order=self.order, item=self.item1, count=2
        )
        serializer = OrderItemSerializer(order_item)
        self.assertEqual(serializer.data["count"], 2)
        self.assertEqual(serializer.data["item"]["name"], "Pizza")

    def test_order_serializer_create(self):
        """Test OrderSerializer create operation"""
        data = {
            "customer_name": "Jane Smith",
            "phone": "9876543210",
            "address": "456 Oak St",
            "order_items": [
                {"item_id": self.item1.id, "count": 2},
                {"item_id": self.item2.id, "count": 1},
            ],
        }
        serializer = OrderSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        order = serializer.save()

        expected_total = (self.item1.price * 2) + (self.item2.price * 1)
        self.assertEqual(order.total_price, expected_total)
        self.assertEqual(order.order_items.count(), 2)

    def test_order_serializer_update(self):
        """Test OrderSerializer update operation"""
        # Create initial order items
        OrderItem.objects.create(order=self.order, item=self.item1, count=2)

        # Update data
        data = {
            "customer_name": "Jane Smith",
            "phone": "9876543210",
            "address": "456 Oak St",
            "order_items": [{"item_id": self.item2.id, "count": 3}],
        }

        serializer = OrderSerializer(self.order, data=data)
        self.assertTrue(serializer.is_valid())
        updated_order = serializer.save()

        self.assertEqual(updated_order.customer_name, "Jane Smith")
        self.assertEqual(updated_order.order_items.count(), 1)
        self.assertEqual(updated_order.total_price, self.item2.price * 3)

    def test_order_serializer_validate_stock(self):
        """Test OrderSerializer stock validation"""
        data = {
            "customer_name": "Jane Smith",
            "phone": "9876543210",
            "address": "456 Oak St",
            "order_items": [
                {"item_id": self.item1.id, "count": 51}  # Exceeds quantity
            ],
        }

        serializer = OrderSerializer(data=data)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_order_serializer_update_stock_validation(self):
        """Test OrderSerializer stock validation during update"""
        # Create initial order
        order = Order.objects.create(
            customer_name="Test User",
            phone="1234567890",
            address="Test Address",
            status="new",
        )
        OrderItem.objects.create(order=order, item=self.item1, count=10)

        # Create another order consuming stock
        other_order = Order.objects.create(
            customer_name="Other User",
            phone="0987654321",
            address="Other Address",
            status="new",
        )
        OrderItem.objects.create(order=other_order, item=self.item1, count=35)

        # Try to update first order with remaining stock + 1
        data = {
            "customer_name": "Test User",
            "phone": "1234567890",
            "address": "Test Address",
            "order_items": [
                # Should fail (50 - (35 + 10) < 6)
                {"item_id": self.item1.id, "count": 16}
            ],
        }

        serializer = OrderSerializer(order, data=data)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_order_serializer_readonly_fields(self):
        """Test OrderSerializer read-only fields"""
        data = {
            "customer_name": "Jane Smith",
            "phone": "9876543210",
            "address": "456 Oak St",
            "status": "delivered",  # Should be ignored
            "total_price": "100.00",  # Should be ignored
            "order_items": [{"item_id": self.item1.id, "count": 2}],
        }

        serializer = OrderSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        order = serializer.save()

        self.assertEqual(order.status, "new")  # Default status
        self.assertEqual(order.total_price, self.item1.price * 2)  # Calculated price

    def test_order_serializer_partial_update(self):
        """Test OrderSerializer partial update"""
        OrderItem.objects.create(order=self.order, item=self.item1, count=2)
        initial_total = self.order.total_price

        data = {"customer_name": "New Name"}
        serializer = OrderSerializer(self.order, data=data, partial=True)
        self.assertTrue(serializer.is_valid())
        updated_order = serializer.save()

        self.assertEqual(updated_order.customer_name, "New Name")
        self.assertEqual(updated_order.total_price, initial_total)
        self.assertEqual(updated_order.order_items.count(), 1)

    def test_order_serializer_empty_order_items(self):
        """Test OrderSerializer with empty order items"""
        data = {
            "customer_name": "Jane Smith",
            "phone": "9876543210",
            "address": "456 Oak St",
            "order_items": [],  # Should not be empty list
        }

        serializer = OrderSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_order_serializer_null_order_items(self):
        """Test OrderSerializer with empty order items"""
        data = {
            "customer_name": "Jane Smith",
            "phone": "9876543210",
            "address": "456 Oak St",
            "order_items": None,  # Should not be empty list
        }

        serializer = OrderSerializer(data=data)
        self.assertFalse(serializer.is_valid())

    def test_order_serializer_invalid_item_id(self):
        """Test OrderSerializer with invalid item ID"""
        data = {
            "customer_name": "Jane Smith",
            "phone": "9876543210",
            "address": "456 Oak St",
            "order_items": [{"item_id": 999, "count": 1}],  # Non-existent item ID
        }

        serializer = OrderSerializer(data=data)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)

    def test_order_serializer_duplicate_items(self):
        """Test OrderSerializer with duplicate items"""
        data = {
            "customer_name": "Jane Smith",
            "phone": "9876543210",
            "address": "456 Oak St",
            "order_items": [
                {"item_id": self.item1.id, "count": 1},
                {"item_id": self.item1.id, "count": 2},
            ],
        }

        serializer = OrderSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        order = serializer.save()

        # Both items should be created separately
        self.assertEqual(order.order_items.count(), 2)
        self.assertEqual(order.total_price, self.item1.price * 3)

    def test_order_serializer_bulk_items(self):
        """Test OrderSerializer with multiple items"""
        data = {
            "customer_name": "Jane Smith",
            "phone": "9876543210",
            "address": "456 Oak St",
            "order_items": [
                {"item_id": self.item1.id, "count": 2},
                {"item_id": self.item2.id, "count": 3},
            ],
        }

        serializer = OrderSerializer(data=data)
        self.assertTrue(serializer.is_valid())
        order = serializer.save()

        expected_total = (self.item1.price * 2) + (self.item2.price * 3)
        self.assertEqual(order.total_price, expected_total)
        self.assertEqual(order.order_items.count(), 2)

    def test_order_item_serializer_negative_count(self):
        """Test OrderItemSerializer with negative count"""
        data = {"item_id": self.item1.id, "count": -1}
        serializer = OrderItemSerializer(data=data)
        with self.assertRaises(ValidationError):
            serializer.is_valid(raise_exception=True)
