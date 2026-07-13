# Schema Hints — Purely Pickles Billing System

> **⚠️ These are HINTS, not the full schema.**  
> Your job is to read these, think about the relationships, and design your **OWN Supabase schema**.

---

## What the Billing System Gives You (Daily CSV)

Every day, the billing system exports a CSV with these columns:

| Column | What it means | Example |
|---|---|---|
| `order_date` | Date of order (YYYY-MM-DD) | `2018-06-22` |
| `sales_qty` | How many items ordered | `3` |
| `sales_amount` | Total bill in INR | `875.00` |
| `currency` | Always "INR" | `INR` |
| `user_id` | Who placed the order | `5321` |
| `r_id` | Which restaurant made the food | `158203` |
| `restaurant_name` | Restaurant name | `theka coffee desi` |
| `city` | City of restaurant | `Abohar` |
| `restaurant_cuisine` | Type of food | `Beverages` |

---

## Other Data Available (via MCP Tools)

### Restaurants
- Each restaurant has an **ID** (this is the `r_id` in orders)
- Has: name, city, rating, cost level, cuisine type
- **Hint:** One restaurant → many orders. That's a **one-to-many** relationship.

### Food Items
- Each food item has an **f_id** (unique identifier)
- Has: item name, veg or non-veg
- **Hint:** Food items appear on menus, not directly in orders.

### Menu
- Links restaurants to food items with prices
- Has: menu_id, r_id, f_id, cuisine, price
- **Hint:** This is a **junction table** between restaurants and food.

### Users (Customers)
- Each user has a **user_id** (this is the `user_id` in orders)
- Has: name, email, gender, occupation, monthly income, education
- **Hint:** One user → many orders. That's another **one-to-many**.

---

## Your Job: Design YOUR Database

Think about these questions:

1. **What tables do you need?**  
   (Hint: Look at the entities — Orders, Restaurants, Users, Food, Menu)

2. **What are the Primary Keys for each table?**  
   (Hint: Every table needs a unique identifier)

3. **What are the Foreign Keys?**  
   (Hint: `orders.r_id → restaurants.id`, `orders.user_id → users.user_id`)

4. **What column types should you use?**  
   (Hint: Dates → `DATE`, money → `NUMERIC`, text → `TEXT`, numbers → `INTEGER`)

5. **What constraints do you need?**  
   (Hint: Can a restaurant_id in orders be null? Can sales_amount be negative?)

---

## Schema Design Clues (Read Carefully)

```
CLUE #1: The daily CSV joins orders + restaurants.
         In YOUR database, these should be SEPARATE tables linked by FK.

CLUE #2: A single order has one restaurant (r_id) and one user (user_id).
         That's TWO foreign keys on the orders table.

CLUE #3: The menu table links restaurants (r_id) to food items (f_id).
         Think about what the PRIMARY KEY of the menu table should be.

CLUE #4: Not all columns from the CSV need to go into ONE table.
         Split them logically: order info → orders table,
         restaurant info → restaurants table.

CLUE #5: You'll receive daily CSVs. Your schema should handle DUPLICATES —
         what if you accidentally import the same day twice?
```

---

## Example: What a Good Schema Looks Like

Here's a PARTIAL example (I'm not giving you the full thing):

```sql
-- Orders table (partial — you fill in the rest)
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    order_date DATE NOT NULL,
    sales_qty INTEGER,
    sales_amount NUMERIC,
    -- TODO: What foreign keys go here?
    -- TODO: What constraints?
);

-- Restaurants table
CREATE TABLE restaurants (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    city TEXT,
    -- TODO: What other columns?
);
```

---

> **Remember:** The schema is defined **ONCE**. It shouldn't change.  
> The data follows the schema rules every day.  
> This is what makes your database QUERYABLE and RELIABLE.
