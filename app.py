import boto3, json, dash, base64, traceback, platform, psutil
from dash import html, dcc, Input, Output, State, ctx, dash_table
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from io import StringIO
from datetime import datetime

BUCKET_NAME = 'analytics-dashboard-cc-project'
try:
    s3 = boto3.client('s3')
    lam = boto3.client('lambda')
    logs_client = boto3.client('logs')
except Exception as e:
    print(f"AWS init warning: {e}")

activity_log = []
def log_event(msg):
    activity_log.insert(0, {"time": datetime.now().strftime("%H:%M:%S"), "msg": msg})
    if len(activity_log) > 30: activity_log.pop()

app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "Cloud Analytics Pro | AWS Serverless Dashboard"

# System info
sys_info = {
    "os": platform.system() + " " + platform.release(),
    "python": platform.python_version(),
    "cpu_cores": psutil.cpu_count(),
}

app.layout = html.Div([
    # HEADER
    html.Div([
        html.Div([
            html.Div("⚡", className="logo-icon"),
            html.Div([html.H1("Cloud Analytics Pro"), html.P("Serverless Data Intelligence Platform")], className="logo-text")
        ], className="logo-area"),
        html.Div([
            html.Span("● PIPELINE ACTIVE", className="badge badge-live"),
            html.Span(id="live-clock", className="badge"),
            html.Span("ap-south-1", className="badge"),
            html.Span("AWS Lambda + S3", className="badge"),
        ], className="header-badges")
    ], className="top-header"),

    # SYSTEM STATUS BAR
    html.Div([
        html.Div([
            html.Span("SYS", className="sys-label"),
            html.Span(f"OS: {sys_info['os']}", className="sys-item"),
            html.Span(f"Python: {sys_info['python']}", className="sys-item"),
            html.Span(f"Cores: {sys_info['cpu_cores']}", className="sys-item"),
            html.Span(id="cpu-usage", className="sys-item"),
            html.Span(id="mem-usage", className="sys-item"),
            html.Span(f"Bucket: {BUCKET_NAME}", className="sys-item sys-highlight"),
        ]),
    ], className="sys-bar"),

    # TABS
    html.Div([
        dcc.Tabs(id='main-tabs', value='tab-pipeline', children=[
            dcc.Tab(label='🚀 Pipeline', value='tab-pipeline', className='tab-item', selected_className='tab-active'),
            dcc.Tab(label='🗂️ S3 Explorer', value='tab-explorer', className='tab-item', selected_className='tab-active'),
            dcc.Tab(label='📋 Data Preview', value='tab-preview', className='tab-item', selected_className='tab-active'),
            dcc.Tab(label='⏱️ Lambda Metrics', value='tab-metrics', className='tab-item', selected_className='tab-active'),
            dcc.Tab(label='📝 Activity Log', value='tab-log', className='tab-item', selected_className='tab-active'),
        ], className="tabs-container"),
        html.Div(id='tab-content')
    ], className="main-container"),

    # FOOTER TERMINAL
    html.Div([
        html.Div([
            html.Span("▸ ", style={"color": "#10b981"}),
            html.Span("cloud-analytics@aws", style={"color": "#6366f1"}),
            html.Span(":~$ ", style={"color": "#94a3b8"}),
            html.Span("System initialized. Connected to S3 and Lambda.", className="term-line", **{"data-text": "System initialized. Connected to S3 and Lambda."}),
        ], className="terminal-line"),
        html.Div([
            html.Span("▸ ", style={"color": "#10b981"}),
            html.Span("cloud-analytics@aws", style={"color": "#6366f1"}),
            html.Span(":~$ ", style={"color": "#94a3b8"}),
            html.Span(f"Region: ap-south-1 | Bucket: {BUCKET_NAME} | Runtime: Python {sys_info['python']}", className="term-line",
                       **{"data-text": f"Region: ap-south-1 | Bucket: {BUCKET_NAME} | Runtime: Python {sys_info['python']}"}),
        ], className="terminal-line"),
        html.Div([
            html.Span("▸ ", style={"color": "#10b981"}),
            html.Span("cloud-analytics@aws", style={"color": "#6366f1"}),
            html.Span(":~$ ", style={"color": "#94a3b8"}),
            html.Span("Awaiting commands...", className="term-line term-blink", **{"data-text": "Awaiting commands..."}),
        ], className="terminal-line"),
    ], className="footer-terminal"),

    dcc.Interval(id='sys-refresh', interval=3000, n_intervals=0),
])

