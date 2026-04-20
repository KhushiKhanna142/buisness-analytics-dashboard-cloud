import boto3
import pandas as pd
import json
from io import StringIO

BUCKET_NAME = 'analytics-dashboard-cc-project'

def download_csv_from_s3(filename):
    s3 = boto3.client('s3')
    response = s3.get_object(Bucket=BUCKET_NAME, Key=f'raw-data/{filename}')
    content = response['Body'].read().decode('utf-8')
    df = pd.read_csv(StringIO(content))
    return df

def analyze_data(df):
    summary = {
        'total_rows': len(df),
        'total_columns': len(df.columns),
        'columns': list(df.columns),
        'numeric_summary': json.loads(df.describe().to_json())
    }
    return summary

def save_results_to_s3(summary, result_filename):
    s3 = boto3.client('s3')
    result_json = json.dumps(summary, indent=2)
    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=f'reports/{result_filename}',
        Body=result_json,
        ContentType='application/json'
    )
    print(f'Results saved to reports/{result_filename}')

def run_pipeline(filename):
    print(f'Downloading {filename} from S3...')
    df = download_csv_from_s3(filename)
    print(f'Loaded {len(df)} rows')
    summary = analyze_data(df)
    result_filename = filename.replace('.csv', '_results.json')
    save_results_to_s3(summary, result_filename)
    return summary

if __name__ == '__main__':
    run_pipeline('sample.csv')
