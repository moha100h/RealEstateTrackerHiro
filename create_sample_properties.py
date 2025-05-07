"""
Script to create sample properties for demo purposes
"""

import os
import django
import random

# Initialize Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hiro_estate.settings')
django.setup()

# Import models after Django setup
from properties.models import Property, PropertyType, TransactionType, PropertyStatus

def create_sample_properties(count=5):
    """Create sample properties for demonstration"""
    
    # Get existing types, statuses, and transaction types
    property_types = list(PropertyType.objects.all())
    transaction_types = list(TransactionType.objects.all())
    property_statuses = list(PropertyStatus.objects.all())
    
    # Only create properties if we have the necessary types
    if not property_types or not transaction_types or not property_statuses:
        print("Error: Make sure property types, transaction types, and statuses exist first.")
        return
    
    # Sample data for properties
    addresses = [
        "تهران، خیابان ولیعصر، کوچه نیلوفر، پلاک 42",
        "تهران، سعادت آباد، خیابان 24، پلاک 13",
        "تهران، پاسداران، خیابان گلستان، کوچه بهار، پلاک 8",
        "مشهد، بلوار وکیل آباد، خیابان هنرستان، پلاک 27",
        "اصفهان، خیابان چهارباغ بالا، کوچه مهتاب، پلاک 15",
        "شیراز، بلوار زند، کوچه سعدی، پلاک 19",
        "تبریز، خیابان ولیعصر، کوچه ارغوان، پلاک 23",
        "تهران، میدان ونک، برج آسمان، طبقه 12، واحد 4",
        "تهران، بلوار فرهنگ، کوچه هفتم، پلاک 3"
    ]
    
    titles = [
        "آپارتمان لوکس دوبلکس",
        "ویلای دوبلکس مدرن",
        "آپارتمان نوساز فول امکانات",
        "واحد تجاری بر خیابان اصلی",
        "خانه ویلایی باغچه دار",
        "پنت هاوس با ویو عالی",
        "آپارتمان سه خوابه نورگیر",
        "دفتر کار اداری",
        "مغازه تجاری در پاساژ مدرن"
    ]
    
    descriptions = [
        "این ملک دارای موقعیت مکانی عالی، دسترسی آسان به مترو و اتوبوس، مناسب برای زندگی خانوادگی، دارای انباری و پارکینگ می‌باشد.",
        "ملک بسیار لوکس با طراحی داخلی مدرن، کابینت های هایگلس، کف سرامیک، سیستم گرمایش و سرمایش مرکزی و نورگیر عالی.",
        "این ملک دارای آشپزخانه اپن، پنجره‌های دوجداره، آسانسور، لابی مجلل و نگهبانی 24 ساعته می‌باشد. دارای سند تک برگ و آماده تحویل.",
        "ملک نوساز با امکانات کامل، دسترسی عالی به مراکز خرید، بیمارستان و پارک. مناسب برای سرمایه گذاری با موقعیت استثنایی.",
        "فرصت استثنایی سرمایه گذاری در بهترین موقعیت منطقه، دسترسی عالی، نزدیک به مدارس و مراکز خرید. قابلیت رشد قیمت بالا."
    ]
    
    print(f"Creating {count} sample properties...")
    
    for i in range(count):
        # Randomly select types
        property_type = random.choice(property_types)
        transaction_type = random.choice(transaction_types)
        status = random.choice(property_statuses)
        
        # Generate random property details
        title = random.choice(titles)
        address = random.choice(addresses)
        area = random.randint(50, 300)
        price = random.randint(5, 50) * 100_000_000  # 500 million to 5 billion tomans
        year_built = random.randint(1390, 1402)
        rooms = random.randint(1, 5)
        description = random.choice(descriptions)
        
        # Create the property
        property = Property.objects.create(
            title=title,
            address=address,
            area=area,
            price=price,
            year_built=year_built,
            property_type=property_type,
            transaction_type=transaction_type,
            status=status,
            rooms=rooms,
            description=description
        )
        
        print(f"Created property: {property.property_code} - {property.title}")
    
    print("Sample properties created successfully!")

if __name__ == "__main__":
    create_sample_properties(8)  # Create 8 sample properties