def pipeline_tab():
    return html.Div([
        html.Div([
            html.Div([html.Div("📤", className="arch-icon"), html.Div("Data Ingestion", className="arch-label"), html.Div("Amazon S3", className="arch-svc")], className="arch-step"),
            html.Div([html.Div("⚡", className="arch-icon"), html.Div("Serverless Compute", className="arch-label"), html.Div("AWS Lambda", className="arch-svc")], className="arch-step"),
            html.Div([html.Div("📊", className="arch-icon"), html.Div("Visualization", className="arch-label"), html.Div("Plotly + Dash", className="arch-svc")], className="arch-step"),
        ], className="arch-banner"),
        html.Div([
            html.Div([
                html.Div([
                    html.Div([html.Div("📤", className="card-header-icon icon-ingest"), html.Div([html.Div("Ingestion Layer", className="card-title"), html.Div("Upload CSV → Amazon S3", className="card-subtitle")])], className="card-header"),
                    dcc.Upload(id='upload-data', children=html.Div([html.Div("☁️", className="drop-icon"), html.Div("Drop CSV file here", className="drop-text"), html.Div("or click to browse", className="drop-hint")]), className="drop-zone", multiple=False),
                    dcc.Loading(html.Div(id='upload-status'), type="dot", color="#6366f1")
                ], className="glass-card"),
                html.Div([
                    html.Div([html.Div("⚡", className="card-header-icon icon-compute"), html.Div([html.Div("Compute Layer", className="card-title"), html.Div("Process with Lambda", className="card-subtitle")])], className="card-header"),
                    dcc.Input(id='filename-input', placeholder='filename (e.g. sample.csv)', type='text', className="field-input"),
                    html.Div([dcc.Checklist(id='compute-mode', options=[{'label': ' AWS Lambda (Serverless)', 'value': 'lambda'}], value=['lambda'], inline=True)], className="mode-toggle"),
                    html.Button('🚀 Trigger Processing', id='analyze-button', n_clicks=0, className="btn-launch"),
                    dcc.Loading(html.Div(id='analysis-output'), type="dot", color="#6366f1")
                ], className="glass-card"),
                html.Div([
                    html.Div([html.Div("🗄️", className="card-header-icon icon-storage"), html.Div([html.Div("Storage Layer", className="card-title"), html.Div("S3 Report Artifacts", className="card-subtitle")])], className="card-header"),
                    html.Button('🔄 Refresh Reports', id='refresh-button', n_clicks=0, className="btn-refresh"),
                    dcc.Loading(html.Div(id='reports-list'), type="dot", color="#f59e0b")
                ], className="glass-card"),
            ]),
            html.Div([
                html.Div([
                    html.Div([html.Div("📊", className="card-header-icon icon-dash"), html.Div([html.Div("Analytics Dashboard", className="card-title"), html.Div("Real-time data visualizations", className="card-subtitle")])], className="card-header"),
                    html.Div(id="dashboard-content", children=[html.Div([html.Div("📡", className="empty-icon"), html.Div("Awaiting Data", className="empty-title"), html.Div("Upload → Process → View Report", className="empty-desc")], className="empty-state")])
                ], className="glass-card dash-panel")
            ])
        ], className="pipeline-grid")
    ])

def explorer_tab():
    return html.Div([
        html.Div([
            html.Div([html.Div("🗂️", className="card-header-icon icon-storage"), html.Div([html.Div("S3 Bucket Explorer", className="card-title"), html.Div(f"s3://{BUCKET_NAME}", className="card-subtitle")])], className="card-header"),
            html.Button('🔍 Scan Bucket', id='scan-bucket', n_clicks=0, className="btn-launch"),
            html.Div(id='bucket-contents', style={"marginTop": "20px"})
        ], className="glass-card")
    ])

