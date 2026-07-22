# version 1
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import duckdb
import pandas as pd
from groq import Groq
import os
import tempfile
import shutil

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# In-memory DuckDB connection
con = duckdb.connect(database=':memory:')

# Changed to standard 'def' because disk I/O and pandas are synchronous
@app.post("/upload")
def upload_file(file: UploadFile = File(...)):
    tmp_path = None
    try:
        # 1. Safely stream the incoming file to a physical temporary file on disk
        suffix = ".csv" if file.filename.endswith('.csv') else ".xlsx"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = tmp.name

        # 2. Pandas reads from the physical file path (bulletproof)
        if suffix == '.csv':
            df = pd.read_csv(tmp_path)
        else:
            df = pd.read_excel(tmp_path)

        # 3. Store in DuckDB
        con.execute("CREATE OR REPLACE TABLE uploaded_data AS SELECT * FROM df")
        
        return {
            "message": "File uploaded and transformed to DuckDB successfully.", 
            "columns": list(df.columns)
        }
    except Exception as e:
        return {"error": f"Failed to process file: {str(e)}"}
    finally:
        # 4. Clean up the temporary file so we don't fill up the server's storage
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)

@app.post("/query")
def query_data(prompt: str = Form(...)):
    try:
        # Get schema to help Groq understand the data structure
        schema_query = "DESCRIBE uploaded_data;"
        schema_df = con.execute(schema_query).df()
        schema_str = schema_df.to_string()
    except Exception:
        return {"error": "No dataset found in memory. Please upload a file first.", "sql": ""}

    system_prompt = f"You are a strict SQL generator for DuckDB. The table name is 'uploaded_data'. Do not include markdown formatting or explanations. Here is the schema:\n{schema_str}"
    
    generated_sql = ""
    
    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
        )
        
        generated_sql = completion.choices[0].message.content.strip()
        generated_sql = generated_sql.replace("```sql", "").replace("```", "").strip()

        result_df = con.execute(generated_sql).df()
        return {"sql": generated_sql, "result": result_df.to_dict(orient="records")}
    except Exception as e:
        return {"error": f"Execution error: {str(e)}", "sql": generated_sql}
