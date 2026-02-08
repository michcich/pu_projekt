import React, { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { companiesApi, reportsApi, chatApi } from '../api/client';
import { 
  ArrowLeft, Upload, FileText, Trash2, MessageSquare, 
  Send, Bot, User, Loader2, TrendingUp 
} from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import ChartRenderer from '../components/ChartRenderer';

const CompanyDetailsPage = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const [company, setCompany] = useState(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  
  // Chat state
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isChatLoading, setIsChatLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    fetchCompanyDetails();
    // Load chat history if session exists in localStorage for this company
    const savedSession = localStorage.getItem(`chat_session_${id}`);
    if (savedSession) {
      setSessionId(savedSession);
      fetchChatHistory(savedSession);
    }
  }, [id]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  const fetchCompanyDetails = async () => {
    try {
      const response = await companiesApi.getOne(id);
      setCompany(response.data);
    } catch (error) {
      console.error('Error fetching company:', error);
      if (error.response?.status === 404) navigate('/');
    } finally {
      setLoading(false);
    }
  };

  const fetchChatHistory = async (sid) => {
    try {
      const response = await chatApi.getHistory(sid);
      // Map history to include chart_data if we stored it (backend currently doesn't store chart_data in history table, 
      // so charts only appear in current session unless we persist them. 
      // For now, history load will just show text.)
      setMessages(response.data);
    } catch (error) {
      console.error('Error fetching history:', error);
      localStorage.removeItem(`chat_session_${id}`);
      setSessionId(null);
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    const formData = new FormData();
    formData.append('file', file);
    formData.append('company_id', id);
    
    // REMOVED: Manual period guessing logic that was forcing "2024"
    // The backend will now extract the correct period from the PDF content via AI/Regex
    
    setUploading(true);
    try {
      await reportsApi.upload(formData);
      await fetchCompanyDetails();
    } catch (error) {
      alert('Błąd uploadu: ' + (error.response?.data?.detail || error.message));
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteReport = async (reportId) => {
    if (!window.confirm('Usunąć ten raport?')) return;
    try {
      await reportsApi.delete(reportId);
      fetchCompanyDetails();
    } catch (error) {
      console.error('Error deleting report:', error);
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!inputMessage.trim() || isChatLoading) return;

    const userMsg = { role: 'user', content: inputMessage };
    setMessages(prev => [...prev, userMsg]);
    setInputMessage('');
    setIsChatLoading(true);

    try {
      const response = await chatApi.sendMessage({
        message: userMsg.content,
        company_id: parseInt(id),
        session_id: sessionId
      });

      const data = response.data;
      
      if (!sessionId) {
        setSessionId(data.session_id);
        localStorage.setItem(`chat_session_${id}`, data.session_id);
      }

      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: data.response,
        chart_data: data.has_chart ? data.chart_data : null
      }]);
    } catch (error) {
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Przepraszam, wystąpił błąd połączenia.' 
      }]);
    } finally {
      setIsChatLoading(false);
    }
  };

  const handleAnalyzeTrends = async () => {
    if (isChatLoading) return;
    
    const userMsg = { role: 'user', content: "Przeprowadź analizę trendów dla tej firmy." };
    setMessages(prev => [...prev, userMsg]);
    setIsChatLoading(true);

    try {
      const response = await chatApi.analyze(id);
      const analysis = response.data.result.analysis || JSON.stringify(response.data.result);
      
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: `**Analiza Trendów:**\n\n${analysis}` 
      }]);
    } catch (error) {
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Nie udało się przeprowadzić analizy trendów.' 
      }]);
    } finally {
      setIsChatLoading(false);
    }
  };

  if (loading) return <div className="text-center py-12 text-gray-400">Ładowanie...</div>;
  if (!company) return null;

  return (
    <div className="h-[calc(100vh-8rem)] flex flex-col lg:flex-row gap-6">
      {/* Left Column: Company Info & Reports */}
      <div className="lg:w-1/3 flex flex-col gap-6 overflow-hidden">
        {/* Company Header */}
        <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 shrink-0">
          <button 
            onClick={() => navigate('/')}
            className="flex items-center text-gray-400 hover:text-white mb-4 transition-colors"
          >
            <ArrowLeft size={16} className="mr-1" /> Wróć
          </button>
          
          <h1 className="text-2xl font-bold text-white mb-2">{company.name}</h1>
          <div className="flex flex-wrap gap-2 mb-4">
            {company.ticker && (
              <span className="px-2 py-1 bg-gray-700 text-gray-300 text-xs rounded font-mono">
                {company.ticker}
              </span>
            )}
            {company.industry && (
              <span className="px-2 py-1 bg-gray-700 text-gray-300 text-xs rounded">
                {company.industry}
              </span>
            )}
          </div>
          <p className="text-gray-400 text-sm line-clamp-3">{company.description}</p>
        </div>

        {/* Reports List */}
        <div className="bg-gray-800 rounded-xl border border-gray-700 flex flex-col flex-1 overflow-hidden">
          <div className="p-4 border-b border-gray-700 flex justify-between items-center bg-gray-800 z-10">
            <h3 className="font-semibold text-white flex items-center">
              <FileText size={18} className="mr-2 text-blue-400" />
              Raporty ({company.reports.length})
            </h3>
            <label className={`
              flex items-center px-3 py-1.5 bg-blue-600 hover:bg-blue-700 
              text-white text-sm rounded-lg cursor-pointer transition-colors
              ${uploading ? 'opacity-50 cursor-not-allowed' : ''}
            `}>
              <Upload size={16} className="mr-2" />
              {uploading ? 'Wgrywanie...' : 'Dodaj PDF'}
              <input 
                type="file" 
                accept=".pdf" 
                className="hidden" 
                onChange={handleFileUpload}
                disabled={uploading}
              />
            </label>
          </div>
          
          <div className="overflow-y-auto p-2 space-y-2 flex-1">
            {company.reports.length === 0 ? (
              <div className="text-center py-8 text-gray-500 text-sm">
                Brak raportów. Wgraj pierwszy plik PDF.
              </div>
            ) : (
              company.reports.map((report) => (
                <div 
                  key={report.id}
                  className="flex items-center justify-between p-3 bg-gray-700/30 rounded-lg hover:bg-gray-700/50 transition-colors group"
                >
                  <div className="min-w-0">
                    <div className="font-medium text-gray-200 truncate text-sm">
                      {report.report_period || report.filename}
                    </div>
                    <div className="text-xs text-gray-500">
                      {new Date(report.upload_date).toLocaleDateString()} • {(report.file_size / 1024 / 1024).toFixed(2)} MB
                    </div>
                  </div>
                  <button 
                    onClick={() => handleDeleteReport(report.id)}
                    className="text-gray-500 hover:text-red-400 p-1.5 opacity-0 group-hover:opacity-100 transition-opacity"
                    title="Usuń raport"
                  >
                    <Trash2 size={16} />
                  </button>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Right Column: Chat */}
      <div className="lg:w-2/3 bg-gray-800 rounded-xl border border-gray-700 flex flex-col overflow-hidden">
        {/* Chat Header */}
        <div className="p-4 border-b border-gray-700 flex justify-between items-center bg-gray-800">
          <div className="flex items-center">
            <MessageSquare size={20} className="text-blue-400 mr-2" />
            <h3 className="font-semibold text-white">Asystent Finansowy</h3>
          </div>
          {company.reports.length > 1 && (
            <button
              onClick={handleAnalyzeTrends}
              disabled={isChatLoading}
              className="flex items-center px-3 py-1.5 bg-purple-600/20 text-purple-300 hover:bg-purple-600/30 rounded-lg text-sm transition-colors border border-purple-500/30"
            >
              <TrendingUp size={16} className="mr-2" />
              Analizuj trendy
            </button>
          )}
        </div>

        {/* Chat Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-900/50">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-gray-500 space-y-4">
              <Bot size={48} className="text-gray-700" />
              <div className="text-center max-w-md">
                <p className="mb-2">Witaj w asystencie firmy <b>{company.name}</b>.</p>
                <p className="text-sm">
                  Mam dostęp do {company.reports.length} raportów tej firmy. 
                  Możesz pytać o wyniki finansowe, porównania między kwartałami lub trendy.
                </p>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-lg mt-4">
                <button 
                  onClick={() => setInputMessage("Podsumuj ostatni raport")}
                  className="p-2 text-sm bg-gray-800 border border-gray-700 rounded hover:border-blue-500 text-left transition-colors"
                >
                  "Podsumuj ostatni raport"
                </button>
                <button 
                  onClick={() => setInputMessage("Jaki jest trend przychodów?")}
                  className="p-2 text-sm bg-gray-800 border border-gray-700 rounded hover:border-blue-500 text-left transition-colors"
                >
                  "Jaki jest trend przychodów?"
                </button>
              </div>
            </div>
          ) : (
            messages.map((msg, idx) => (
              <div 
                key={idx} 
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`
                  max-w-[85%] rounded-2xl p-4 
                  ${msg.role === 'user' 
                    ? 'bg-blue-600 text-white rounded-br-none' 
                    : 'bg-gray-700 text-gray-100 rounded-bl-none'}
                `}>
                  <div className="flex items-center gap-2 mb-1 opacity-70 text-xs">
                    {msg.role === 'user' ? <User size={12} /> : <Bot size={12} />}
                    <span>{msg.role === 'user' ? 'Ty' : 'AI'}</span>
                  </div>
                  <div className="prose prose-invert prose-sm max-w-none">
                    <ReactMarkdown>{msg.content}</ReactMarkdown>
                  </div>
                  
                  {/* Chart Rendering */}
                  {msg.chart_data && (
                    <div className="mt-4 text-black">
                      <ChartRenderer chartData={msg.chart_data} />
                    </div>
                  )}
                </div>
              </div>
            ))
          )}
          {isChatLoading && (
            <div className="flex justify-start">
              <div className="bg-gray-700 rounded-2xl rounded-bl-none p-4 flex items-center gap-2">
                <Loader2 size={16} className="animate-spin text-blue-400" />
                <span className="text-sm text-gray-300">Analizuję dane...</span>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="p-4 bg-gray-800 border-t border-gray-700">
          <form onSubmit={handleSendMessage} className="flex gap-2">
            <input
              type="text"
              value={inputMessage}
              onChange={(e) => setInputMessage(e.target.value)}
              placeholder="Zadaj pytanie o finanse firmy..."
              className="flex-1 bg-gray-900 border border-gray-600 rounded-lg px-4 py-3 text-white focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
              disabled={isChatLoading}
            />
            <button 
              type="submit"
              disabled={!inputMessage.trim() || isChatLoading}
              className="bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white px-4 rounded-lg transition-colors flex items-center justify-center min-w-[3rem]"
            >
              <Send size={20} />
            </button>
          </form>
        </div>
      </div>
    </div>
  );
};

export default CompanyDetailsPage;
