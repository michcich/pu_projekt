import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import CompaniesPage from './pages/CompaniesPage';
import CompanyDetailsPage from './pages/CompanyDetailsPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<CompaniesPage />} />
          <Route path="company/:id" element={<CompanyDetailsPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;