def preview_tab():
    return html.Div([
        html.Div([
            html.Div([html.Div("📋", className="card-header-icon icon-ingest"), html.Div([html.Div("Data Preview & Quality", className="card-title"), html.Div("Inspect raw CSV from S3", className="card-subtitle")])], className="card-header"),
            html.Div([
                dcc.Input(id='preview-filename', placeholder='filename (e.g. sample.csv)', type='text', className="field-input", style={"marginBottom": "0"}),
                html.Button('👁️ Preview', id='preview-btn', n_clicks=0, className="btn-launch"),
            ], style={"display": "grid", "gridTemplateColumns": "1fr auto", "gap": "12px", "alignItems": "center"}),
            html.Div(id='preview-output', style={"marginTop": "20px"})
        ], className="glass-card")
    ])

def metrics_tab():
    return html.Div([
        html.Div([
            html.Div([html.Div("⏱️", className="card-header-icon icon-compute"), html.Div([html.Div("Lambda Performance & CloudWatch Logs", className="card-title"), html.Div("BusinessAnalyticsProcessor", className="card-subtitle")])], className="card-header"),
            html.Button('📊 Fetch CloudWatch Logs', id='fetch-metrics', n_clicks=0, className="btn-launch"),
            html.Div(id='metrics-output', style={"marginTop": "20px"})
        ], className="glass-card")
    ])

def log_tab():
    return html.Div([
        html.Div([
            html.Div([html.Div("📝", className="card-header-icon icon-dash"), html.Div([html.Div("Pipeline Activity Log", className="card-title"), html.Div("Real-time event tracking (auto-refresh)", className="card-subtitle")])], className="card-header"),
            html.Div(id='activity-log')
        ], className="glass-card")
    ])

# ===== CALLBACKS =====
@app.callback(Output('tab-content', 'children'), Input('main-tabs', 'value'))
def render_tab(tab):
    return {'tab-pipeline': pipeline_tab, 'tab-explorer': explorer_tab, 'tab-preview': preview_tab, 'tab-metrics': metrics_tab, 'tab-log': log_tab}.get(tab, pipeline_tab)()

@app.callback(Output('cpu-usage', 'children'), Output('mem-usage', 'children'), Input('sys-refresh', 'n_intervals'))
def update_sys(_):
    return f"CPU: {psutil.cpu_percent()}%", f"RAM: {psutil.virtual_memory().percent}%"

@app.callback(Output('upload-status', 'children'), Output('filename-input', 'value'), Input('upload-data', 'contents'), State('upload-data', 'filename'))
def upload_to_s3(contents, filename):
    if not contents: return dash.no_update, dash.no_update
    try:
        _, cs = contents.split(',')
        s3.put_object(Bucket=BUCKET_NAME, Key=f'raw-data/{filename}', Body=base64.b64decode(cs))
        log_event(f"📤 Uploaded {filename} → s3://{BUCKET_NAME}/raw-data/")
        return html.Div(f'✅ {filename} uploaded to S3', className="status-msg msg-success"), filename
    except Exception as e:
        log_event(f"❌ Upload failed: {e}")
        return html.Div(f'❌ {e}', className="status-msg msg-error"), dash.no_update

@app.callback(Output('analysis-output', 'children'), Input('analyze-button', 'n_clicks'), State('filename-input', 'value'), State('compute-mode', 'value'))
def run_analysis(n, filename, mode):
    if n == 0 or not filename: return dash.no_update
    use_lambda = 'lambda' in mode
    try:
        if use_lambda:
            log_event(f"⚡ Invoking Lambda for {filename}...")
            resp = lam.invoke(FunctionName='BusinessAnalyticsProcessor', InvocationType='RequestResponse', Payload=json.dumps({"bucket": BUCKET_NAME, "key": f"raw-data/{filename}"}))
            result = json.loads(resp['Payload'].read().decode('utf-8'))
            if result.get('statusCode') == 200:
                body = json.loads(result['body'])
                log_event(f"✅ Lambda complete → {body['result_key']}")
                return html.Div(f"✅ Lambda → {body['result_key']}", className="status-msg msg-success")
            return html.Div(f"❌ {result}", className="status-msg msg-error")
        else:
            log_event(f"💻 Local processing {filename}...")
            from analyze import run_pipeline
            result = run_pipeline(filename)
            if result['statusCode'] == 200:
                body = json.loads(result['body'])
                log_event(f"✅ Local done → {body['result_key']}")
                return html.Div(f"✅ {body['result_key']}", className="status-msg msg-success")
            return html.Div(f"❌ {result['body']}", className="status-msg msg-error")
    except Exception as e:
        log_event(f"❌ {e}")
        return html.Div(f'❌ {e}', className="status-msg msg-error")

