"""
Google Books ETL Pipeline DAG

This DAG implements an ETL (Extract, Transform, Load) pipeline to:
1. Extract: Fetch book data from Google Books API
2. Transform: Clean and deduplicate the book data
3. Load: Store the processed data into PostgreSQL database

Author: Data Engineering Team
Date: 2024
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import requests
import pandas as pd
import time


# ============================================================================
# EXTRACT: Fetch data from Google Books API
# ============================================================================

def get_google_books_data(num_books, **context):
    """
    Extract book data from Google Books API.
    
    Args:
        num_books (int): Number of books to fetch
        **context: Airflow context dictionary
    
    Returns:
        None: Pushes data to XCom with key 'book_data'
    """
    ti = context['ti']
    base_url = "https://www.googleapis.com/books/v1/volumes"
    
    books = []
    seen_titles = set()
    start_index = 0
    max_results = 40  # Google Books API max per request
    
    print(f"Starting to fetch {num_books} books from Google Books API...")
    
    while len(books) < num_books:
        params = {
            "q": "data engineering",
            "maxResults": min(max_results, num_books - len(books)),
            "startIndex": start_index
        }
        
        try:
            response = requests.get(base_url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Check if we have items
            if "items" not in data or not data["items"]:
                print("No more books found in API response")
                break
            
            # Process each book item
            for item in data["items"]:
                volume_info = item.get("volumeInfo", {})
                
                # Extract title
                title = volume_info.get("title", "").strip()
                if not title or title in seen_titles:
                    continue
                
                # Extract authors (can be a list)
                authors = volume_info.get("authors", [])
                author = ", ".join(authors) if authors else "Unknown"
                
                # Extract price information
                sale_info = item.get("saleInfo", {})
                price_info = sale_info.get("retailPrice", {})
                if price_info:
                    price = f"{price_info.get('amount', 'N/A')} {price_info.get('currencyCode', '')}"
                else:
                    price = sale_info.get("saleability", "NOT_FOR_SALE")
                
                # Extract average rating
                rating = volume_info.get("averageRating", "N/A")
                if rating != "N/A":
                    rating = f"{rating}/5.0"
                
                seen_titles.add(title)
                books.append({
                    "title": title,
                    "author": author,
                    "price": str(price),
                    "rating": str(rating),
                })
            
            # Check if we've reached the total available items
            total_items = data.get("totalItems", 0)
            if start_index + len(data["items"]) >= total_items or len(books) >= num_books:
                break
            
            start_index += len(data["items"])
            time.sleep(1)  # Be respectful to the API
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching books from API: {e}")
            break
        except Exception as e:
            print(f"Unexpected error: {e}")
            break
    
    # Limit to the requested number of books
    books = books[:num_books]
    
    # Check if we have any books
    if not books:
        print("Warning: No books were fetched. Pushing empty list.")
        ti.xcom_push(key='book_data', value=[])
        return
    
    # Transform: Clean and deduplicate
    df = pd.DataFrame(books)
    if not df.empty:
        df.drop_duplicates(subset="title", inplace=True)
        print(f"Fetched {len(df)} unique books after deduplication")
    
    # Push to XCom for next task
    ti.xcom_push(key='book_data', value=df.to_dict('records'))


# ============================================================================
# LOAD: Database operations
# ============================================================================

def create_books_table():
    """
    Create the books table in PostgreSQL if it doesn't exist.
    
    Table Schema:
        - id: SERIAL PRIMARY KEY
        - title: TEXT NOT NULL
        - author: TEXT
        - price: TEXT
        - rating: TEXT
    """
    postgres_hook = PostgresHook(postgres_conn_id='books_connection')
    create_table_query = """
    CREATE TABLE IF NOT EXISTS books (
        id SERIAL PRIMARY KEY,
        title TEXT NOT NULL,
        author TEXT,
        price TEXT,
        rating TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    postgres_hook.run(create_table_query)
    print("Books table created/verified successfully")


def insert_book_data_into_postgres(**context):
    """
    Insert book data into PostgreSQL database.
    
    Args:
        **context: Airflow context dictionary
    
    Raises:
        ValueError: If no book data is found in XCom
    """
    ti = context['ti']
    book_data = ti.xcom_pull(key='book_data', task_ids='fetch_book_data')
    
    if not book_data:
        print("Warning: No book data found in XCom. Skipping insert.")
        return
    
    postgres_hook = PostgresHook(postgres_conn_id='books_connection')
    conn = postgres_hook.get_conn()
    cursor = conn.cursor()
    
    insert_query = """
        INSERT INTO books (title, author, price, rating)
        VALUES (%s, %s, %s, %s)
    """
    
    try:
        inserted_count = 0
        for book in book_data:
            cursor.execute(
                insert_query,
                (
                    book.get('title', ''),
                    book.get('author', ''),
                    book.get('price', ''),
                    book.get('rating', '')
                )
            )
            inserted_count += 1
        
        conn.commit()
        print(f"Successfully inserted {inserted_count} books into the database.")
        
    except Exception as e:
        conn.rollback()
        print(f"Error inserting data: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


# ============================================================================
# DAG Configuration
# ============================================================================

default_args = {
    'owner': 'data_engineering',
    'depends_on_past': False,
    'start_date': datetime(2024, 6, 20),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    dag_id='fetch_and_store_google_books',
    default_args=default_args,
    description='ETL pipeline to fetch book data from Google Books API and store in PostgreSQL',
    schedule=timedelta(days=1),
    catchup=False,
    tags=['etl', 'google-books', 'postgres', 'data-engineering'],
)


# ============================================================================
# Task Definitions
# ============================================================================

fetch_book_data_task = PythonOperator(
    task_id='fetch_book_data',
    python_callable=get_google_books_data,
    op_args=[50],  # Number of books to fetch
    dag=dag,
)

create_table_task = PythonOperator(
    task_id='create_table',
    python_callable=create_books_table,
    dag=dag,
)

insert_book_data_task = PythonOperator(
    task_id='insert_book_data',
    python_callable=insert_book_data_into_postgres,
    dag=dag,
)


# ============================================================================
# Task Dependencies
# ============================================================================

fetch_book_data_task >> create_table_task >> insert_book_data_task
