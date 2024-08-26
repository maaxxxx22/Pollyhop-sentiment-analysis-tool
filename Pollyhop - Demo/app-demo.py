from flask import Flask, render_template, request, jsonify
import pandas as pd

app = Flask(__name__, static_url_path='/static')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def analyze():
    # Load a demo CSV file for analysis (Replace with your actual demo file)
    demo_csv = 'data/demo.csv'
    df = pd.read_csv(demo_csv)

    # Example analysis: calculating the mean of 'predicted_pct'
    summary = {
        'average_predicted_pct': df['predicted_pct'].mean()
    }

    # Prepare data in the format expected by the frontend
    data = df.to_dict(orient='records')

    # Return the data and summary to the frontend
    return jsonify({'data': data, 'summary': summary})

if __name__ == '__main__':
    app.run(debug=True)