@app.callback(Output('reports-list', 'children'), Input('refresh-button', 'n_clicks'), Input('analysis-output', 'children'))
def list_reports(n, _):
    try:
        resp = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix='reports/')
        if 'Contents' not in resp: return html.Div('No reports.', style={"color": "#64748b"})
        files = [o['Key'] for o in resp['Contents'] if o['Key'].endswith('.json')]
        return html.Div([html.Div([html.Span("📄"), html.Span(f.replace('reports/','')), html.Button("View", id={'type':'view-report','index':f}, className="view-btn")], className="report-row") for f in files])
    except Exception as e:
        return html.Div(f"Error: {e}", className="status-msg msg-error")

@app.callback(Output('dashboard-content', 'children'), Input({'type': 'view-report', 'index': dash.dependencies.ALL}, 'n_clicks'), prevent_initial_call=True)
def update_dashboard(n_clicks):
    if not any(n_clicks): return dash.no_update
    cid = ctx.triggered_id
    if not cid: return dash.no_update
    rk = cid['index']
    log_event(f"📊 Rendering dashboard for {rk}")
    try:
        data = json.loads(s3.get_object(Bucket=BUCKET_NAME, Key=rk)['Body'].read().decode('utf-8'))
        pbg = 'rgba(0,0,0,0)'
        kpis = html.Div([
            html.Div([html.Div(str(data.get('total_rows',0)), className="kpi-number"), html.Div("Rows", className="kpi-name")], className="kpi-tile"),
            html.Div([html.Div(str(data.get('total_columns',0)), className="kpi-number"), html.Div("Features", className="kpi-name")], className="kpi-tile"),
            html.Div([html.Div(str(len(data.get('numeric_columns',[]))), className="kpi-number"), html.Div("Numeric", className="kpi-name")], className="kpi-tile"),
            html.Div([html.Div(str(len(data.get('categorical_columns',[]))), className="kpi-number"), html.Div("Categorical", className="kpi-name")], className="kpi-tile"),
        ], className="kpi-row")
        charts = []
        for col, counts in list(data.get('categorical_summary',{}).items())[:2]:
            fig = px.pie(names=list(counts.keys()), values=list(counts.values()), title=f"{col}", template="plotly_dark", color_discrete_sequence=px.colors.sequential.Plasma_r, hole=0.4)
            fig.update_layout(paper_bgcolor=pbg, plot_bgcolor=pbg, margin=dict(t=40,b=20,l=20,r=20), font=dict(family="Inter"))
            charts.append(html.Div(dcc.Graph(figure=fig, config={'displayModeBar': False}), className="chart-wrapper"))
        ns = data.get('numeric_summary',{})
        if ns:
            means = {c: round(s.get('mean',0),2) for c,s in ns.items()}
            fig2 = px.bar(x=list(means.keys()), y=list(means.values()), title="Feature Averages", template="plotly_dark")
            fig2.update_traces(marker=dict(color=list(means.values()), colorscale='Viridis'))
            fig2.update_layout(paper_bgcolor=pbg, plot_bgcolor=pbg, font=dict(family="Inter"))
            charts.append(html.Div(dcc.Graph(figure=fig2, config={'displayModeBar': False}), className="chart-wrapper"))
            stds = {c: round(s.get('std',0),2) for c,s in ns.items()}
            fig_s = px.bar(x=list(stds.keys()), y=list(stds.values()), title="Std Deviation", template="plotly_dark")
            fig_s.update_traces(marker_color='#f59e0b')
            fig_s.update_layout(paper_bgcolor=pbg, plot_bgcolor=pbg, font=dict(family="Inter"))
            charts.append(html.Div(dcc.Graph(figure=fig_s, config={'displayModeBar': False}), className="chart-wrapper"))
        corr = data.get('correlation',{})
        if corr:
            cols = list(corr.keys())
            z = [[corr[c][r] for r in cols] for c in cols]
            fig3 = go.Figure(data=go.Heatmap(z=z, x=cols, y=cols, colorscale='Viridis', zmin=-1, zmax=1))
            fig3.update_layout(title="Correlation Matrix", template="plotly_dark", paper_bgcolor=pbg, plot_bgcolor=pbg, font=dict(family="Inter"))
            charts.append(html.Div(dcc.Graph(figure=fig3, config={'displayModeBar': False}), className="chart-wrapper"))
        if ns and len(ns)>2:
            cols_r = list(ns.keys())
            fig_r = go.Figure()
            fig_r.add_trace(go.Scatterpolar(r=[ns[c].get('min',0) for c in cols_r], theta=cols_r, fill='toself', name='Min', line_color='#06b6d4'))
            fig_r.add_trace(go.Scatterpolar(r=[ns[c].get('max',0) for c in cols_r], theta=cols_r, fill='toself', name='Max', line_color='#f43f5e'))
            fig_r.update_layout(title="Min/Max Radar", template="plotly_dark", paper_bgcolor=pbg, font=dict(family="Inter"), polar=dict(bgcolor='rgba(0,0,0,0)'))
            charts.append(html.Div(dcc.Graph(figure=fig_r, config={'displayModeBar': False}), className="chart-wrapper"))
        return html.Div([html.Div(f"📋 {rk.replace('reports/','')}", style={"fontSize":"15px","fontWeight":"600","marginBottom":"20px","color":"#818cf8","fontFamily":"JetBrains Mono"}), kpis, html.Div(charts, className="charts-grid")])
    except Exception as e:
        return html.Div(f"Error: {e}", className="status-msg msg-error")

