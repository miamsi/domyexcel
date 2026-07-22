# version 1
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import duckdb
import pandas as pd
from groq import Groq
import os

app = FastAPI()

# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# In-memory DuckDB connection
con = duckdb.connect(database=':memory:')

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    # Read the file into a pandas dataframe
    if file.filename.endswith('.csv'):
        df = pd.read_csv(file.file)
    elif file.filename.endswith('.xlsx'):
        df = pd.read_excel(file.file)
    else:
        return {"error": "Unsupported file format"}

    # Register dataframe to DuckDB as 'uploaded_data'
    con.register('uploaded_data', df)
    
    return {
        "message": "File uploaded and transformed to DuckDB successfully.", 
        "columns": list(df.columns)
    }

@app.post("/query")
async def query_data(prompt: str = Form(...)):
    # Get schema to help Groq understand the data structure
    schema_query = "DESCRIBE uploaded_data;"
    schema_df = con.execute(schema_query).df()
    schema_str = schema_df.to_string()

    # Instruct Groq to generate only the SQL
    system_prompt = f"You are a strict SQL generator for DuckDB. The table name is 'uploaded_data'. Do not include markdown formatting or explanations. Here is the schema:\n{schema_str}"
    
    completion = client.chat.completions.create(
        model="llama3-70b-8192",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
    )
    
    generated_sql = completion.choices[0].message.content.strip()
    # Clean up formatting just in case Groq returns markdown
    generated_sql = generated_sql.replace("```sql", "").replace("```", "").strip()

    try:
        # Execute the generated SQL query in DuckDB
        result_df = con.execute(generated_sql).df()
        return {"sql": generated_sql, "result": result_df.to_dict(orient="records")}
    except Exception as e:
        return {"error": str(e), "sql": generated_sql}
