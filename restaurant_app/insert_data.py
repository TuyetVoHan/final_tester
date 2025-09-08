import sqlite3

def insert_restaurants():
    conn = sqlite3.connect("restaurant_app/restaurant_reservation.db")
    cursor = conn.cursor()

    restaurants = [
        ("Pizza Palace", "New York, NY", "Italian", 4.5, "Authentic Italian pizza with fresh ingredients."),
        ("Sushi World", "Los Angeles, CA", "Japanese", 4.7, "Fresh sushi and sashimi with modern twists."),
        ("Curry House", "Chicago, IL", "Indian", 4.3, "Traditional Indian curries with rich spices."),
        ("Taco Fiesta", "Houston, TX", "Mexican", 4.2, "Street-style tacos with homemade tortillas."),
        ("Burger Haven", "Miami, FL", "American", 4.4, "Classic and gourmet burgers with fresh toppings."),
        ("Dragon Wok", "San Francisco, CA", "Chinese", 4.6, "Authentic Chinese stir-fry and dim sum."),
        ("Le Gourmet", "Boston, MA", "French", 4.8, "Fine French dining with elegant atmosphere."),
        ("Steak Supreme", "Dallas, TX", "Steakhouse", 4.5, "Premium steaks grilled to perfection."),
        ("Seafood Shack", "Seattle, WA", "Seafood", 4.3, "Fresh catches daily with ocean views."),
        ("Veggie Delight", "Portland, OR", "Vegetarian", 4.6, "Healthy plant-based meals and smoothies."),
        ("Mediterraneo", "San Diego, CA", "Mediterranean", 4.4, "Mediterranean flavors with fresh olive oil."),
        ("BBQ Barn", "Nashville, TN", "BBQ", 4.5, "Smoky BBQ ribs and pulled pork specialties."),
        ("Kebab King", "Detroit, MI", "Middle Eastern", 4.2, "Authentic kebabs and falafel dishes."),
        ("Golden Dragon", "Las Vegas, NV", "Chinese", 4.1, "Casual Chinese dining with family portions."),
        ("Pasta Fresca", "Philadelphia, PA", "Italian", 4.7, "Handmade pasta and wood-fired pizza.")
    ]

    cursor.executemany("""
    INSERT INTO Restaurants (name, location, cuisine, rating, description)
    VALUES (?, ?, ?, ?, ?)
    """, restaurants)

    conn.commit()
    conn.close()
    print("✅ 15 restaurants inserted successfully!")

if __name__ == "__main__":
    insert_restaurants()
