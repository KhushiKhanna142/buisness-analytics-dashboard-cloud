import boto3
import json
import dash
from dash import html, dcc, Input, Output, State
import pandas as pd
from io import StringIO

BUCKET_NAME = 'analytics-dashboard-cc-project'

app = dash.Dash(__name__)

app.index_string = '''
<!DOCTYPE html>
<html>
<head>
    {%metas%}
    <title>Data Analytics Dashboard</title>
    {%favicon%}
    {%css%}
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            background: #f0f2f5;
            color: #1a1a2e;
        }
        .header {
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            color: white;
            padding: 24px 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.2);
        }
        .header h1 { font-size: 24px; font-weight: 600; letter-spacing: 0.5px; }
        .header p { font-size: 13px; color: #a0aec0; margin-top: 4px; }
        .container { max-width: 1000px; margin: 32px auto; padding: 0 24px; }
        .card {
            background: white;
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 24px;
            box-shadow: 0 1px 4px rgba(0,0,0,0.08);
        }
        .card h3 {
            font-size: 15px;
            font-weight: 600;
            color: #2d3748;
            margin-bottom: 16px;
            padding-bottom: 10px;
            border-bottom: 2px solid #e2e8f0;
        }
        .upload-box {
            border: 2px dashed #cbd5e0;
            border-radius: 10px;
            padding: 32px;
            text-align: center;
            cursor: pointer;
            transition: all 0.2s;
            background: #f7fafc;
        }
        .upload-box:hover { border-color: #4299e1; background: #ebf8ff; }
        .upload-icon { font-size: 32px; margin-bottom: 8px; }
        .upload-text { font-size: 14px; color: #718096; }
        .input-row { display: flex; gap: 12px; align-items: center; }
        .text-input {
            flex: 1;
            padding: 10px 14px;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            font-size: 14px;
            outline: none;
            transition: border 0.2s;
        }
        .text-input:focus { border-color: #4299e1; }
        .btn {
            padding: 10px 24px;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        .btn-primary { background: #4299e1; color: white; }
        .btn-primary:hover { background: #3182ce; }
        .btn-secondary { background: #edf2f7; color: #4a5568; }
        .btn-secondary:hover { background: #e2e8f0; }
        .status-success {
            margin-top: 12px;
            padding: 10px 14px;
            background: #f0fff4;
            border: 1px solid #9ae6b4;
            border-radius: 8px;
            color: #276749;
            font-size: 13px;
        }
        .status-error {
            margin-top: 12px;
            padding: 10px 14px;
            background: #fff5f5;
            border: 1px solid #feb2b2;
            border-radius: 8px;
            color: #c53030;
            font-size: 13px;
        }
        .result-box {
            background: #1a1a2e;
            color: #68d391;
            padding: 20px;
            border-radius: 10px;
            font-family: monospace;
            font-size: 13px;
            line-height: 1.6;
            white-space: pre-wrap;
            margin-top: 12px;
            max-height: 400px;
            overflow-y: auto;
        }
        .report-item {
            display: flex;
            align-items: center;
            padding: 10px 14px;
            background: #f7fafc;
            border-radius: 8px;
            margin-bottom: 8px;
            font-size: 13px;
            color: #4a5568;
            border: 1px solid #e2e8f0;
        }
        .report-icon { margin-right: 10px; font-size: 16px; }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 16px;
            margin-bottom: 24px;
        }
        .stat-card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 1px 4px rgba(0,0,0,0.08);
            border-top: 3px solid #4299e1;
        }
        .stat-value { font-size: 28px; font-weight: 700; color: #2d3748; }
        .stat-label { font-size: 12px; color: #718096; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.5px; }
    </style>
</head>
<body>
    {%app_entry%}
    <footer>{%config%}{%scripts%}{%renderer%}</footer>
</body>
</html>
'''

app.layout = html.Div([
    html.Div([
        html.H1("Data Analytics Dashboard"),
        html.P("S3 + EC2 Cloud Computing Project")
    ], className="header"),

    html.Div([
        html.Div([
            html.Div("📊", className="stat-value"),
            html.Div("S3 Storage", className="stat-label")
        ], className="stat-card"),
        html.Div([
            html.Div("⚙️", className="stat-value"),
            html.Div("EC2 Compute", className="stat-label")
        ], className="stat-card"),
        html.Div([
            html.Div("✅", className="stat-value"),
            html.Div("Pipeline Active", className="stat-label")
        ], className="stat-card"),
    ], className="stats-grid", style={"marginTop": "32px", "padding": "0 24px", "maxWidth": "1000px", "margin": "32px auto 0"}),

    html.Div([
        html.Div([
            html.H3("Upload CSV File to S3"),
            dcc.Upload(
                id='upload-data',
                children=html.Div([
                    html.Div("☁️", className="upload-icon"),
                    html.Div("Drag and drop or click to upload a CSV file", className="upload-text")
                ]),
                className="upload-box",
                multiple=False
            ),
            html.Div(id='upload-status')
        ], className="card"),

        html.Div([
            html.H3("Run Analysis"),
            html.Div([
                dcc.Input(
                    id='filename-input',
                    placeholder='Enter filename e.g. sample.csv',
                    type='text',
                    className="text-input"
                ),
                html.Button('Analyze', id='analyze-button', n_clicks=0, className="btn btn-primary"),
            ], className="input-row"),
            html.Div(id='analysis-output')
        ], className="card"),

        html.Div([
            html.H3("Reports Saved to S3"),
            html.Button('Refresh Reports', id='refresh-button', n_clicks=0, className="btn btn-secondary"),
            html.Div(id='reports-list', style={"marginTop": "16px"})
        ], className="card"),

    ], className="container")
])

@app.callback(
    Output('upload-status', 'children'),
    Input('upload-data', 'contents'),
    State('upload-data', 'filename')
)
def upload_to_s3(contents, filename):
    if contents is None:
        return ''
    import base64
    content_type, content_string = contents.split(',')
    decoded = base64.b64decode(content_string)
    s3 = boto3.client('s3')
    s3.put_object(Bucket=BUCKET_NAME, Key=f'raw-data/{filename}', Body=decoded)
    return html.Div(f'✅ {filename} uploaded to S3 successfully.', className="status-success")

@app.callback(
    Output('analysis-output', 'children'),
    Input('analyze-button', 'n_clicks'),
    State('filename-input', 'value')
)
def run_analysis(n_clicks, filename):
    if n_clicks == 0 or not filename:
        return ''
    try:
        from analyze import run_pipeline
        summary = run_pipeline(filename)
        return html.Div(json.dumps(summary, indent=2), className="result-box")
    except Exception as e:
        return html.Div(f'Error: {str(e)}', className="status-error")

@app.callback(
    Output('reports-list', 'children'),
    Input('refresh-button', 'n_clicks')
)
def list_reports(n_clicks):
    s3 = boto3.client('s3')
    response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix='reports/')
    if 'Contents' not in response:
        return html.Div('No reports yet. Run an analysis first.', style={"color": "#718096", "fontSize": "14px"})
    files = [obj['Key'].replace('reports/', '') for obj in response['Contents']]
    return html.Div([
        html.Div([
            html.Span("📄", className="report-icon"),
            html.Span(f)
        ], className="report-item") for f in files
    ])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050, debug=False)
