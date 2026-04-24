import sqlite3
import json
from datetime import datetime
import os

DB_PATH = "zm_learning.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            store_id TEXT,
            issue_type TEXT,
            recommended_action TEXT,
            feedback TEXT, -- 'positive' or 'negative'
            context_json TEXT,
            timestamp DATETIME
        )
    ''')
    conn.commit()
    conn.close()

def save_feedback(store_id, issue_type, action, feedback, context):
    """Save user feedback to the learning database."""
    init_db()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO feedback (store_id, issue_type, recommended_action, feedback, context_json, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (store_id, issue_type, action, feedback, json.dumps(context), datetime.now()))
    conn.commit()
    conn.close()

def get_historical_patterns(issue_type, context_features=None):
    """
    Retrieve success rates and similar cases for a given issue type.
    Context features can be used for future fuzzy matching (footfall range, etc.)
    """
    if not os.path.exists(DB_PATH):
        return {"similar_cases": 0, "success_rate": 0.0, "best_action": None}
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Simple issue-based matching for now
    c.execute('''
        SELECT 
            COUNT(*) as total,
            SUM(CASE WHEN feedback = 'positive' THEN 1 ELSE 0 END) as positive_count,
            recommended_action
        FROM feedback
        WHERE issue_type = ?
        GROUP BY recommended_action
        ORDER BY positive_count DESC
    ''', (issue_type,))
    
    rows = c.fetchall()
    conn.close()
    
    if not rows:
        return {"similar_cases": 0, "success_rate": 0.0, "best_action": None}
    
    total_cases = sum(row['total'] for row in rows)
    total_positive = sum(row['positive_count'] for row in rows)
    best_action = rows[0]['recommended_action']
    
    return {
        "similar_cases": total_cases,
        "success_rate": round(total_positive / total_cases, 2) if total_cases > 0 else 0.0,
        "best_action": best_action
    }

def get_learning_stats():
    """Retrieve aggregate stats for the dashboard."""
    if not os.path.exists(DB_PATH):
        return {"total_feedback": 0, "avg_success": 0.0, "top_issues": []}
    
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) as total, SUM(CASE WHEN feedback = 'positive' THEN 1 ELSE 0 END) as positive FROM feedback")
    row = c.fetchone()
    total = row['total']
    positive = row['positive'] or 0
    
    c.execute('''
        SELECT issue_type, COUNT(*) as count 
        FROM feedback 
        GROUP BY issue_type 
        ORDER BY count DESC LIMIT 5
    ''')
    top_issues = [dict(r) for r in c.fetchall()]
    
    conn.close()
    return {
        "total_feedback": total,
        "avg_success": round(positive / total * 100, 1) if total > 0 else 0.0,
        "top_issues": top_issues
    }
