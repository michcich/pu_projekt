import React from 'react';
import {
  LineChart, Line, BarChart, Bar, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

const ChartRenderer = ({ chartData }) => {
  if (!chartData || !chartData.data) return null;

  const { type, title, data } = chartData;

  const formatValue = (value) => {
    if (value >= 1_000_000_000_000) {
        return `${(value / 1_000_000_000).toFixed(2)} mld`;
    }
    if (value >= 1_000_000) {
      return `${(value / 1_000_000).toLocaleString('pl-PL', {maximumFractionDigits: 0})} mln`;
    } 
    if (value >= 1_000) {
      return `${(value / 1_000).toFixed(0)} tys`;
    }
    return value;
  };

  const chartDataFormatted = data.labels.map((label, index) => {
    const point = { name: label };
    data.datasets.forEach(dataset => {
      point[dataset.label] = dataset.data[index];
    });
    return point;
  });

  const renderChart = () => {
    const commonProps = {
      data: chartDataFormatted,
      margin: { top: 5, right: 30, left: 20, bottom: 5 }
    };

    switch (type) {
      case 'line':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart {...commonProps}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis tickFormatter={formatValue} width={100} />
              <Tooltip formatter={(value) => [formatValue(value), '']} />
              <Legend />
              {data.datasets.map((dataset, idx) => (
                <Line 
                  key={idx}
                  type="monotone" 
                  dataKey={dataset.label} 
                  stroke={dataset.borderColor || "#8884d8"} 
                  activeDot={{ r: 8 }} 
                />
              ))}
            </LineChart>
          </ResponsiveContainer>
        );
      
      case 'bar':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <BarChart {...commonProps}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis tickFormatter={formatValue} width={100} />
              <Tooltip formatter={(value) => [formatValue(value), '']} />
              <Legend />
              {data.datasets.map((dataset, idx) => (
                <Bar 
                  key={idx}
                  dataKey={dataset.label} 
                  fill={dataset.backgroundColor || "#82ca9d"} 
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        );
      
      case 'area':
        return (
          <ResponsiveContainer width="100%" height={300}>
            <AreaChart {...commonProps}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis tickFormatter={formatValue} width={100} />
              <Tooltip formatter={(value) => [formatValue(value), '']} />
              <Legend />
              {data.datasets.map((dataset, idx) => (
                <Area 
                  key={idx}
                  type="monotone" 
                  dataKey={dataset.label} 
                  stroke={dataset.borderColor || "#8884d8"} 
                  fill={dataset.backgroundColor || "#8884d8"} 
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        );
      
      default:
        return <div>Nieobsługiwany typ wykresu: {type}</div>;
    }
  };

  return (
    <div className="w-full p-4 bg-white rounded-lg shadow-sm border border-gray-200 my-4">
      {title && <h3 className="text-lg font-semibold mb-4 text-center">{title}</h3>}
      <div className="w-full h-[300px]">
        {renderChart()}
      </div>
    </div>
  );
};

export default ChartRenderer;
