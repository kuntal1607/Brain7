import React, { useState } from 'react';
import { Upload, Zap, CheckCircle, Loader2, FileText, ListTodo, Activity, Compass, Clock, CheckSquare, Square } from 'lucide-react';

function App() {
  const [files, setFiles] = useState([]);
  const [summary, setSummary] = useState("");
  const [tasks, setTasks] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(false);

  const parseStringToDate = (dateStr) => {
    if (!dateStr) return new Date(8640000000000000); 
    
    const cleanStr = dateStr.toLowerCase().trim();
    const now = new Date();

    if (cleanStr.includes('today') || cleanStr.includes('now')) return now;
    if (cleanStr.includes('tomorrow')) {
      const tomorrow = new Date();
      tomorrow.setDate(now.getDate() + 1);
      return tomorrow;
    }

    const timestamp = Date.parse(dateStr);
    if (!isNaN(timestamp)) return new Date(timestamp);

    const match = cleanStr.match(/(\d+)/);
    if (match) {
      const day = parseInt(match[1], 10);
      const testDate = new Date(now.getFullYear(), now.getMonth(), day);
      if (testDate < now && day < now.getDate()) {
        testDate.setMonth(now.getMonth() + 1);
      }
      return testDate;
    }

    return new Date(8640000000000000);
  };

  const handleProcess = async () => {
    if (files.length === 0) return alert("Please upload execution scripts or syllabus profiles first!");
    setLoading(true);
    setSummary("");
    setLogs([]);

    try {
      let combinedIncomingTasks = [];
      let combinedLogs = [];
      let lastSummary = "";

      for (let i = 0; i < files.length; i++) {
        const formData = new FormData();
        formData.append('file', files[i]);

        const response = await fetch('https://brain7-backend.onrender.com/agent/process', {
          method: 'POST',
          body: formData,
        });

        if (!response.ok) throw new Error(`Backend pipeline connection dropped on file ${files[i].name}`);
        const data = await response.json();
        
        lastSummary = data.summary || "No synthesis compiled.";
        if (data.logs) combinedLogs = [...combinedLogs, ...data.logs];
        if (data.tasks) combinedIncomingTasks = [...combinedIncomingTasks, ...data.tasks];
      }

      setSummary(lastSummary);
      setLogs(combinedLogs);
      
      setTasks(prevTasks => {
        const combinedTasks = [...prevTasks, ...combinedIncomingTasks];
        return combinedTasks.sort((a, b) => parseStringToDate(a.deadline) - parseStringToDate(b.deadline));
      });

      setFiles([]);

    } catch (error) {
      setSummary("API Pipeline Disconnected: Please ensure your FastAPI server is running on port 8000.");
      setLogs(["Connection setup to backend failed."]);
    } finally {
      setLoading(false);
    }
  };

  const toggleTaskCompletion = (index) => {
    setTasks(prevTasks => 
      prevTasks.map((task, i) => 
        i === index 
          ? { ...task, status: task.status === "Completed" ? "Ready" : "Completed" } 
          : task
      )
    );
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-6 font-sans antialiased selection:bg-indigo-500/30">
      
      <header className="max-w-7xl mx-auto mb-8 bg-slate-800/50 backdrop-blur-md p-5 rounded-3xl border border-slate-700/50 flex items-center justify-center shadow-xl">
        <div className="flex items-center gap-3 justify-center">
          <div className="p-2.5 bg-indigo-500/10 rounded-xl border border-indigo-500/20">
            <Zap className="text-indigo-400 w-5 h-5 fill-indigo-400/20 animate-pulse" />
          </div>
          <h1 className="text-2xl font-black tracking-tight bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent text-center">
            Brain7- AI agent
          </h1>
        </div>
      </header>

      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        
        <div className="lg:col-span-3 space-y-6 order-2 lg:order-1">
          {summary ? (
            <div className="bg-slate-800/80 rounded-3xl shadow-xl border border-slate-700/50 overflow-hidden">
              <div className="bg-slate-900/80 px-4 py-3 flex items-center gap-2 text-slate-200 text-xs font-bold border-b border-slate-800 uppercase tracking-wider">
                <CheckCircle className="text-emerald-400 w-4 h-4" />
                Analysis Summary
              </div>
              <div className="p-4 text-xs text-slate-300 whitespace-pre-wrap leading-relaxed max-h-[40vh] overflow-y-auto">
                {summary}
              </div>
            </div>
          ) : (
            <div className="bg-slate-800/20 rounded-3xl p-6 text-center border border-slate-800/60 text-xs text-slate-500 italic">
              Awaiting system file parsing to compile operational synthesis text logs...
            </div>
          )}

          {logs.length > 0 && (
            <div className="bg-slate-800/60 rounded-3xl p-4 border border-slate-700/50 shadow-inner">
              <h3 className="text-[10px] font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <Activity size={12} className="text-indigo-400" /> Continuous Engine Operations
              </h3>
              <div className="space-y-1.5 max-h-40 overflow-y-auto pr-1">
                {logs.map((log, index) => (
                  <p key={index} className="text-[10px] font-mono bg-slate-900/50 p-2 rounded-xl border border-slate-800 text-slate-400">
                    {log}
                  </p>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="lg:col-span-4 order-1 lg:order-2">
          <div className="bg-slate-800/40 backdrop-blur-sm border-2 border-dashed border-slate-700/80 rounded-3xl p-8 text-center hover:border-indigo-500/40 transition-all duration-300 sticky top-28 shadow-xl">
            <input 
              type="file" 
              id="upload" 
              className="hidden" 
              multiple 
              onChange={(e) => setFiles(Array.from(e.target.files))} 
            />
            <label htmlFor="upload" className="cursor-pointer group block">
              <div className="w-16 h-16 bg-slate-800 rounded-2xl flex items-center justify-center mx-auto mb-4 group-hover:bg-slate-700 border border-slate-700 shadow-md group-hover:border-indigo-500/30 transition-all">
                <FileText className="text-slate-400 group-hover:text-indigo-400 w-7 h-7 transition-colors" />
              </div>
              <h2 className="text-base font-bold text-slate-100 group-hover:text-indigo-300 transition-colors">
                {files.length > 0 ? `${files.length} files` : "Upload Files"}
              </h2>
              <p className="text-xs text-slate-400 mt-2 bg-slate-900/40 inline-block px-3 py-1 rounded-lg border border-slate-800 font-medium truncate max-w-xs">
                {files.length > 0 ? files.map(f => f.name).join(', ') : "Select PDF, DOCX"}
              </p>
            </label>

            {files.length > 0 && (
              <button 
                onClick={handleProcess}
                disabled={loading}
                className="mt-6 w-full bg-indigo-600 text-white py-3.5 rounded-xl font-bold flex items-center justify-center gap-2 hover:bg-indigo-500 active:scale-[0.99] transition-all disabled:opacity-50 text-sm shadow-lg shadow-indigo-600/30"
              >
                {loading ? <Loader2 className="animate-spin w-4 h-4" /> : <Compass size={16} />}
                {loading ? "Processing..." : "Enter to upload files"}
              </button>
            )}
          </div>
        </div>

        <div className="lg:col-span-5 space-y-3 order-3">
          <div className="flex items-center gap-2 text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 px-1">
            <ListTodo className="w-4 h-4 text-indigo-400" />
            Check-List Roadmap  ({tasks.length})
          </div>

          {tasks.length === 0 ? (
            <div className="bg-slate-800/20 rounded-3xl p-12 text-center border border-slate-800 text-slate-500 text-sm italic">
              No entries initialized yet. Load any files using the center hub.
            </div>
          ) : (
            <div className="space-y-2.5 max-h-[75vh] overflow-y-auto pr-1">
              {tasks.map((task, index) => {
                const isCompleted = task.status === "Completed";
                return (
                  <div 
                    key={index} 
                    onClick={() => toggleTaskCompletion(index)}
                    className={`p-4 rounded-2xl border transition-all duration-150 cursor-pointer flex items-center justify-between gap-4 select-none ${
                      isCompleted 
                        ? 'bg-slate-800/20 border-slate-800/80 opacity-50' 
                        : 'bg-slate-800 border-slate-700/60 hover:border-slate-600 hover:bg-slate-800/90 shadow-md'
                    }`}
                  >
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="flex-shrink-0 text-indigo-400">
                        {isCompleted ? (
                          <CheckSquare className="w-4 h-4 text-emerald-400" />
                        ) : (
                          <Square className="w-4 h-4 text-slate-500" />
                        )}
                      </div>

                      <div className="min-w-0">
                        <h3 className={`font-bold text-sm tracking-tight truncate max-w-xs md:max-w-sm ${
                          isCompleted ? 'line-through text-slate-500 font-normal' : 'text-slate-200'
                        }`}>
                          {task.title}
                        </h3>
                      </div>
                    </div>

                    <div className="flex-shrink-0 flex items-center gap-1.5 text-xs font-semibold bg-slate-900/60 px-3 py-1.5 rounded-xl border border-slate-800/80">
                      <Clock size={12} className={isCompleted ? 'text-slate-600' : 'text-indigo-400'} />
                      <span className={isCompleted ? 'line-through text-slate-600 font-normal' : 'text-slate-300'}>
                        {task.deadline}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

export default App;