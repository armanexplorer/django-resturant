from django.db import connection


def update_inventory(item_name, quantity):
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE inventory
            SET quantity = quantity - %s
            WHERE item_name = %s
        """,
            [quantity, item_name],
        )