@app.callback(Output('bucket-contents', 'children'), Input('scan-bucket', 'n_clicks'), prevent_initial_call=True)
def scan_bucket(n):
    try:
        log_event("🗂️ Scanning S3 bucket...")
        resp = s3.list_objects_v2(Bucket=BUCKET_NAME)
        if 'Contents' not in resp: return html.Div("Empty bucket.", style={"color":"#64748b"})
        objects = resp['Contents']
        total_size = sum(o['Size'] for o in objects)
        rows = [{"Key": o['Key'], "Size": f"{round(o['Size']/1024,2)} KB", "Modified": o['LastModified'].strftime("%Y-%m-%d %H:%M"), "Class": o.get('StorageClass','STANDARD')} for o in objects]
        stats = html.Div([
            html.Div([html.Div(str(len(objects)), className="kpi-number"), html.Div("Objects", className="kpi-name")], className="kpi-tile"),
            html.Div([html.Div(f"{round(total_size/1024,1)}", className="kpi-number"), html.Div("Total KB", className="kpi-name")], className="kpi-tile"),
            html.Div([html.Div(str(len([o for o in objects if 'raw-data' in o['Key']])), className="kpi-number"), html.Div("Raw Files", className="kpi-name")], className="kpi-tile"),
            html.Div([html.Div(str(len([o for o in objects if 'reports' in o['Key']])), className="kpi-number"), html.Div("Reports", className="kpi-name")], className="kpi-tile"),
        ], className="kpi-row")
        tbl = dash_table.DataTable(data=rows, columns=[{"name":c,"id":c} for c in ["Key","Size","Modified","Class"]],
            style_header={'backgroundColor':'#1e293b','color':'#94a3b8','fontWeight':'600','border':'1px solid #334155','fontFamily':'Inter'},
            style_cell={'backgroundColor':'#0f172a','color':'#f1f5f9','border':'1px solid #1e293b','fontSize':'12px','fontFamily':'JetBrains Mono','padding':'10px'},
            style_data_conditional=[{'if':{'row_index':'odd'},'backgroundColor':'#0a0f1e'}], page_size=15)
        return html.Div([stats, tbl])
    except Exception as e:
        return html.Div(f"Error: {e}", className="status-msg msg-error")

