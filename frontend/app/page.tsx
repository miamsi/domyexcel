// version 1
'use client';
import { useState } from 'react';

export default function Home() {
  const [file, setFile] = useState<File | null>(null);
  const [prompt, setPrompt] = useState('');
  const [result, setResult] = useState<any[]>([]);
  const [sql, setSql] = useState('');
  const [loading, setLoading] = useState(false);

  // Note: Replace this with your actual SnapDeploy URL later
  const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://127.0.0.1:8000'; 

  const handleUpload = async () => {
    if (!file) return;
    setLoading(true);
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      await fetch(`${BACKEND_URL}/upload`, { 
        method: 'POST', 
        body: formData 
      });
      alert('File uploaded to DuckDB successfully!');
    } catch (error) {
      console.error(error);
      alert('Upload failed');
    }
    setLoading(false);
  };

  const handleQuery = async () => {
    if (!prompt) return;
    setLoading(true);
    const formData = new FormData();
    formData.append('prompt', prompt);
    
    try {
      const res = await fetch(`${BACKEND_URL}/query`, { 
        method: 'POST', 
        body: formData 
      });
      const data = await res.json();
      setSql(data.sql);
      setResult(data.result || []);
    } catch (error) {
      console.error(error);
    }
    setLoading(false);
  };

  return (
    <div style={{ padding: '40px', fontFamily: 'sans-serif', maxWidth: '800px', margin: '0 auto' }}>
      <h1>Data Chatbot</h1>
      
      <div style={{ marginBottom: '30px', padding: '20px', border: '1px solid #ccc' }}>
        <h3>1. Upload Data</h3>
        <input 
          type="file" 
          accept=".csv, .xlsx" 
          onChange={(e) => setFile(e.target.files?.[0] || null)} 
          style={{ marginRight: '10px' }}
        />
        <button onClick={handleUpload} disabled={loading}>
          {loading ? 'Processing...' : 'Upload File'}
        </button>
      </div>

      <div style={{ marginBottom: '30px', padding: '20px', border: '1px solid #ccc' }}>
        <h3>2. Chat with Data</h3>
        <input 
          type="text" 
          value={prompt} 
          onChange={(e) => setPrompt(e.target.value)} 
          placeholder="e.g., Show me the top 5 rows" 
          style={{ width: '70%', padding: '8px', marginRight: '10px' }}
        />
        <button onClick={handleQuery} disabled={loading} style={{ padding: '8px 15px' }}>
          Ask
        </button>
      </div>

      {sql && (
        <div style={{ marginBottom: '20px', padding: '15px', backgroundColor: '#f5f5f5' }}>
          <strong>Generated SQL:</strong>
          <pre style={{ margin: '10px 0 0 0', whiteSpace: 'pre-wrap' }}>{sql}</pre>
        </div>
      )}

      {result.length > 0 && (
        <div style={{ overflowX: 'auto' }}>
          <table border={1} cellPadding={8} style={{ borderCollapse: 'collapse', width: '100%' }}>
            <thead style={{ backgroundColor: '#eee' }}>
              <tr>
                {Object.keys(result[0]).map((key) => <th key={key}>{key}</th>)}
              </tr>
            </thead>
            <tbody>
              {result.map((row, i) => (
                <tr key={i}>
                  {Object.values(row).map((val: any, j) => <td key={j}>{val}</td>)}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
