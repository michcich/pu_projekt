import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

const client = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const companiesApi = {
  getAll: () => client.get('/companies/'),
  create: (data) => client.post('/companies/', data),
  getOne: (id) => client.get(`/companies/${id}`),
  delete: (id) => client.delete(`/companies/${id}`),
};

export const reportsApi = {
  upload: (formData) => client.post('/reports/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  autoUpload: (formData) => client.post('/reports/auto-upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  }),
  delete: (id) => client.delete(`/reports/${id}`),
};

export const chatApi = {
  sendMessage: (data) => client.post('/chat/', data),
  getHistory: (sessionId) => client.get(`/chat/history/${sessionId}`),
  analyze: (companyId) => client.post(`/chat/analyze/${companyId}`),
  clearSession: (sessionId) => client.delete(`/chat/session/${sessionId}`),
};

export default client;