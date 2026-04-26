import json
import boto3
import pandas as pd
from io import StringIO
import traceback

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    """
    AWS Lambda handler function.
    Expected event payload:
    {
        "bucket": "analytics-dashboard-cc-project",
        "key": "raw-data/sample.csv"
    }
    """
    print(f"Received event: {json.dumps(event)}")
    
    try:
        # Extract bucket and key from the event
        bucket_name = event.get('bucket')
        file_key = event.get('key')
        
        if not bucket_name or not file_key:
            raise ValueError("Event must contain 'bucket' and 'key'")

        print(f"Downloading s3://{bucket_name}/{file_key}")
        
        # 1. Download CSV from S3
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        csv_content = response['Body'].read().decode('utf-8')
        
        # 2. Load into Pandas
        df = pd.read_csv(StringIO(csv_content))
        print(f"Successfully loaded data with shape: {df.shape}")
        
        # 3. Perform Advanced Analysis
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        # Basic stats
        summary = {
            "status": "success",
            "file": file_key,
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "columns": list(df.columns),
            "numeric_columns": numeric_cols,
            "categorical_columns": categorical_cols,
        }
        
        # Numeric Summary
        if numeric_cols:
            summary["numeric_summary"] = json.loads(df[numeric_cols].describe().to_json())
            
            # Add correlation matrix if multiple numeric columns
            if len(numeric_cols) > 1:
                corr_matrix = df[numeric_cols].corr().fillna(0).to_dict()
                summary["correlation"] = corr_matrix
        
        # Categorical Summary (Top 5 values for pie charts)
        cat_summary = {}
        for col in categorical_cols:
            value_counts = df[col].value_counts().head(5).to_dict()
            # Convert keys to strings just in case
            cat_summary[col] = {str(k): int(v) for k, v in value_counts.items()}
        
        summary["categorical_summary"] = cat_summary
        
        # 4. Save results back to S3
        # Extract filename without prefix
        base_filename = file_key.split('/')[-1]
        result_key = f"reports/{base_filename.replace('.csv', '_results.json')}"
        
        s3_client.put_object(
            Bucket=bucket_name,
            Key=result_key,
            Body=json.dumps(summary, indent=2),
            ContentType='application/json'
        )
        
        print(f"Analysis complete. Results saved to s3://{bucket_name}/{result_key}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Analysis successful',
                'result_key': result_key
            })
        }

    except Exception as e:
        print(f"Error processing data: {str(e)}")
        print(traceback.format_exc())
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': str(e)
            })
        }
