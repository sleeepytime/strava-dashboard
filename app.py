from flask import Flask, render_template, request, jsonify
from services.data import get_current_view_data
from services.analytics import compute_stats, get_activity_detail, build_timeline 
from services.visuals import get_graphs

app = Flask(__name__)

@app.route("/api/graphs")
def update_graphs():
    df, _, _ = get_current_view_data(request.args)
    return jsonify(get_graphs(df))

@app.route("/api/timeline")
def update_timeline():
    df, start, end = get_current_view_data(request.args)
    return jsonify(build_timeline(df, start, end))

@app.route("/api/stats")
def update_stats():
    df, _, _ = get_current_view_data(request.args)
    return jsonify(compute_stats(df))

@app.route("/api/activity")
def activity_detail():
    df, _, _ = get_current_view_data(request.args)

    # Extract 'mode' (default to 'latest') and 'date'
    mode = request.args.get("mode", "latest")
    date = request.args.get("date")
    
    return jsonify(get_activity_detail(df, mode, date))

@app.route("/")
def home():
    df, start, end = get_current_view_data(request.args)

    stats = compute_stats(df)
    timeline_days = build_timeline(df, start, end)

    return render_template(
        "index.html",
        total_miles=stats["total_miles"],
        total_time=stats["total_time"],
        total_activities=stats["total_activities"],
        timeline_days=timeline_days,
        start_date=start,
        end_date=end,
    )
  
if __name__ == "__main__":
    # Setting host to '0.0.0.0' tells Flask to listen on all public IPs
    app.run(debug=True, host='0.0.0.0', port=5000)