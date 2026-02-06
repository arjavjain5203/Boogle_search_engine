from flask import Flask, render_template, request
from boogle.config import Config
from boogle.query_engine.engine import QueryEngine

app = Flask(__name__, 
            template_folder='templates',
            static_folder='static')

# Initialize Query Engine once on startup
print("Initializing Query Engine...")
query_engine = QueryEngine()
print("Query Engine Ready.")

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search')
def search():
    query = request.args.get('q', '')
    if not query:
        return render_template('index.html')
    
    page = int(request.args.get('page', 1))
    per_page = 10
    
    results, corrected_query, was_corrected = query_engine.search(query)
    total_results = len(results)
    
    start = (page - 1) * per_page
    end = start + per_page
    paginated_results = results[start:end]
    
    # Generate snippets for displayed results on-the-fly
    display_results = []
    # Use corrected query for snippets to highlight actual matched terms
    snippet_query = corrected_query if was_corrected else query
    
    for res in paginated_results:
        snippet = query_engine.get_snippet(res['doc_id'], snippet_query)
        res_with_snippet = res.copy()
        res_with_snippet['snippet'] = snippet
        display_results.append(res_with_snippet)
    
    return render_template('results.html', 
                           query=query, 
                           corrected_query=corrected_query,
                           was_corrected=was_corrected,
                           results=display_results, 
                           page=page, 
                           total=total_results,
                           per_page=per_page)

@app.route('/status')
def status():
    # Read crawler state
    state_path = os.path.join(Config.STORAGE_PATH, 'crawl_state.json')
    state = {}
    if os.path.exists(state_path):
        try:
            with open(state_path, 'r') as f:
                state = json.load(f)
        except:
            state = {"error": "Could not load state"}
            
    # Read scheduler state
    queue_path = os.path.join(Config.STORAGE_PATH, 'scheduler_queue.json')
    queue_len = 0
    if os.path.exists(queue_path):
        try:
            with open(queue_path, 'r') as f:
                queue = json.load(f)
                queue_len = len(queue)
        except:
            pass

    return render_template('dashboard.html', state=state, queue_len=queue_len)

if __name__ == '__main__':
    app.run(port=Config.FLASK_PORT, debug=True)
