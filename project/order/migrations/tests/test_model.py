from decimal import Decimal
from django.test import TestCase
from django.core.exceptions import ValidationError
from order.models import Order, Item, OrderItem


class OrderModelTest(TestCase):
    def setUp(self):
        # Create test items
        self.pizza = Item.objects.create(
            name="Pizza", price=Decimal("10.99"), quantity=50
        )
        self.burger = Item.objects.create(
            name="Burger", price=Decimal("8.99"), quantity=30
        )
        self.drink = Item.objects.create(
            name="Soft Drink", price=Decimal("2.99"), quantity=100
        )

        # Create a basic order
        self.order = Order.objects.create(
            customer_name="John Doe",
            phone="1234567890",
            address="123 Main St",
            status="new",
        )

    def test_create_order(self):
        """Test basic order creation"""
        order = Order.objects.create(
            customer_name="Jane Smith",
            phone="9876543210",
            address="456 Oak St",
            status="new",
        )
        self.assertEqual(order.status, "new")
        self.assertIsNone(order.total_price)

    def test_create_item(self):
        """Test item creation"""
        item = Item.objects.create(name="Salad", price=Decimal("6.99"), quantity=20)
        self.assertEqual(item.name, "Salad")
        self.assertEqual(item.price, Decimal("6.99"))
        self.assertEqual(item.quantity, 20)

    def test_create_order_item(self):
        """Test order item creation"""
        order_item = OrderItem.objects.create(
            order=self.order, item=self.pizza, count=2
        )
        self.assertEqual(order_item.count, 2)
        self.assertEqual(order_item.item, self.pizza)

    def test_order_item_minimum_count(self):
        """Test order item count validation"""
        with self.assertRaises(ValidationError):
            order_item = OrderItem(order=self.order, item=self.pizza, count=0)
            order_item.full_clean()

    def test_multiple_items_in_order(self):
        """Test adding multiple items to an order"""
        OrderItem.objects.create(order=self.order, item=self.pizza, count=2)
        OrderItem.objects.create(order=self.order, item=self.burger, count=1)
        OrderItem.objects.create(order=self.order, item=self.drink, count=3)

        self.assertEqual(self.order.order_items.count(), 3)

    def test_order_status_transition(self):
        """Test order status transitions"""
        self.order.status = "preparing"
        self.order.save()
        self.assertEqual(self.order.status, "preparing")

        self.order.status = "ready"
        self.order.save()
        self.assertEqual(self.order.status, "ready")

    def test_invalid_order_status(self):
        """Test setting invalid order status"""
        with self.assertRaises(ValidationError):
            self.order.status = "invalid_status"
            self.order.full_clean()

    def test_item_price_decimal_places(self):
        """Test item price decimal places validation"""
        with self.assertRaises(ValidationError):
            item = Item(name="Test Item", price=Decimal("10.999"), quantity=10)
            item.full_clean()

    def test_delete_order_cascade(self):
        """Test cascade deletion of order items when order is deleted"""
        OrderItem.objects.create(order=self.order, item=self.pizza, count=2)
        order_id = self.order.id
        self.order.delete()
        self.assertEqual(OrderItem.objects.filter(order_id=order_id).count(), 0)

    def test_delete_item_cascade(self):
        """Test cascade deletion of order items when item is deleted"""
        order_item = OrderItem.objects.create(
            order=self.order, item=self.pizza, count=2
        )
        self.pizza.delete()
        self.assertEqual(OrderItem.objects.filter(id=order_item.id).count(), 0)

    def test_order_items_related_name(self):
        """Test related name functionality"""
        OrderItem.objects.create(order=self.order, item=self.pizza, count=2)
        self.assertTrue(hasattr(self.order, "order_items"))
        self.assertEqual(self.order.order_items.first().item, self.pizza)

    def test_item_order_items_related_name(self):
        """Test related name functionality for items"""
        order_item = OrderItem.objects.create(
            order=self.order, item=self.pizza, count=2
        )
        self.assertTrue(hasattr(self.pizza, "order_items"))
        self.assertEqual(self.pizza.order_items.first(), order_item)

    def test_phone_number_length(self):
        """Test phone number length validation"""
        with self.assertRaises(ValidationError):
            order = Order(
                customer_name="Test Customer",
                phone="1" * 21,  # Exceeds max_length of 20
                address="Test Address",
                status="new",
            )
            order.full_clean()

    def test_customer_name_length(self):
        """Test customer name length validation"""
        with self.assertRaises(ValidationError):
            order = Order(
                customer_name="A" * 101,  # Exceeds max_length of 100
                phone="1234567890",
                address="Test Address",
                status="new",
            )
            order.full_clean()

    def test_item_name_length(self):
        """Test item name length validation"""
        with self.assertRaises(ValidationError):
            item = Item(
                name="A" * 101,  # Exceeds max_length of 100
                price=Decimal("10.99"),
                quantity=10,
            )
            item.full_clean()

    def test_negative_item_quantity(self):
        """Test negative quantity validation"""
        with self.assertRaises(ValidationError):
            item = Item(name="Test Item", price=Decimal("10.99"), quantity=-1)
            item.full_clean()

    def test_order_created_at_auto_now(self):
        """Test created_at is automatically set"""
        order = Order.objects.create(
            customer_name="Test Customer",
            phone="1234567890",
            address="Test Address",
            status="new",
        )
        self.assertIsNotNone(order.created_at)

    def test_multiple_orders_same_customer(self):
        """Test creating multiple orders for the same customer"""
        customer_name = "Regular Customer"
        order1 = Order.objects.create(
            customer_name=customer_name,
            phone="1234567890",
            address="Test Address",
            status="new",
        )
        order2 = Order.objects.create(
            customer_name=customer_name,
            phone="1234567890",
            address="Test Address",
            status="new",
        )
        self.assertNotEqual(order1.id, order2.id)
