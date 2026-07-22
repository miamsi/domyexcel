# version 1
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import duckdb
import pandas as pd
from groq import Groq
import os
import io

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

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        # Read uploaded bytes into memory safely
        contents = await file.read()
        buffer = io.BytesIO(contents)

        if file.filename.endswith('.csv'):
            df = pd.read_csv(buffer)
        elif file.filename.endswith('.xlsx'):
            df = pd.read_excel(buffer)
        else:
            return {"error": "Unsupported file format. Please upload .csv or .xlsx"}

        # Store physically in DuckDB memory as a table
        con.execute("CREATE OR REPLACE TABLE uploaded_data AS SELECT * FROM df")
        
        return {
            "message": "File uploaded and transformed to DuckDB successfully.", 
            "columns": list(df.columns)
        }
    except Exception as e:
        return {"error": f"Failed to process file: {str(e)}"}

@app.post("/query")
async def query_data(prompt: str = Form(...)):
    try:
        # Get schema to help Groq understand the data structure
        schema_query = "DESCRIBE uploaded_data;"
        schema_df = con.execute(schema_query).df()
        schema_str = schema_df.to_string()
    except Exception:
        return {"error": "No dataset found in memory. Please upload a file first.", "sql": ""}

    system_prompt = f"You are a strict SQL generator for DuckDB. The table name is 'uploaded_data'. Do not include markdown formatting or explanations. Here is the schema:\n{schema_str}"
    
    try:
        completion = client.chat.completions.create(
            model="llama3-70b-8192",
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
        return {"error": f"Execution error: {str(e)}", "sql": generated_sql if 'generated_sql' in locals() else ""}