@app.callback(Output('preview-output', 'children'), Input('preview-btn', 'n_clicks'), State('preview-filename', 'value'), prevent_initial_call=True)
def preview_data(n, filename):
    if not filename: return html.Div("Enter filename.", className="status-msg msg-error")
    try:
        log_event(f"👁️ Previewing {filename}")
        df = pd.read_csv(StringIO(s3.get_object(Bucket=BUCKET_NAME, Key=f'raw-data/{filename}')['Body'].read().decode('utf-8')))
        info = html.Div([
            html.Div([html.Div(str(len(df)), className="kpi-number"), html.Div("Rows", className="kpi-name")], className="kpi-tile"),
            html.Div([html.Div(str(len(df.columns)), className="kpi-number"), html.Div("Columns", className="kpi-name")], className="kpi-tile"),
            html.Div([html.Div(str(df.isnull().sum().sum()), className="kpi-number"), html.Div("Null Values", className="kpi-name")], className="kpi-tile"),
            html.Div([html.Div(str(len(df.dtypes.unique())), className="kpi-number"), html.Div("Data Types", className="kpi-name")], className="kpi-tile"),
        ], className="kpi-row")
        dtypes = html.Div([html.Span(f"{c}: {df[c].dtype}", className="badge", style={"margin":"3px"}) for c in df.columns], style={"marginBottom":"16px"})
        tbl = dash_table.DataTable(data=df.head(50).to_dict('records'), columns=[{"name":c,"id":c} for c in df.columns],
            style_header={'backgroundColor':'#1e293b','color':'#94a3b8','fontWeight':'600','border':'1px solid #334155','fontFamily':'Inter'},
            style_cell={'backgroundColor':'#0f172a','color':'#f1f5f9','border':'1px solid #1e293b','fontSize':'12px','fontFamily':'JetBrains Mono','padding':'8px','maxWidth':'200px','overflow':'hidden','textOverflow':'ellipsis'},
            style_data_conditional=[{'if':{'row_index':'odd'},'backgroundColor':'#0a0f1e'}], page_size=20, sort_action='native', filter_action='native')
        return html.Div([info, dtypes, tbl])
    except Exception as e:
        return html.Div(f"Error: {e}", className="status-msg msg-error")

@app.callback(Output('metrics-output', 'children'), Input('fetch-metrics', 'n_clicks'), prevent_initial_call=True)
def fetch_metrics(n):
    try:
        log_event("⏱️ Fetching CloudWatch logs...")
        lg = '/aws/lambda/BusinessAnalyticsProcessor'
        streams = logs_client.describe_log_streams(logGroupName=lg, orderBy='LastEventTime', descending=True, limit=5).get('logStreams',[])
        if not streams: return html.Div("No logs found. Run Lambda first.", style={"color":"#64748b"})
        entries = []
        for st in streams[:3]:
            for ev in logs_client.get_log_events(logGroupName=lg, logStreamName=st['logStreamName'], limit=15).get('events',[]):
                msg = ev['message'].strip()
                if msg:
                    ts = datetime.fromtimestamp(ev['timestamp']/1000).strftime("%H:%M:%S")
                    entries.append({"Time": ts, "Log": msg[:300]})
        if not entries: entries = [{"Time":"-","Log":"No entries."}]
        tbl = dash_table.DataTable(data=entries[:25], columns=[{"name":"Time","id":"Time"},{"name":"Log","id":"Log"}],
            style_header={'backgroundColor':'#1e293b','color':'#94a3b8','fontWeight':'600','border':'1px solid #334155','fontFamily':'Inter'},
            style_cell={'backgroundColor':'#0f172a','color':'#f1f5f9','border':'1px solid #1e293b','fontSize':'11px','fontFamily':'JetBrains Mono','padding':'8px','whiteSpace':'normal'},
            style_cell_conditional=[{'if':{'column_id':'Time'},'width':'80px','color':'#6366f1'}])
        return tbl
    except Exception as e:
        return html.Div(f"CloudWatch error: {e}", className="status-msg msg-error")

@app.callback(Output('activity-log', 'children'), Input('sys-refresh', 'n_intervals'))
def update_log(_):
    if not activity_log: return html.Div("No activity yet.", style={"color":"#64748b","padding":"20px"})
    return html.Div([html.Div([html.Span(e['time'], style={"color":"#6366f1","fontFamily":"JetBrains Mono","fontSize":"12px","minWidth":"70px"}), html.Span(e['msg'], style={"fontSize":"13px"})], className="report-row") for e in activity_log])

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8050, debug=False)
