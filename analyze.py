import boto3
import pandas as pd
import json
from io import StringIO
import traceback

BUCKET_NAME = 'analytics-dashboard-cc-project'
s3_client = boto3.client('s3')

def download_csv_from_s3(filename):
    response = s3_client.get_object(Bucket=BUCKET_NAME, Key=f'raw-data/{filename}')
    content = response['Body'].read().decode('utf-8')
    df = pd.read_csv(StringIO(content))
    return df

def analyze_data(df):
    """
    Advanced analysis mirroring the Lambda function for local fallback.
    """
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    summary = {
        "status": "success",
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "columns": list(df.columns),
        "numeric_columns": numeric_cols,
        "categorical_columns": categorical_cols,
    }
    
    # Numeric Summary
    if numeric_cols:
        summary["numeric_summary"] = json.loads(df[numeric_cols].describe().to_json())
        if len(numeric_cols) > 1:
            corr_matrix = df[numeric_cols].corr().fillna(0).to_dict()
            summary["correlation"] = corr_matrix
            
    # Categorical Summary
    cat_summary = {}
    for col in categorical_cols:
        value_counts = df[col].value_counts().head(5).to_dict()
        cat_summary[col] = {str(k): int(v) for k, v in value_counts.items()}
    summary["categorical_summary"] = cat_summary
    
    return summary

def save_results_to_s3(summary, result_filename):
    result_json = json.dumps(summary, indent=2)
    s3_client.put_object(
        Bucket=BUCKET_NAME,
        Key=f'reports/{result_filename}',
        Body=result_json,
        ContentType='application/json'
    )
    print(f'Results saved to s3://{BUCKET_NAME}/reports/{result_filename}')

def run_pipeline(filename):
    print(f'Starting local processing for {filename}...')
    try:
        df = download_csv_from_s3(filename)
        print(f'Loaded {len(df)} rows')
        summary = analyze_data(df)
        summary['file'] = f"raw-data/{filename}"
        
        result_filename = filename.replace('.csv', '_results.json')
        save_results_to_s3(summary, result_filename)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Local analysis successful',
                'result_key': f'reports/{result_filename}'
            })
        }
    except Exception as e:
        print(f"Error: {str(e)}")
        print(traceback.format_exc())
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

if __name__ == '__main__':
    # Test locally
    run_pipeline('sample.csv')
