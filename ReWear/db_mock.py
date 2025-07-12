from database import *
import random


def add_mock_products(user_id=2, count=20):

    db = SessionLocal()
    created_products = []
    
    try:
        # Check if user exists
        user = db.query(User).filter(User.uid == user_id).first()
        if not user:
            print(f"User with ID {user_id} not found")
            return []
        
        # Sample data for products
        categories = ['Tops', 'Bottoms', 'Dresses', 'Outerwear']
        subcategories = {
            'Tops': ['Casual', 'Formal', 'Athletic'],
            'Bottoms': ['Casual', 'Formal', 'Athletic'],
            'Dresses': ['Casual', 'Formal', 'Evening'],
            'Outerwear': ['Light', 'Heavy', 'Formal']
        }
        conditions = ['New with tags', 'Like New', 'Good', 'Fair']
        sizes = ['XS', 'S', 'M', 'L', 'XL', 'XXL']
        
        # Sample titles by category
        titles = {
            'Tops': [
                'Cotton T-Shirt', 'Silk Blouse', 'Button-Down Shirt', 
                'Cashmere Sweater', 'Polo Shirt', 'Tank Top',
                'Crop Top', 'Turtleneck', 'V-Neck Tee'
            ],
            'Bottoms': [
                'Slim Jeans', 'Chino Pants', 'Linen Trousers',
                'Cargo Shorts', 'Pleated Skirt', 'Denim Shorts',
                'Leather Pants', 'Corduroy Pants', 'Pencil Skirt'
            ],
            'Dresses': [
                'Maxi Dress', 'Cocktail Dress', 'Wrap Dress',
                'Shift Dress', 'A-Line Dress', 'Bodycon Dress',
                'Slip Dress', 'Sundress', 'Evening Gown'
            ],
            'Outerwear': [
                'Denim Jacket', 'Leather Jacket', 'Trench Coat',
                'Puffer Jacket', 'Wool Coat', 'Blazer',
                'Windbreaker', 'Parka', 'Bomber Jacket'
            ]
        }
        
        # Sample descriptions
        descriptions = [
            "Barely worn, in excellent condition. Perfect for any occasion.",
            "Stylish and comfortable, a must-have for your wardrobe.",
            "High-quality fabric that will last for years.",
            "Trendy design that never goes out of style.",
            "Versatile piece that can be dressed up or down.",
            "Luxurious feel with attention to detail.",
            "Classic cut with modern details.",
            "Unique piece that will make you stand out.",
            "Comfortable fit with elegant design."
        ]
        
        # Sample image URLs (placeholder images)
        image_urls = [
            "https://via.placeholder.com/500x600?text=Fashion+Item",
            "https://via.placeholder.com/500x600?text=Clothing",
            "https://via.placeholder.com/500x600?text=Apparel",
            "https://via.placeholder.com/500x600?text=Style",
            "https://via.placeholder.com/500x600?text=Wardrobe"
        ]
        
        # Create products
        for i in range(count):
            # Select random attributes
            category = random.choice(categories)
            subcategory = random.choice(subcategories[category])
            condition = random.choice(conditions)
            size = random.choice(sizes)
            title = f"{random.choice(titles[category])} - {subcategory}"
            description = random.choice(descriptions)
            
            # Calculate point value
            point_value = calculate_points(category, subcategory, condition)
            
            # Create product
            new_product = Product(
                uid=user_id,
                title=title,
                description=description,
                category=category,
                subcategory=subcategory,
                size=size,
                condition=condition,
                point_value=point_value,
                status="available"  # Make them available immediately for demo
            )
            
            db.add(new_product)
            db.flush()  # Get the ID without committing
            
            # Add a primary image
            primary_image = ProductImage(
                pid=new_product.pid,
                image_url=random.choice(image_urls),
                is_primary=True
            )
            db.add(primary_image)
            
            # Add 1-2 additional images
            for _ in range(random.randint(1, 2)):
                additional_image = ProductImage(
                    pid=new_product.pid,
                    image_url=random.choice(image_urls),
                    is_primary=False
                )
                db.add(additional_image)
            
            created_products.append(new_product.pid)
        
        # Commit all changes
        db.commit()
        
        print(f"Successfully created {count} mock products for user ID {user_id}")
        return created_products
        
    except Exception as e:
        db.rollback()
        print(f"Error creating mock products: {e}")
        return []
    finally:
        db.close()


add_mock_products()