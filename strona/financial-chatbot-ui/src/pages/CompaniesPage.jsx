import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { companiesApi, reportsApi } from '../api/client';
import { Plus, Building, FileText, Trash2, Search, UploadCloud, Loader2 } from 'lucide-react';

const CompaniesPage = () => {
  const [companies, setCompanies] = useState([]);
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [newCompany, setNewCompany] = useState({ name: '', ticker: '', industry: '', description: '' });
  const [searchTerm, setSearchTerm] = useState('');
  const [isAutoUploading, setIsAutoUploading] = useState(false);

  useEffect(() => {
    fetchCompanies();
  }, []);

  const fetchCompanies = async () => {
    try {
      const response = await companiesApi.getAll();
      setCompanies(response.data);
    } catch (error) {
      console.error('Error fetching companies:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCompany = async (e) => {
    e.preventDefault();
    try {
      await companiesApi.create(newCompany);
      setIsModalOpen(false);
      setNewCompany({ name: '', ticker: '', industry: '', description: '' });
      fetchCompanies();
    } catch (error) {
      alert('Błąd podczas tworzenia firmy: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleDeleteCompany = async (e, id) => {
    e.preventDefault(); // Prevent navigation
    if (window.confirm('Czy na pewno chcesz usunąć tę firmę i wszystkie jej raporty?')) {
      try {
        await companiesApi.delete(id);
        fetchCompanies();
      } catch (error) {
        console.error('Error deleting company:', error);
      }
    }
  };

  const handleAutoUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;

    setIsAutoUploading(true);
    const formData = new FormData();
    formData.append('file', file);

    try {
      await reportsApi.autoUpload(formData);
      alert('Raport przetworzony pomyślnie! Firma została zaktualizowana.');
      fetchCompanies();
    } catch (error) {
      alert('Błąd automatycznego przetwarzania: ' + (error.response?.data?.detail || error.message));
    } finally {
      setIsAutoUploading(false);
      // Reset input value to allow uploading same file again
      e.target.value = '';
    }
  };

  const filteredCompanies = companies.filter(c => 
    c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (c.ticker && c.ticker.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  return (
    <div>
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-8 gap-4">
        <div>
          <h2 className="text-2xl font-bold text-white">Firmy</h2>
          <p className="text-gray-400 mt-1">Zarządzaj bazą firm i ich raportami</p>
        </div>
        <div className="flex gap-3">
          <label className={`
            flex items-center px-4 py-2 bg-green-600 hover:bg-green-700 
            text-white rounded-lg transition-colors cursor-pointer
            ${isAutoUploading ? 'opacity-70 cursor-not-allowed' : ''}
          `}>
            {isAutoUploading ? (
              <Loader2 size={20} className="mr-2 animate-spin" />
            ) : (
              <UploadCloud size={20} className="mr-2" />
            )}
            {isAutoUploading ? 'Przetwarzanie...' : 'Szybki Upload PDF'}
            <input 
              type="file" 
              accept=".pdf" 
              className="hidden" 
              onChange={handleAutoUpload}
              disabled={isAutoUploading}
            />
          </label>
          
          <button 
            onClick={() => setIsModalOpen(true)}
            className="flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            <Plus size={20} className="mr-2" />
            Dodaj firmę
          </button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="mb-6 relative">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
          <Search size={20} className="text-gray-500" />
        </div>
        <input
          type="text"
          placeholder="Szukaj firmy..."
          className="w-full pl-10 pr-4 py-2 bg-gray-800 border border-gray-700 rounded-lg text-white focus:outline-none focus:border-blue-500"
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {loading ? (
        <div className="text-center py-12 text-gray-400">Ładowanie...</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredCompanies.map((company) => (
            <Link 
              key={company.id} 
              to={`/company/${company.id}`}
              className="block bg-gray-800 rounded-xl border border-gray-700 hover:border-blue-500 transition-all hover:shadow-lg group"
            >
              <div className="p-6">
                <div className="flex justify-between items-start mb-4">
                  <div className="p-3 bg-gray-700 rounded-lg group-hover:bg-blue-900/30 transition-colors">
                    <Building size={24} className="text-blue-400" />
                  </div>
                  <button
                    onClick={(e) => handleDeleteCompany(e, company.id)}
                    className="text-gray-500 hover:text-red-400 p-1 rounded transition-colors"
                  >
                    <Trash2 size={18} />
                  </button>
                </div>
                
                <h3 className="text-xl font-semibold text-white mb-1">{company.name}</h3>
                <div className="flex items-center gap-2 mb-3">
                  {company.ticker && (
                    <span className="px-2 py-0.5 bg-gray-700 text-gray-300 text-xs rounded font-mono">
                      {company.ticker}
                    </span>
                  )}
                  {company.industry && (
                    <span className="text-sm text-gray-400 truncate">
                      {company.industry}
                    </span>
                  )}
                </div>
                
                <div className="flex items-center text-sm text-gray-400 mt-4 pt-4 border-t border-gray-700">
                  <FileText size={16} className="mr-2" />
                  {company.reports_count} raportów
                </div>
              </div>
            </Link>
          ))}
          
          {filteredCompanies.length === 0 && (
            <div className="col-span-full text-center py-12 text-gray-500 bg-gray-800/50 rounded-xl border border-gray-700 border-dashed">
              Brak firm spełniających kryteria wyszukiwania
            </div>
          )}
        </div>
      )}

      {/* Modal */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-gray-800 rounded-xl max-w-md w-full p-6 border border-gray-700 shadow-2xl">
            <h3 className="text-xl font-bold text-white mb-4">Nowa firma</h3>
            <form onSubmit={handleCreateCompany} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Nazwa firmy *</label>
                <input
                  required
                  type="text"
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                  value={newCompany.name}
                  onChange={e => setNewCompany({...newCompany, name: e.target.value})}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">Ticker (Symbol)</label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                    value={newCompany.ticker}
                    onChange={e => setNewCompany({...newCompany, ticker: e.target.value})}
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-400 mb-1">Branża</label>
                  <input
                    type="text"
                    className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                    value={newCompany.industry}
                    onChange={e => setNewCompany({...newCompany, industry: e.target.value})}
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-400 mb-1">Opis</label>
                <textarea
                  className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500 h-24 resize-none"
                  value={newCompany.description}
                  onChange={e => setNewCompany({...newCompany, description: e.target.value})}
                />
              </div>
              <div className="flex justify-end gap-3 mt-6">
                <button
                  type="button"
                  onClick={() => setIsModalOpen(false)}
                  className="px-4 py-2 text-gray-300 hover:text-white hover:bg-gray-700 rounded-lg transition-colors"
                >
                  Anuluj
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                  Utwórz
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default CompaniesPage;