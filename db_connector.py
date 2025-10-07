# db_connector.py

import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv

load_dotenv()

DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")


def get_db_connection():
    """
    Establishes and returns a psycopg2 connection object (conn).
    The caller is responsible for handling and closing this connection.
    """
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            host=DB_HOST,
            port=DB_PORT
        )
        return conn
    except psycopg2.Error as e:
        raise ConnectionError(f"Error connecting to the DB: {e}")


def execute_query(query, fetch_results=False):
    """
    Executes an SQL query in PostgreSQL.
    Returns a DataFrame if fetch_results is True (for SELECT), or None/Error.
    (YOUR EXISTING CODE)
    """
    conn = None
    df = pd.DataFrame()
    
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute(query)
        
        if fetch_results:
            column_names = [desc[0] for desc in cur.description]
            records = cur.fetchall()
            df = pd.DataFrame(records, columns=column_names)
        else:
            conn.commit()
            
    except ConnectionError as e:
        error_message = f"{e}"
        df = pd.DataFrame({'Error': [error_message]})
        
    except psycopg2.Error as e:
        error_message = f"DB Error: Could not execute the query. {e}"
        df = pd.DataFrame({'Error': [error_message]})
        if conn:
            conn.rollback()
            
    except Exception as e:
        error_message = f"General Error: {e}"
        df = pd.DataFrame({'Error': [error_message]})
        
    finally:
        if conn:
            try:
                cur.close()
                conn.close()
            except:
                pass
            
    return df