import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)


// For users.jsx testing
// import React from 'react';
// import ReactDOM from 'react-dom/client';
// import Users from './users.jsx'; // This is the new import
// import './index.css';

// ReactDOM.createRoot(document.getElementById('root')).render(
//   <React.StrictMode>
//     <Users /> {/* This is the new component to render */}
//   </React.StrictMode>,
// );



